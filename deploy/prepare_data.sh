#!/usr/bin/env bash
# Run on a machine that has the loaded database and data/raw/reference. Produces data-server/ (gitignored):
#   data-server/db/cleartab.sql.gz        database dump, restored by the db container on first start
#   data-server/reference/                CMS MUE zips and ncci_ptp.sqlite (AMA license, never commit)
# Then copy data-server/ to the server: scp -r data-server ubuntu@<server-ip>:~/cleartab/
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
: "${DATABASE_URL:?DATABASE_URL is not set}"
mkdir -p data-server/db data-server/reference
pg_dump --no-owner --no-acl "$DATABASE_URL" | gzip -9 > data-server/db/cleartab.sql.gz
cp data/raw/reference/medicare-ncci-*-mue-table.zip data-server/reference/
if [ -f data/raw/reference/ncci_ptp.sqlite ]; then
  cp data/raw/reference/ncci_ptp.sqlite data-server/reference/
else
  echo "ncci_ptp.sqlite not found: the pair check will be skipped (see MANUAL_DOWNLOADS.md)"
fi
cp -r data/raw/reference/ambulance data-server/reference/ 2>/dev/null || true
du -sh data-server/*
