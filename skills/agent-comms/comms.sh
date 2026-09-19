#!/bin/sh
# comms - a vendor-neutral message bus for AI agents.
# Needs only a POSIX shell and a filesystem. No daemon, no port, no SDK, no vendor API.
# Optional: set COMMS_GIT=1 to sync the bus through a git remote across machines.
# Optional: set COMMS_BUS=<name> or configure default_bus to select an isolated message bus.
#
# Configuration & settings:
#   comms config set default_bus project-a    # sets default bus in ~/.config/agentcomms/config
#   comms config set git 1                    # enables git sync mode
#   comms config list                         # prints active configuration
#
# Environment overrides:
#   export COMMS_BUS=project-a        # selects ~/.agentcomms/project-a
#   export COMMS_ROOT=~/.agentcomms   # explicit override of bus root path
#   export COMMS_ME=planner           # your agent name
#   export COMMS_GIT=1                # enable git sync
#
# Commands:
#   comms register "plans the work"   # announce yourself
#   comms peers                       # who else is here
#   comms send builder "do the thing" # leave a message
#   comms inbox                       # how many are waiting
#   comms read                        # print unread oldest-first, then ack them
#   comms config [list|get|set]       # manage settings
#
# Safety & filtering:
#   - Token protection: pre-flight check blocks tokens (ghp_, gho_, bearer ) and private keys
#   - Custom filter: checks local $ROOT/.comms-filter for blocked regex patterns
#   - Override with COMMS_FORCE=1
#
# Design rule that makes it lock-free: a message is a NEW FILE, never an edit.
# Two agents therefore never write the same path, so there is nothing to lock
# and, under git, nothing that can ever merge-conflict.

set -eu

die() { echo "comms: $1" >&2; exit 1; }

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
CFG_GIT=$(get_config git 2>/dev/null || true)
CFG_ME=$(get_config me 2>/dev/null || true)

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

ME="${COMMS_ME:-$CFG_ME}"
GIT="${COMMS_GIT:-${CFG_GIT:-0}}"

# Append-only is what makes the bus lock-free, and on its own it is also what turns a
# channel into an archive. An agent cannot tell a live instruction from a dead one -
# both are a file with a name and a first line - so handed the archive it works through
# the archive. Everything therefore expires, on three windows, because the three things
# on the bus fail differently.
CFG_TTL=$(get_config ttl_days 2>/dev/null || true)
CFG_MAIL_TTL=$(get_config mail_ttl_days 2>/dev/null || true)
CFG_PEER_TTL=$(get_config peer_ttl_days 2>/dev/null || true)
TTL="${COMMS_TTL_DAYS:-${CFG_TTL:-7}}"            # broadcasts, and mail already read
MAIL_TTL="${COMMS_MAIL_TTL_DAYS:-${CFG_MAIL_TTL:-30}}"   # mail still uncollected
PEER_TTL="${COMMS_PEER_TTL_DAYS:-${CFG_PEER_TTL:-14}}"   # a registration nobody refreshes

need_me() { [ -n "$ME" ] || die "set COMMS_ME to your agent name (or: comms config set me <name>)"; }

stamp() { date -u +%Y-%m-%dT%H-%M-%SZ; }
# bsd and gnu date disagree on relative times, so try one form then the other
hour_ago() { date -u -v-1H +%Y-%m-%dT%H-%M-%SZ 2>/dev/null || date -u -d '1 hour ago' +%Y-%m-%dT%H-%M-%SZ 2>/dev/null; }
days_ago() { date -u -v-"$1"d +%Y-%m-%dT%H-%M-%SZ 2>/dev/null || date -u -d "$1 days ago" +%Y-%m-%dT%H-%M-%SZ 2>/dev/null; }
rand() { LC_ALL=C tr -dc 'a-f0-9' < /dev/urandom | dd bs=1 count=6 2>/dev/null; }

# Age comes out of the filename, never off mtime: a clone stamps every file with the
# moment it was checked out, so an mtime rule would call the whole archive new on a
# fresh machine and start eating live mail on an old one. Filenames already lead with
# the sender's UTC clock in the shape stamp() emits, so "older than" is a string compare.
is_msg() { case "$1" in [0-9][0-9][0-9][0-9]-*.md) return 0 ;; *) return 1 ;; esac; }

