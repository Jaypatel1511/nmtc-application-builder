#!/usr/bin/env bash
# Releasing nmtc-application-builder is now CI-ONLY.
# Publishing happens via .github/workflows/release.yml on a version-tag push,
# using PyPI Trusted Publisher (OIDC). Never publish from a local working tree.
#
# To cut a release:
#   1. Bump version in pyproject.toml (and streamlit_app/requirements.txt --
#      tests/test_streamlit_deployment_pin.py forces them equal), update
#      CHANGELOG.md, commit.
#   2. Merge to main (ff-only).
#   3. git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin main && git push origin vX.Y.Z
#   4. CI builds, wheel-tests, and publishes.
#   5. THE PUBLIC STREAMLIT APP IS DOWN FROM STEP 2 UNTIL STEP 4 FINISHES, and
#      needs a manual reboot afterwards. Read the next paragraph before you
#      start, because the window is in this procedure and not in anyone's
#      mistake.
#
# THE MERGE-TO-PUBLISH WINDOW (1.4.1 S6)
#
# Streamlit Community Cloud deploys the app's SOURCE from the main branch and
# installs its LIBRARY from PyPI, pinned by streamlit_app/requirements.txt to
# `nmtc-application-builder==<this version>`. Step 2 pushes a main whose pin
# names a version step 4 has not published yet, so the rebuild step 2 triggers
# runs `pip install nmtc-application-builder==X.Y.Z` against a PyPI that does
# not have it. Resolution fails and the public app is down until the upload
# lands. This happened on PR #12 and it was not a mistake anybody made -- it is
# what steps 2 and 3 do in this order.
#
# THE PIN IS NOT THE BUG, AND LOOSENING IT IS NOT THE FIX. See the ruling in
# streamlit_app/requirements.txt: `>=` either fails identically (a floor at an
# unpublished version resolves to nothing) or resolves to an OLDER library than
# the branch source, which serves half-working pages instead of an outage --
# silent, per-page, and on a tool whose numbers inform a federal filing.
#
# WHAT ACTUALLY CLOSES THE WINDOW is deploying from a branch that moves AFTER
# the publish, not before it: point Streamlit Cloud at a `deploy` branch and
# fast-forward it to the tag once step 4 is green. Source and library then
# advance together and both are the published artifact. That is a change to the
# Streamlit Cloud app settings, which is Jay's to make; until it is made, the
# outage window is real and this comment is where it is written down.
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
