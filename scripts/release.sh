#!/usr/bin/env bash
# Usage: scripts/release.sh
#
# Safe release pipeline for nmtc-application-builder:
#   1. Run test suite (abort on any failure)
#   2. Build wheel + sdist
#   3. twine check (abort if metadata is malformed)
#   4. twine upload (abort on non-zero exit)
#   5. Poll PyPI until the new version appears (60s timeout)
#   6. Only after PyPI confirms the version: update streamlit_app/requirements.txt and commit
#
# Run from the repo root:  bash scripts/release.sh
set -euo pipefail

PACKAGE_NAME="nmtc-application-builder"
REQUIREMENTS="streamlit_app/requirements.txt"
POLL_TIMEOUT=60    # seconds to wait for PyPI to reflect the new version
POLL_INTERVAL=5    # seconds between polls

# ── 0. resolve version from pyproject.toml ────────────────────────────────────
VERSION=$(python3 -c "
import tomllib, pathlib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
print(data['project']['version'])
" 2>/dev/null || python3 -c "
import re, pathlib
txt = pathlib.Path('pyproject.toml').read_text()
m = re.search(r'^version\s*=\s*\"([^\"]+)\"', txt, re.MULTILINE)
print(m.group(1))
")

echo "==> Releasing ${PACKAGE_NAME} ${VERSION}"

# ── 1. test suite ─────────────────────────────────────────────────────────────
echo ""
echo "── Step 1: pytest (excluding slow wheel test) ──"
python3 -m pytest -m "not wheel" -q
echo "   Tests passed."

# ── 2. clean build ────────────────────────────────────────────────────────────
echo ""
echo "── Step 2: clean build ──"
rm -rf dist build "$(echo "${PACKAGE_NAME}" | tr '-' '_').egg-info"
python3 -m build
echo "   Built artifacts:"
ls -lh dist/*"${VERSION}"*

# ── 3. twine check ────────────────────────────────────────────────────────────
echo ""
echo "── Step 3: twine check ──"
python3 -m twine check dist/*"${VERSION}"*
echo "   twine check passed."

# ── 4. twine upload ───────────────────────────────────────────────────────────
echo ""
echo "── Step 4: twine upload ──"
# twine exits non-zero on HTTP errors; set -e will abort here if upload fails
python3 -m twine upload --verbose dist/*"${VERSION}"*
echo "   Upload command exited 0."

# ── 5. poll PyPI until version is visible ────────────────────────────────────
echo ""
echo "── Step 5: polling PyPI for ${VERSION} (${POLL_TIMEOUT}s timeout) ──"
ELAPSED=0
while true; do
    VISIBLE=$(pip index versions "${PACKAGE_NAME}" --no-cache-dir 2>/dev/null \
               | grep -o "${VERSION}" || true)
    if [ -n "$VISIBLE" ]; then
        echo "   ${VERSION} is visible on PyPI after ${ELAPSED}s."
        break
    fi
    if [ "$ELAPSED" -ge "$POLL_TIMEOUT" ]; then
        echo "ERROR: ${VERSION} did not appear on PyPI within ${POLL_TIMEOUT}s." >&2
        echo "       Check https://pypi.org/project/${PACKAGE_NAME}/ manually." >&2
        exit 1
    fi
    echo "   Not visible yet — waiting ${POLL_INTERVAL}s (${ELAPSED}s elapsed)..."
    sleep "${POLL_INTERVAL}"
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

# ── 6. update requirements.txt and commit ─────────────────────────────────────
echo ""
echo "── Step 6: update ${REQUIREMENTS} and commit ──"
# Replace any existing pin for this package
sed -i.bak "s|^${PACKAGE_NAME}==.*|${PACKAGE_NAME}==${VERSION}|" "${REQUIREMENTS}"
rm -f "${REQUIREMENTS}.bak"

git add "${REQUIREMENTS}"

# Only commit if there's actually a change
if git diff --cached --quiet; then
    echo "   ${REQUIREMENTS} already pinned to ${VERSION} — no commit needed."
else
    git commit -m "Pin ${PACKAGE_NAME}==${VERSION} in Streamlit requirements"
    echo "   Committed."
fi

echo ""
echo "==> Release ${VERSION} complete."
echo "    PyPI: https://pypi.org/project/${PACKAGE_NAME}/${VERSION}/"
