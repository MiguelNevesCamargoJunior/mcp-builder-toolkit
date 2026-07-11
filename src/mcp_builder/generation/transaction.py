"""Staged filesystem apply for clean and regenerating projects."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from mcp_builder.domain.artifacts import ArtifactPlan, ArtifactSpec
from mcp_builder.domain.diagnostics import (
    Codes,
    Diagnostic,
    Ownership,
    PlannedChange,
    PlannedChangeAction,
    Severity,
)
from mcp_builder.generation.renderer import content_hash
from mcp_builder.generation.state import BuildState, save_state, try_load_state
from mcp_builder.manifest.paths import normalize_relative_path, safe_project_path


@dataclass(frozen=True, slots=True)
class _FileSnapshot:
    relative_path: str
    content: bytes | None
    mode: int | None


@dataclass(slots=True)
class ApplyResult:
    changes: list[PlannedChange]
    diagnostics: list[Diagnostic]
    applied: bool


def classify_changes(
    plan: ArtifactPlan,
    project_root: Path,
    prior: BuildState | None,
    *,
    force_managed: set[str] | None = None,
) -> tuple[list[PlannedChange], list[tuple[PlannedChange, ArtifactSpec | None]], list[Diagnostic]]:
    """Classify planned artifacts against disk and prior state.

    Returns (user-facing changes, apply-actions with specs, diagnostics).
    """
    force = {normalize_relative_path(p) for p in (force_managed or set())}
    diagnostics: list[Diagnostic] = []
    changes: list[PlannedChange] = []
    actions: list[tuple[PlannedChange, ArtifactSpec | None]] = []

    prior_artifacts = prior.artifacts if prior else {}
    desired_paths = {normalize_relative_path(a.relative_path): a for a in plan.artifacts}

    for rel, art in desired_paths.items():
        dest = safe_project_path(project_root, rel)
        exists = dest.is_file()
        current_hash = content_hash(dest.read_text(encoding="utf-8")) if exists else None
        prev = prior_artifacts.get(rel)

        if art.ownership is Ownership.SCAFFOLD_ONCE:
            if exists:
                change = PlannedChange(
                    path=rel,
                    action=PlannedChangeAction.PRESERVE,
                    ownership=art.ownership,
                )
                changes.append(change)
                # no write
            else:
                change = PlannedChange(
                    path=rel,
                    action=PlannedChangeAction.CREATE,
                    ownership=art.ownership,
                )
                changes.append(change)
                actions.append((change, art))
            continue

        if art.ownership is Ownership.DERIVED:
            if exists and current_hash == art.content_hash:
                change = PlannedChange(
                    path=rel,
                    action=PlannedChangeAction.UNCHANGED,
                    ownership=art.ownership,
                )
                changes.append(change)
            else:
                action = PlannedChangeAction.UPDATE if exists else PlannedChangeAction.CREATE
                change = PlannedChange(path=rel, action=action, ownership=art.ownership)
                changes.append(change)
                actions.append((change, art))
            continue

        # managed
        if not exists:
            change = PlannedChange(
                path=rel,
                action=PlannedChangeAction.CREATE,
                ownership=art.ownership,
            )
            changes.append(change)
            actions.append((change, art))
            continue

        if current_hash == art.content_hash:
            change = PlannedChange(
                path=rel,
                action=PlannedChangeAction.UNCHANGED,
                ownership=art.ownership,
            )
            changes.append(change)
            continue

        # content differs from desired
        prior_hash = prev.generated_hash if prev else None
        user_modified = prior_hash is not None and current_hash != prior_hash
        # If no prior state, treat existing file as user-owned conflict when different
        if prior is None and exists:
            user_modified = True

        if user_modified and rel not in force:
            change = PlannedChange(
                path=rel,
                action=PlannedChangeAction.CONFLICT,
                ownership=art.ownership,
            )
            changes.append(change)
            diagnostics.append(
                Diagnostic(
                    code=Codes.GEN_CONFLICT,
                    severity=Severity.ERROR,
                    message=f"Managed file was modified and conflicts with new generation: {rel}",
                    path=rel,
                    hint=f"Re-run with --force-managed {rel} to overwrite, or restore the file.",
                )
            )
            continue

        change = PlannedChange(
            path=rel,
            action=PlannedChangeAction.UPDATE,
            ownership=art.ownership,
        )
        changes.append(change)
        actions.append((change, art))

    # Prior managed files no longer desired
    for rel, prev in prior_artifacts.items():
        if rel in desired_paths:
            continue
        if prev.ownership is not Ownership.MANAGED:
            continue
        dest = safe_project_path(project_root, rel)
        if not dest.is_file():
            continue
        current_hash = content_hash(dest.read_text(encoding="utf-8"))
        if current_hash == prev.generated_hash:
            change = PlannedChange(
                path=rel,
                action=PlannedChangeAction.REMOVE_MANAGED,
                ownership=Ownership.MANAGED,
            )
            changes.append(change)
            actions.append((change, None))
        else:
            change = PlannedChange(
                path=rel,
                action=PlannedChangeAction.ORPHAN,
                ownership=Ownership.MANAGED,
            )
            changes.append(change)
            diagnostics.append(
                Diagnostic(
                    code=Codes.GEN_CONFLICT,
                    severity=Severity.WARNING,
                    message=f"Previously managed file is no longer generated and was modified: {rel}",
                    path=rel,
                    hint="File was preserved. Delete manually if no longer needed.",
                )
            )

    return changes, actions, diagnostics


def apply_plan(
    plan: ArtifactPlan,
    project_root: Path,
    *,
    dry_run: bool = False,
    force_managed: set[str] | None = None,
) -> ApplyResult:
    project_root = project_root.resolve()
    prior, state_error = try_load_state(project_root)
    if state_error is not None:
        diagnostic = Diagnostic(
            code=Codes.GEN_IO,
            severity=Severity.ERROR,
            message=f"Build state is corrupt or unsafe: {state_error}",
            path=".mcp-builder/state.json",
            hint="Inspect or remove the state file, then regenerate.",
        )
        return ApplyResult(changes=[], diagnostics=[diagnostic], applied=False)
    try:
        changes, actions, diagnostics = classify_changes(
            plan, project_root, prior, force_managed=force_managed
        )
    except (OSError, ValueError) as exc:
        diagnostic = Diagnostic(
            code=Codes.PATH_INVALID,
            severity=Severity.ERROR,
            message=f"Unsafe generation path: {exc}",
        )
        return ApplyResult(changes=[], diagnostics=[diagnostic], applied=False)
    diagnostics = list(plan.diagnostics) + diagnostics

    if any(d.severity is Severity.ERROR for d in diagnostics):
        return ApplyResult(changes=changes, diagnostics=diagnostics, applied=False)

    if dry_run:
        return ApplyResult(changes=changes, diagnostics=diagnostics, applied=False)

    snapshots = _snapshot_files(
        project_root,
        [change.path for change, _art in actions] + [".mcp-builder/state.json"],
    )
    new_state = BuildState.from_plan(plan)

    # Stage, apply, and write state as one rollback boundary.
    try:
        _apply_actions(project_root, plan, actions)
        save_state(project_root, new_state)
    except OSError as exc:
        rollback_error = _restore_files(snapshots, project_root)
        detail = f"; rollback also failed: {rollback_error}" if rollback_error else ""
        diagnostics.append(
            Diagnostic(
                code=Codes.GEN_IO,
                severity=Severity.ERROR,
                message=f"Filesystem failure during generation: {exc}{detail}",
                hint="The builder rolled back files changed by this generation attempt.",
            )
        )
        return ApplyResult(changes=changes, diagnostics=diagnostics, applied=False)

    diagnostics.append(
        Diagnostic(
            code=Codes.GEN_SUCCESS,
            severity=Severity.INFO,
            message=f"Generated {sum(1 for c in changes if c.action.value in {'create', 'update'})} file(s)",
        )
    )
    return ApplyResult(changes=changes, diagnostics=diagnostics, applied=True)


def _apply_actions(
    project_root: Path,
    plan: ArtifactPlan,
    actions: list[tuple[PlannedChange, ArtifactSpec | None]],
) -> None:
    if not actions:
        return

    staging = Path(tempfile.mkdtemp(prefix=".mcp-builder-stage-", dir=str(project_root)))
    try:
        for change, art in actions:
            if change.action is PlannedChangeAction.REMOVE_MANAGED:
                continue  # handle after successful stage of creates/updates
            assert art is not None
            dest = safe_project_path(staging, change.path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(art.content, encoding="utf-8")
            if art.mode is not None:
                dest.chmod(art.mode)

        # Commit creates/updates
        for change, art in actions:
            if change.action is PlannedChangeAction.REMOVE_MANAGED:
                target = safe_project_path(project_root, change.path)
                if target.is_file():
                    target.unlink()
                continue
            assert art is not None
            staged = staging / change.path
            target = safe_project_path(project_root, change.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target = safe_project_path(project_root, change.path)
            # Atomic replace where possible
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
            )
            os.close(fd)
            tmp_name = Path(temp_name)
            try:
                shutil.copy2(staged, tmp_name)
                os.replace(tmp_name, target)
            finally:
                tmp_name.unlink(missing_ok=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _snapshot_files(project_root: Path, relative_paths: list[str]) -> list[_FileSnapshot]:
    snapshots: list[_FileSnapshot] = []
    for relative_path in dict.fromkeys(relative_paths):
        path = safe_project_path(project_root, relative_path)
        if path.is_file():
            stat = path.stat()
            snapshots.append(
                _FileSnapshot(
                    relative_path=relative_path,
                    content=path.read_bytes(),
                    mode=stat.st_mode,
                )
            )
        else:
            snapshots.append(_FileSnapshot(relative_path=relative_path, content=None, mode=None))
    return snapshots


def _restore_files(snapshots: list[_FileSnapshot], project_root: Path) -> OSError | None:
    try:
        for snapshot in snapshots:
            path = safe_project_path(project_root, snapshot.relative_path)
            if snapshot.content is None:
                if path.is_file():
                    path.unlink()
                parent = path.parent
                while parent != project_root and parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path = safe_project_path(project_root, snapshot.relative_path)
            path.write_bytes(snapshot.content)
            if snapshot.mode is not None:
                path.chmod(snapshot.mode)
    except (OSError, ValueError) as exc:
        return exc if isinstance(exc, OSError) else OSError(str(exc))
    return None


def write_json_state_preview(plan: ArtifactPlan) -> str:
    """Helper for tests — serialize plan metadata."""
    return json.dumps(
        {
            "manifestHash": plan.manifest_hash,
            "builderVersion": plan.builder_version,
            "profile": plan.profile,
            "protocolVersion": plan.protocol_version,
            "artifacts": [a.relative_path for a in plan.artifacts],
        },
        indent=2,
        sort_keys=True,
    )
