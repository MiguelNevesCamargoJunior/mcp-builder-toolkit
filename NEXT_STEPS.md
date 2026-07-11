# Next steps after v0.1.0a1

## Before tagging

1. Review and create the initial commit on `main`.
2. Push `main` and require the CI and security workflows to pass.
3. Enable GitHub private vulnerability reporting.
4. Configure the `PYPI_TOKEN` repository secret, or intentionally leave PyPI
   publication disabled for a GitHub-only alpha.
5. Verify the package name is available on PyPI and TestPyPI.
6. Tag the reviewed commit as `v0.1.0a1`.

## Alpha validation

1. Run at least three external pilot sessions and record results in
   `docs/pilot-evidence.md`.
2. Confirm installation from the published wheel on Python 3.12 and 3.13.
3. Confirm the generated stdio and Streamable HTTP profiles on a clean machine.
4. Review CodeQL, dependency-review, gitleaks, and Scorecard results.

## Candidate follow-ups

- improve CLI error-path coverage;
- add a generated project without the example tool to acceptance CI;
- add optional environment-based API client examples without putting secrets in
  manifests;
- collect evidence before adding another target or compatibility profile.

The public message remains narrow: this is a manifest-driven project generator,
not a no-code API integration runtime or governance platform.
