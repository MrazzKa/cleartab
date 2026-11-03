#!/usr/bin/env bash
# Store the Groq API key in the untracked .env file (it is in .gitignore). The key is read without echo, so it
# does not appear on screen or in shell history.
set -euo pipefail
cd "$(dirname "$0")/.."
read -rsp "Paste the Groq API key and press Enter: " key; echo
[ -n "$key" ] || { echo "No key entered."; exit 1; }
touch .env
grep -v '^GROQ_API_KEY=' .env > .env.tmp || true
echo "GROQ_API_KEY=$key" >> .env.tmp
mv .env.tmp .env && chmod 600 .env
echo "Saved to .env. Restart the API so it picks up the key."
