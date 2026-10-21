#!/usr/bin/env bash
# Print `export` lines for distributor API keys stored in the private vendor-logins file.
#
# Usage (add to ~/.zshrc so every shell, and Claude Code, gets the keys):
#   eval "$("$HOME/Dev/dropout-kicad-library/scripts/vendor-env.sh")"
#
# The file is parsed, never sourced, so passwords containing & $ ; spaces etc. are safe.
# Only API keys are exported. Website usernames/passwords stay in the file and are
# read on demand when a browser sign-in is needed.
#
# This script contains no secrets and is safe to commit. The credentials file is
# deliberately outside ~/Dev so it can never be committed.
#
# Bash 3.2 compatible (macOS default).

CRED_FILE="${DROPOUT_VENDOR_LOGINS:-$HOME/.local/share/dropout/vendor-logins}"

if [ ! -r "$CRED_FILE" ]; then
  echo "vendor-env.sh: cannot read $CRED_FILE" >&2
  exit 1
fi

# Keys to export, and extra names (aliases) tools may expect for the same value.
# Format: SOURCE_NAME:ALIAS1,ALIAS2
EXPORTS="
DIGIKEY_CLIENT_ID:
DIGIKEY_CLIENT_SECRET:
MOUSER_SEARCH_API_KEY:MOUSER_API_KEY
NEWARK_SEARCH_API_KEY:ELEMENT14_API_KEY,NEWARK_API_KEY
"

# Single-quote a value for the shell: ' -> '\''
shq() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

lookup() {
  # Value is everything after the first '=' on the line starting with NAME=
  grep -m1 "^$1=" "$CRED_FILE" | sed "s/^$1=//" | tr -d '\r'
}

for entry in $EXPORTS; do
  name="${entry%%:*}"
  aliases="${entry#*:}"
  value="$(lookup "$name")"
  [ -z "$value" ] && continue
  q="$(shq "$value")"
  echo "export $name=$q"
  IFS=','
  for a in $aliases; do
    [ -n "$a" ] && echo "export $a=$q"
  done
  unset IFS
done