CURSOR=""
pull() {
  [ "$GIT" = 1 ] || return 0
  [ -d "$ROOT/.git" ] || return 0
  git -C "$ROOT" remote 2>/dev/null | grep -q . || return 0
  CURSOR="$ROOT/.git/comms-remote-sha"
  br=$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null) || return 0
  remote=$(git -C "$ROOT" ls-remote origin "$br" 2>/dev/null | cut -f1)
  seen=""
  [ -f "$CURSOR" ] && seen=$(cat "$CURSOR")
  if [ -n "$remote" ] && [ "$remote" = "$seen" ]; then return 0; fi
  git -C "$ROOT" pull --rebase -q 2>/dev/null || true
  [ -n "$remote" ] && echo "$remote" > "$CURSOR"
  return 0
}

push() {
  [ "$GIT" = 1 ] || return 0
  [ -d "$ROOT/.git" ] || return 0
  git -C "$ROOT" remote 2>/dev/null | grep -q . || return 0
  n=0
  while [ "$n" -lt 5 ]; do
    git -C "$ROOT" add -A >/dev/null 2>&1 || true
    git -C "$ROOT" -c user.name="$ME" -c user.email="$ME@agent.local" \
        commit -q -m "comms: $ME" >/dev/null 2>&1 || true
    if git -C "$ROOT" push -q 2>/dev/null; then
      [ -n "${CURSOR:-}" ] && git -C "$ROOT" rev-parse HEAD > "$CURSOR" 2>/dev/null
      return 0
    fi
    git -C "$ROOT" pull --rebase -q 2>/dev/null || true
    n=$((n + 1))
  done
  echo "comms: push failed after 5 tries, message is local only" >&2
}

