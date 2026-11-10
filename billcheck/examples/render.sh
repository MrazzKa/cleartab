#!/usr/bin/env bash
# Render the synthetic example documents (no real person) from src/*.html with headless Chromium.
# Usage: CHROME=/path/to/chrome billcheck/examples/render.sh
set -euo pipefail
cd "$(dirname "$0")"
CHROME=${CHROME:-$(command -v chromium || command -v google-chrome || true)}
[ -n "$CHROME" ] || { echo "Set CHROME to a Chromium or Chrome binary"; exit 1; }
"$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=er_eob.pdf "file://$PWD/src/er_eob.html"
"$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1.5 \
  --window-size=840,640 --screenshot=er_bill.png "file://$PWD/src/er_bill.html"
ls -l er_eob.pdf er_bill.png
