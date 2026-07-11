"""Exit code constants match the public CLI contract."""

from mcp_builder.cli.exit_codes import ExitCode


def test_exit_codes() -> None:
    assert ExitCode.SUCCESS == 0
    assert ExitCode.INTERNAL_ERROR == 1
    assert ExitCode.USAGE_OR_VALIDATION == 2
    assert ExitCode.GENERATION_CONFLICT == 3
    assert ExitCode.UNSUPPORTED_ENVIRONMENT == 4
    assert ExitCode.FILESYSTEM_FAILURE == 5
    assert ExitCode.DOCTOR_UNHEALTHY == 6
