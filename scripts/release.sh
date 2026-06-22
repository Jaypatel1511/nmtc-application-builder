#!/usr/bin/env bash
# Releasing nmtc-application-builder is now CI-ONLY.
# Publishing happens via .github/workflows/release.yml on a version-tag push,
# using PyPI Trusted Publisher (OIDC). Never publish from a local working tree.
#
# To cut a release:
#   1. Bump version in pyproject.toml, update CHANGELOG.md, commit.
#   2. Merge to main (ff-only).
#   3. git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin main && git push origin vX.Y.Z
#   4. CI builds, wheel-tests, and publishes.
#
# This script no longer uploads. It runs a local pre-flight only.
set -euo pipefail

echo "Local pre-flight only — publishing is CI-only (see .github/workflows/release.yml)."
echo ""
echo "-- pytest (excluding slow wheel test) --"
python3 -m pytest -m "not wheel" -q
echo ""
echo "-- build --"
rm -rf dist build nmtc_application_builder.egg-info
python3 -m build
echo ""
echo "Pre-flight passed. To publish: push a vX.Y.Z tag; CI handles the upload."
