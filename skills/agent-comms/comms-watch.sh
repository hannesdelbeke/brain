#!/bin/sh
# comms-watch - wake LOCAL agents when mail arrives for them.
#
# This is the one piece that cannot be shared across machines: a process on PC A
# cannot start a process on PC B, so every machine that hosts agents runs its own
# copy, and each one only ever wakes the agents living on it.
#
# It is also the only piece that knows which vendor each agent is, because waking
# is the one operation with no common interface - though every CLI does have some
# one-shot headless mode, which is what makes this short.
#
#   export COMMS_BUS=project-a
#   export COMMS_LOCAL="planner:claude builder:gemini"   # name:vendor, space separated
#   comms-watch            # poll forever
#   comms-watch once       # check once and exit, for a doorbell or a cron job
#
# Pair `comms-watch once` with COMMS_NOTIFY on the sending side (MQTT, ssh, a
# webhook) and the poll loop becomes a push channel.

set -eu

CONFIG_FILE="${COMMS_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/agentcomms/config}"

get_config() {
  [ -f "$CONFIG_FILE" ] || return 1
  key="$1"
  val=$(sed -n "s/^[[:space:]]*$key[[:space:]]*=[[:space:]]*//p" "$CONFIG_FILE" 2>/dev/null | head -n 1 | tr -d '\r')
  val=$(echo "$val" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
  [ -n "$val" ] || return 1
  echo "$val"
}

CFG_DEFAULT_BUS=$(get_config default_bus 2>/dev/null || true)
CFG_ROOT=$(get_config root 2>/dev/null || true)

BUS="${COMMS_BUS:-$CFG_DEFAULT_BUS}"
if [ -n "${COMMS_ROOT:-}" ]; then
  ROOT="$COMMS_ROOT"
elif [ -n "$BUS" ]; then
  ROOT="$HOME/.agentcomms/$BUS"
elif [ -n "$CFG_ROOT" ]; then
  ROOT="$CFG_ROOT"
else
  ROOT="$HOME/.agentcomms"
fi

LOCAL="${COMMS_LOCAL:-}"
POLL="${COMMS_POLL:-30}"
BIN="${COMMS_BIN:-comms}"
ONCE=0
[ "${1:-}" = once ] && ONCE=1

[ -n "$LOCAL" ] || { echo "comms-watch: set COMMS_LOCAL to \"name:vendor ...\"" >&2; exit 1; }

wake() {
  name="$1"; vendor="$2"
  msg="You have unread mail on the comms bus. Run \`COMMS_ME=$name $BIN read\` and act on what it says."
  echo "comms-watch: waking $name ($vendor)"
  case "$vendor" in
    claude) claude -p "$msg" >/dev/null 2>&1 || true ;;
    gemini) gemini -p "$msg" >/dev/null 2>&1 || true ;;
    codex)  codex exec "$msg" >/dev/null 2>&1 || true ;;
    *)      COMMS_ME="$name" COMMS_MSG="$msg" sh -c "$vendor" >/dev/null 2>&1 || true ;;
  esac
}

while :; do
  for pair in $LOCAL; do
    name="${pair%%:*}"
    vendor="${pair#*:}"
    n=$(COMMS_ME="$name" COMMS_ROOT="$ROOT" "$BIN" inbox 2>/dev/null | awk '{print $1+$3}')
    [ -n "${n:-}" ] || n=0
    [ "$n" -gt 0 ] && wake "$name" "$vendor"
  done
  [ "$ONCE" = 1 ] && break
  sleep "$POLL"
done
