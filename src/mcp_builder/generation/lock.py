"""Cross-platform exclusive generation lock for a project root."""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path
from types import TracebackType

from mcp_builder.domain.diagnostics import Codes, Diagnostic, Severity
from mcp_builder.manifest.paths import safe_project_path

LOCK_DIR = ".mcp-builder"
LOCK_NAME = "generate.lock"
DEFAULT_STALE_SECONDS = 30 * 60  # 30 minutes


class GenerationLockError(Exception):
    """Raised when the project generation lock cannot be acquired."""

    def __init__(self, message: str, *, diagnostic: Diagnostic) -> None:
        super().__init__(message)
        self.diagnostic = diagnostic


class GenerationLock:
    """Exclusive lock stored at ``<project>/.mcp-builder/generate.lock``.

    Uses atomic create (``O_CREAT | O_EXCL``) so it works on Linux, macOS, and
    Windows without native flock semantics. Stale locks older than
    ``stale_seconds`` are removed and retried once.

    All paths are validated through ``safe_project_path`` to prevent symlink
    traversal and junction following.
    """

    def __init__(
        self,
        project_root: Path,
        *,
        stale_seconds: int = DEFAULT_STALE_SECONDS,
    ) -> None:
        self.project_root = project_root.resolve()
        self.stale_seconds = stale_seconds
        try:
            self.path = safe_project_path(self.project_root, f"{LOCK_DIR}/{LOCK_NAME}")
        except ValueError as exc:
            raise GenerationLockError(
                str(exc),
                diagnostic=Diagnostic(
                    code=Codes.GEN_LOCK,
                    severity=Severity.ERROR,
                    message=str(exc),
                    hint="Remove the problematic symlink before generating.",
                ),
            ) from exc
        self._held = False
        self._last_content: str | None = None

    def __enter__(self) -> GenerationLock:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()

    def acquire(self) -> None:
        if self._held:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._try_create()
        except FileExistsError:
            if self._is_stale():
                self._last_content = self._read_content()
                with contextlib.suppress(OSError):
                    self.path.unlink(missing_ok=True)
                if self.path.exists():
                    raise GenerationLockError(
                        f"Could not remove stale lock: {self.path}",
                        diagnostic=Diagnostic(
                            code=Codes.GEN_LOCK,
                            severity=Severity.ERROR,
                            message=f"Could not remove stale lock: {self.path}",
                            path=str(self.path),
                            hint="Remove the file manually.",
                        ),
                    ) from None
                try:
                    self._try_create()
                    return
                except FileExistsError:
                    pass
            raise GenerationLockError(
                f"Generation already in progress for {self.project_root}",
                diagnostic=Diagnostic(
                    code=Codes.GEN_LOCK,
                    severity=Severity.ERROR,
                    message=(
                        f"Could not acquire generation lock: {self.path} "
                        "(another generate may be running)"
                    ),
                    path=str(self.path),
                    hint="Wait for the other process to finish, or remove a stale lock file.",
                ),
            ) from None

    def release(self) -> None:
        if not self._held:
            return
        try:
            self.path.unlink(missing_ok=True)
        finally:
            self._held = False

    def _try_create(self) -> None:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(self.path, flags, 0o644)
        try:
            payload = f"pid={os.getpid()}\ncreated={time.time():.3f}\n"
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        self._held = True

    def _is_stale(self) -> bool:
        try:
            age = time.time() - self.path.stat().st_mtime
        except OSError:
            return True
        return age > self.stale_seconds

    def _read_content(self) -> str | None:
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError:
            return None
