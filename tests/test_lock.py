"""T036: project generation lock tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_builder.generation.lock import GenerationLock, GenerationLockError


def test_lock_exclusive(tmp_path: Path) -> None:
    with GenerationLock(tmp_path):
        with pytest.raises(GenerationLockError) as exc:
            GenerationLock(tmp_path).acquire()
        assert exc.value.diagnostic.code == "MBT-GEN-003"
    # After release, acquire succeeds
    with GenerationLock(tmp_path) as lock:
        assert lock.path.is_file()
    assert not (tmp_path / ".mcp-builder" / "generate.lock").exists()


def test_stale_lock_is_reclaimed(tmp_path: Path) -> None:
    lock_path = tmp_path / ".mcp-builder" / "generate.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text("pid=0\ncreated=0\n", encoding="utf-8")
    # Force mtime into the past
    import os
    import time

    past = time.time() - 3600
    os.utime(lock_path, (past, past))

    with GenerationLock(tmp_path, stale_seconds=60):
        assert lock_path.is_file()