content_filter() {
  to="$1"
  body="$2"

  # 1. Credential / token protection
  has_secret=0
  secret_type=""
  if printf '%s\n' "$body" | grep -Eq 'gh[po]_'; then
    has_secret=1
    secret_type="GitHub token (ghp_/gho_)"
  elif printf '%s\n' "$body" | grep -Eqi 'bearer[[:space:]]'; then
    has_secret=1
    secret_type="Bearer token"
  elif printf '%s\n' "$body" | grep -Eqi 'BEGIN[[:space:]]+([A-Za-z0-9_\-]+[[:space:]]+)?PRIVATE[[:space:]]+KEY'; then
    has_secret=1
    secret_type="Private key"
  fi

  if [ "$has_secret" = 1 ]; then
    if [ "${COMMS_FORCE:-0}" = 1 ]; then
      echo "comms: warning: $secret_type detected, but COMMS_FORCE=1 is set. Proceeding." >&2
    else
      die "safety guard: $secret_type detected in message body. Send aborted (override with COMMS_FORCE=1)."
    fi
  fi

  # 2. Custom filter file: $ROOT/.comms-filter
  combined="$to
$body"
  filter_file="$ROOT/.comms-filter"
  if [ -f "$filter_file" ]; then
    while IFS= read -r pattern || [ -n "$pattern" ]; do
      case "$pattern" in
        ''|'#'*) continue ;;
      esac
      pattern=$(echo "$pattern" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
      [ -n "$pattern" ] || continue
      if printf '%s\n' "$combined" | grep -Eqi "$pattern"; then
        if [ "${COMMS_FORCE:-0}" = 1 ]; then
          echo "comms: warning: blocked pattern '$pattern' detected by $filter_file, but COMMS_FORCE=1 is set. Proceeding." >&2
        else
          die "filter guard: blocked pattern '$pattern' detected by bus filter ($filter_file). Send aborted (override with COMMS_FORCE=1)."
        fi
      fi
    done < "$filter_file"
  fi

  # 3. Size. Every message is read by an agent and paid for in tokens, so the cost of
  # a long one falls on its readers rather than its sender. The bus sits next to a
  # vault and a git history: naming a note or a sha costs a line, pasting what they
  # contain costs every reader the whole thing.
  max_chars="${COMMS_MAX_CHARS:-500}"
  len=$(printf '%s' "$body" | wc -c | tr -d ' ')
  if [ "$len" -gt "$max_chars" ]; then
    if [ "${COMMS_FORCE:-0}" = 1 ]; then
      echo "comms: warning: message is $len chars against a $max_chars cap, but COMMS_FORCE=1 is set. Proceeding." >&2
    else
      die "size guard: message is $len chars and the cap is $max_chars. Say it in one line and name the note, task file or commit sha instead of pasting it (raise with COMMS_MAX_CHARS, or override with COMMS_FORCE=1)."
    fi
  fi

  # 4. Rate. Two agents can acknowledge each other until a budget is gone, and neither
  # notices, because each message looks reasonable on its own. Counting is free: the
  # filenames already on disk carry the sender and the time.
  # A broadcast is one send and N reads, so counting it once charges the sender for a
  # twentieth of what the fleet actually pays. Priced by fan-out, the cap of twenty
  # means twenty deliveries: four broadcasts to a fleet of seven cost twenty-eight and
  # stop at three, which is the behaviour that was wanted all along.
  max_hour="${COMMS_MAX_PER_HOUR:-20}"
  peers=$(ls "$ROOT/agents"/*.md 2>/dev/null | wc -l | tr -d ' ')
  [ "$peers" -gt 0 ] || peers=1
  ago=$(hour_ago)
  if [ -n "$ago" ]; then
    recent=0
    for m in $(find "$ROOT/inbox" "$ROOT/broadcast" -name "*--$ME--*.md" 2>/dev/null); do
      t=$(basename "$m"); t=${t%%--*}
      [ "$t" \> "$ago" ] || continue
      case "$m" in
        "$ROOT"/broadcast/*) recent=$((recent + peers)) ;;
        *) recent=$((recent + 1)) ;;
      esac
    done
    if [ "$recent" -ge "$max_hour" ]; then
      if [ "${COMMS_FORCE:-0}" = 1 ]; then
        echo "comms: warning: $recent messages sent in the last hour against a $max_hour cap, but COMMS_FORCE=1 is set. Proceeding." >&2
      else
        die "rate guard: you have sent $recent messages in the last hour and the cap is $max_hour. An exchange this long is a loop rather than progress: stop and tell the human what you are stuck on (raise with COMMS_MAX_PER_HOUR, or override with COMMS_FORCE=1)."
      fi
    fi
  fi

  # 5. Environment-level blocked patterns
  if [ -n "${COMMS_BLOCKED_PATTERNS:-}" ]; then
    if printf '%s\n' "$combined" | grep -Eqi "$COMMS_BLOCKED_PATTERNS"; then
      if [ "${COMMS_FORCE:-0}" = 1 ]; then
        echo "comms: warning: blocked pattern detected by COMMS_BLOCKED_PATTERNS, but COMMS_FORCE=1 is set. Proceeding." >&2
      else
        die "filter guard: blocked pattern detected by COMMS_BLOCKED_PATTERNS. Send aborted (override with COMMS_FORCE=1)."
      fi
    fi
  fi
}

cmd_config() {
  sub="${1:-list}"
  case "$sub" in
    list)
      if [ -f "$CONFIG_FILE" ]; then
        echo "config ($CONFIG_FILE):"
        cat "$CONFIG_FILE"
      else
        echo "no config file found ($CONFIG_FILE)"
      fi
      echo "resolved settings:"
      echo "  BUS:  ${BUS:-<unset>}"
      echo "  ROOT: $ROOT"
      echo "  ME:   ${ME:-<unset>}"
      echo "  GIT:  $GIT"
      ;;
    get)
      key="${2:-}"; [ -n "$key" ] || die "usage: comms config get <key>"
      get_config "$key" 2>/dev/null || echo "(unset)"
      ;;
    set)
      key="${2:-}"; val="${3:-}"
      [ -n "$key" ] || die "usage: comms config set <key> <val>"
      mkdir -p "$(dirname "$CONFIG_FILE")"
      if [ -f "$CONFIG_FILE" ] && grep -q "^[[:space:]]*$key[[:space:]]*=" "$CONFIG_FILE"; then
        sed "s|^[[:space:]]*$key[[:space:]]*=.*|$key=$val|" "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
      else
        echo "$key=$val" >> "$CONFIG_FILE"
      fi
      echo "set $key=$val in $CONFIG_FILE"
      ;;
    *) die "usage: comms config [list|get <key>|set <key> <val>]" ;;
  esac
}

cmd_register() {
  need_me
  mkdir -p "$ROOT/agents" "$ROOT/inbox/$ME/done" "$ROOT/broadcast"
  touch "$ROOT/inbox/$ME/.gitkeep" "$ROOT/inbox/$ME/done/.gitkeep" "$ROOT/broadcast/.gitkeep"
  pull
  if [ -f "$ROOT/agents/$ME.md" ]; then
    prev=$(sed -n 's/^host: //p' "$ROOT/agents/$ME.md")
    if [ -n "$prev" ] && [ "$prev" != "$(hostname)" ]; then
      die "name '$ME' is already registered on host '$prev'. Names must be unique across the whole bus, try COMMS_ME=$ME-$(hostname)"
    fi
  fi
  # Coming back after being retired for idleness is just registering again.
  rm -f "$ROOT/agents/retired/$ME.md"
  {
    echo "name: $ME"
    echo "role: ${1:-unspecified}"
    echo "host: $(hostname)"
    echo "cwd: $(pwd)"
    echo "seen: $(stamp)"
  } > "$ROOT/agents/$ME.md"
  # A new agent starts its broadcast cursor at the newest broadcast rather than at the
  # beginning of time, so joining does not mean replaying every broadcast ever sent.
  # History belongs in the notes and the git log; the bus is what happened since you
  # arrived. Only on a first registration - re-running `register` later must not move
  # the cursor past broadcasts this agent has not read yet.
  if [ ! -f "$(bcursor)" ]; then
    { echo "$BMARK"
      for f in "$ROOT/broadcast"/*.md; do
        [ -e "$f" ] || break
        basename "$f"
      done
    } > "$(bcursor)"
  fi
  push
  echo "registered $ME on bus '${BUS:-default}' ($ROOT)"
}

cmd_peers() {
  pull
  [ -d "$ROOT/agents" ] || { echo "no peers"; return 0; }
  pcut=$(days_ago "$PEER_TTL") || pcut=""
  for f in "$ROOT/agents"/*.md; do
    [ -e "$f" ] || { echo "no peers"; return 0; }
    n=$(basename "$f" .md)
    r=$(sed -n 's/^role: //p' "$f")
    s=$(sed -n 's/^seen: //p' "$f")
    w=$(ls "$ROOT/inbox/$n"/*.md 2>/dev/null | wc -l | tr -d ' ')
    # Flagged before it is retired, so the list warns you off an address that has very
    # likely stopped listening, rather than only telling you once it is already gone.
    flag=""
    if [ -n "$pcut" ] && [ -n "$s" ] && [ "$s" \< "$pcut" ]; then flag="  ·  IDLE, retiring"; fi
    echo "$n  ·  $r  ·  seen $s  ·  $w waiting$flag"
  done
}

cmd_send() {
  need_me
  to="${1:-}"; [ -n "$to" ] || die "usage: comms send <to|all> <message>"
  shift
  body="$*"
  [ -n "$body" ] || body=$(cat)
  content_filter "$to" "$body"
  pull
  if [ "$to" = all ]; then
    dir="$ROOT/broadcast"
  else
    if [ ! -f "$ROOT/agents/$to.md" ]; then
      # Worth telling apart from a typo, because it replaces the quiet failure: before
      # names were retired, mail to an agent that had stopped collecting weeks ago landed
      # in a real inbox and the sender was told "sent to $to".
      [ -f "$ROOT/agents/retired/$to.md" ] &&
        die "'$to' was retired after $PEER_TTL days without checking in and is not collecting mail. It becomes reachable again if it re-registers (try: comms peers)"
      die "no such recipient '$to' (try: comms peers)"
    fi
    dir="$ROOT/inbox/$to"
  fi
  mkdir -p "$dir"
  # No front matter. The filename is <ts>--<sender>--<random> and the directory is the
  # recipient, so from/to/ts in the body would be four more lines that every reader
  # pays for to learn what the path already told them.
  f="$dir/$(stamp)--$ME--$(rand).md"
  printf '%s\n' "$body" > "$f"
  # You do not need your own broadcast delivered back to you, and reading it costs the
  # same as reading anyone else's, so record it as seen on the way out.
  [ "$to" = all ] && [ -d "$ROOT/inbox/$ME" ] && bmark_seen "$(basename "$f")"
  push
  if [ -n "${COMMS_NOTIFY:-}" ]; then
    COMMS_TO="$to" COMMS_FROM="$ME" COMMS_BUS="$BUS" sh -c "$COMMS_NOTIFY" >/dev/null 2>&1 || true
  fi
  echo "sent to $to"
}

bcursor() { echo "$ROOT/inbox/$ME/.broadcast-seen"; }

# One short line rather than a filename banner, since the filename is mostly a random
# suffix the reader has no use for: sender, time, and whether it went to everyone.
hdr() {
  b=$(basename "$1" .md); t=${b%%--*}; r=${b#*--}
  echo "> ${r%%--*} ${t}$2"
}

# The cursor used to hold one filename as a high-water mark, which was wrong: two
# broadcasts sent in the same second are separated only by their random suffix, so the
# one with the lower suffix sorted below a mark set by the other and was never
# delivered. It lists every basename it has seen instead. Exact, immune to ordering,
# and one short line per broadcast in a file only its own agent ever reads.
BMARK="#comms-seen-v2"

# A v1 cursor is a bare filename. Reading it as a list would redeliver everything below
# it, so convert it once, keeping its high-water meaning for the history it covered.
bmigrate() {
  c=$(bcursor)
  [ -f "$c" ] || return 0
  head -n 1 "$c" | grep -q "^$BMARK$" && return 0
  old=$(head -n 1 "$c")
  { echo "$BMARK"
    for f in "$ROOT/broadcast"/*.md; do
      [ -e "$f" ] || break
      n=$(basename "$f")
      [ "$n" \> "$old" ] || echo "$n"
    done
  } > "$c.tmp" && mv "$c.tmp" "$c"
}

# An agent deep in its own work still wants direct mail but not every sweep report.
# `inbox/<name>/.mute`, one sender per line, drops that sender's broadcasts on the
# reader's side: the cursor still advances, so muting is never a backlog.
bmuted() {
  m="$ROOT/inbox/$ME/.mute"
  [ -f "$m" ] || return 1
  b=$(basename "$1" .md); r=${b#*--}
  grep -qxF "${r%%--*}" "$m"
}

bunseen() {
  bmigrate
  c=$(bcursor)
  # The floor is the half of expiry that needs nothing to have run yet. gc has to have
  # swept somewhere to shrink the directory, and an agent that registered before the
  # cursor was seeded has no record of the old ones at all; the floor means neither can
  # be shown a broadcast older than the window, on the very next read. Expiry becomes a
  # property of reading rather than a job somebody has to remember.
  floor=$(days_ago "$TTL") || floor=""
  for f in "$ROOT/broadcast"/*.md; do
    [ -e "$f" ] || break
    n=$(basename "$f")
    if [ -n "$floor" ] && [ "$n" \< "$floor" ]; then continue; fi
    if [ ! -f "$c" ] || ! grep -qxF "$n" "$c"; then echo "$f"; fi
  done
}

bmark_seen() {
  c=$(bcursor)
  [ -f "$c" ] || { mkdir -p "$(dirname "$c")"; echo "$BMARK" > "$c"; }
  echo "$1" >> "$c"
}

cmd_inbox() {
  need_me
  pull
  n=$(ls "$ROOT/inbox/$ME"/*.md 2>/dev/null | wc -l | tr -d ' ')
  b=$(bunseen | wc -l | tr -d ' ')
  echo "$n unread, $b broadcast"
}

cmd_read() {
  need_me
  pull
  any=0
  for f in "$ROOT/inbox/$ME"/*.md; do
    [ -e "$f" ] || break
    any=1
    hdr "$f" ""
    cat "$f"
    echo
    mv "$f" "$ROOT/inbox/$ME/done/"
  done
  for f in $(bunseen); do
    if bmuted "$f"; then bmark_seen "$(basename "$f")"; continue; fi
    any=1
    hdr "$f" " all"
    cat "$f"
    echo
    bmark_seen "$(basename "$f")"
  done
  [ "$any" = 1 ] || echo "(empty)"
  af="$ROOT/agents/$ME.md"
  if [ -f "$af" ]; then
    sed "s/^seen: .*/seen: $(stamp)/" "$af" > "$af.tmp" && mv "$af.tmp" "$af"
  fi
  push
  maybe_gc
}

# A delete is not an edit, so gc keeps the one rule the bus is built on: two machines
# sweeping at once both remove the same path, and git resolves delete-against-delete as
# a delete rather than a conflict. Nothing here ever rewrites a message.
#
# What gc does NOT do is redact. The files leave the working tree; every one of them is
# still in the git history, which on a git transport is the transcript the bus is valued
# for. Retention bounds what an agent is asked to read, not what the repo remembers, so
# the rule about keeping secrets out of messages is exactly as binding as before.
cmd_gc() {
  dry=0
  for a in "$@"; do
    case "$a" in
      --dry-run|-n) dry=1 ;;
      *) die "usage: comms gc [--dry-run]" ;;
    esac
  done
  [ -d "$ROOT" ] || die "no bus at $ROOT"
  pull

  bcut=$(days_ago "$TTL")      || die "no usable date arithmetic here, nothing expired"
  mcut=$(days_ago "$MAIL_TTL") || die "no usable date arithmetic here, nothing expired"
  pcut=$(days_ago "$PEER_TTL") || die "no usable date arithmetic here, nothing expired"

  old=0 cold=0 gone=0

  # Broadcasts, and mail already delivered once. done/ is a receipt drawer, not an
  # archive: the move into it is the read receipt, and the receipt stops being useful
  # long before the disk notices.
  for f in "$ROOT/broadcast"/*.md "$ROOT"/inbox/*/done/*.md; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    is_msg "$b" || continue
    if [ "$b" \< "$bcut" ]; then
      if [ "$dry" = 1 ]; then echo "expire       $f"; else rm -f "$f"; fi
      old=$((old + 1))
    fi
  done

  # Mail nobody ever collected gets a much longer rope, because dropping it is the only
  # lossy thing gc does: unlike a broadcast it was addressed to someone, and unlike
  # done/ it was never delivered. Past this window the agent it was for is not coming
  # back for it, and keeping it only means the next agent to take that name inherits a
  # stranger's backlog on its first read.
  for f in "$ROOT"/inbox/*/*.md; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    is_msg "$b" || continue
    if [ "$b" \< "$mcut" ]; then
      if [ "$dry" = 1 ]; then echo "uncollected  $f"; else rm -f "$f"; fi
      cold=$((cold + 1))
    fi
  done

  # The seen-list cursor is the one file that grows with every broadcast the bus has
  # ever carried, so expiring broadcasts without pruning it just moves the unbounded
  # growth somewhere less visible. A line whose broadcast is gone can never match again.
  for c in "$ROOT"/inbox/*/.broadcast-seen; do
    [ -e "$c" ] || continue
    [ "$dry" = 1 ] && continue
    { echo "$BMARK"
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        [ "$line" = "$BMARK" ] && continue
        [ -e "$ROOT/broadcast/$line" ] && echo "$line"
      done < "$c"
    } > "$c.tmp" && mv "$c.tmp" "$c"
  done

  # Registrations are retired, not deleted: the file is the evidence the name was taken,
  # and `send` reads retired/ to explain itself. `read` refreshes `seen`, so anything
  # this stale has not looked at the bus in PEER_TTL days.
  for f in "$ROOT/agents"/*.md; do
    [ -e "$f" ] || continue
    s=$(sed -n 's/^seen: //p' "$f")
    [ -n "$s" ] || continue
    if [ "$s" \< "$pcut" ]; then
      if [ "$dry" = 1 ]; then
        echo "retire       $(basename "$f" .md)"
      else
        mkdir -p "$ROOT/agents/retired"
        mv "$f" "$ROOT/agents/retired/"
      fi
      gone=$((gone + 1))
    fi
  done

  [ "$dry" = 1 ] || push
  echo "gc: $old expired, $cold uncollected, $gone retired (windows ${TTL}d/${MAIL_TTL}d/${PEER_TTL}d)"
}

# Per-clone and deliberately outside the bus. Put the stamp on the bus and the first
# machine to sweep pushes it and talks every other machine out of sweeping; how often
# this clone has swept is local business. The .git path is where pull() already keeps
# its remote sha, and ROOT differs per bus, so this is per-bus for free.
gcstamp() {
  if [ -d "$ROOT/.git" ]; then echo "$ROOT/.git/comms-gc-last"; else echo "$ROOT/.comms-gc-last"; fi
}

# "Cleans up after itself" has to mean without anyone remembering to, so the sweep rides
# on `read` - the one command every agent is already told to run constantly - throttled
# to once a day per clone. The stamp is written before the sweep rather than after, so a
# gc that fails costs one quiet day instead of re-running on every read.
maybe_gc() {
  gs=$(gcstamp)
  today=$(date -u +%Y-%m-%d)
  if [ -f "$gs" ] && [ "$(cat "$gs" 2>/dev/null)" = "$today" ]; then return 0; fi
  echo "$today" > "$gs" 2>/dev/null || return 0
  # In a subshell, because gc reports problems through die() and die() exits. Housekeeping
  # must never take down the `read` that invited it, least of all after the mail has been
  # printed and pushed; `|| true` alone would not catch an exit.
  ( cmd_gc ) >/dev/null 2>&1 || true
}

case "${1:-}" in
  config)   shift; cmd_config "$@" ;;
  register) shift; cmd_register "$@" ;;
  peers)    shift; cmd_peers ;;
  send)     shift; cmd_send "$@" ;;
  inbox)    shift; cmd_inbox ;;
  read)     shift; cmd_read ;;
  gc)       shift; cmd_gc "$@" ;;
  *) die "usage: comms {register <role>|peers|send <to> <msg>|inbox|read|gc [--dry-run]|config [list|get|set]}" ;;
esac
