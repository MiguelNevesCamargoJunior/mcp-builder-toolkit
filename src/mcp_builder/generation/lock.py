"""Cross-platform exclusive generation lock for a project root."""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path
from types import TracebackType

from mcp_builder.domain.diagnostics import Codes, Diagnostic, Severity

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
    """

    def __init__(
        self,
        project_root: Path,
        *,
        stale_seconds: int = DEFAULT_STALE_SECONDS,
    ) -> None:
        self.project_root = project_root.resolve()
        self.stale_seconds = stale_seconds
        self.path = self.project_root / LOCK_DIR / LOCK_NAME
        self._held = False

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
                with contextlib.suppress(OSError):
                    self.path.unlink(missing_ok=True)
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
