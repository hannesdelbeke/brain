#!/bin/sh
# Retention tests for comms.sh. Run: sh test-retention.sh
# Plain-dir bus, no git, isolated HOME so nothing touches the real bus.
set -eu
W="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
T="${TMPDIR:-/tmp}/comms-retention-test.$$"
C="sh $W/comms.sh"
fail=0
ok()  { echo "PASS  $1"; }
bad() { echo "FAIL  $1"; fail=1; }

rm -rf "$T"; mkdir -p "$T"
export HOME="$T" COMMS_ROOT="$T" COMMS_GIT=0 COMMS_CONFIG="$T/config"
TODAY=$(date -u +%Y-%m-%d)
STAMP="$T/.comms-gc-last"
hold_gc() { echo "$TODAY" > "$STAMP"; }
free_gc() { rm -f "$STAMP"; }
BMARK="#comms-seen-v2"

sh -n "$W/comms.sh"       || { echo "FAIL  comms.sh syntax"; exit 1; }; ok "comms.sh syntax"
sh -n "$W/comms-watch.sh" || { echo "FAIL  comms-watch syntax"; exit 1; }; ok "comms-watch.sh syntax"

hold_gc
COMMS_ME=alice $C register "old timer" >/dev/null; hold_gc
COMMS_ME=bob   $C register "builder"   >/dev/null; hold_gc

# artefacts from months ago
printf 'DROP EVERYTHING AND MIGRATE\n' \
  > "$T/broadcast/2026-01-02T03-04-05Z--alice--aaa111.md"
printf 'ancient uncollected\n' \
  > "$T/inbox/alice/2026-01-02T03-04-06Z--bob--bbb222.md"
printf 'ancient already read\n' \
  > "$T/inbox/bob/done/2026-01-02T03-04-07Z--alice--ccc333.md"
sed 's/^seen: .*/seen: 2026-01-02T03-04-05Z/' "$T/agents/alice.md" > "$T/agents/alice.tmp"
mv "$T/agents/alice.tmp" "$T/agents/alice.md"

# 1. an agent whose cursor predates the archive is still floored, with gc held off
rm -f "$T/inbox/bob/.broadcast-seen"
out=$(COMMS_ME=bob $C read); hold_gc
case "$out" in
  *"DROP EVERYTHING"*) bad "cursorless agent replays the archive" ;;
  *) ok "cursorless agent is floored by the retention window" ;;
esac

# 2. a broadcast sent now must still be delivered
COMMS_ME=alice $C send all "this one is current" >/dev/null; hold_gc
out=$(COMMS_ME=bob $C read); hold_gc
case "$out" in
  *"this one is current"*) ok "a current broadcast is still delivered" ;;
  *) bad "a current broadcast was swallowed by the floor" ;;
esac

# 3. dry run reports without removing
before=$(find "$T" -name '*.md' | wc -l | tr -d ' ')
COMMS_ME=bob $C gc --dry-run >/dev/null
after=$(find "$T" -name '*.md' | wc -l | tr -d ' ')
[ "$before" = "$after" ] && ok "gc --dry-run removes nothing" || bad "gc --dry-run deleted files"

# 4. a real sweep expires all three kinds and retires the idle agent
COMMS_ME=bob $C gc >/dev/null
[ -e "$T/broadcast/2026-01-02T03-04-05Z--alice--aaa111.md" ] \
  && bad "old broadcast survived gc" || ok "old broadcast expired"
[ -e "$T/inbox/bob/done/2026-01-02T03-04-07Z--alice--ccc333.md" ] \
  && bad "old done/ receipt survived gc" || ok "old done/ receipt expired"
[ -e "$T/inbox/alice/2026-01-02T03-04-06Z--bob--bbb222.md" ] \
  && bad "old uncollected mail survived gc" || ok "old uncollected mail expired"
[ -f "$T/agents/retired/alice.md" ] && ok "idle agent retired" || bad "idle agent not retired"
[ -f "$T/agents/alice.md" ] && bad "retired agent still listed live" \
  || ok "retired agent dropped from the live list"
[ -f "$T/agents/bob.md" ] && ok "live agent untouched" || bad "gc retired a live agent"

# 5. the seen-list cursor is pruned of lines whose broadcast is gone, keeping its marker
cur="$T/inbox/bob/.broadcast-seen"
head -n 1 "$cur" | grep -qx "$BMARK" && ok "cursor keeps its version marker" \
  || bad "cursor lost its version marker"
grep -q "aaa111" "$cur" && bad "cursor still lists an expired broadcast" \
  || ok "cursor pruned of expired broadcasts"

# 6. gc must not touch anything inside the window
COMMS_ME=bob $C send alice "fresh mail" 2>/dev/null >/dev/null || true
COMMS_ME=bob $C gc >/dev/null
COMMS_ME=alice $C register "back again" >/dev/null; hold_gc
COMMS_ME=bob $C send alice "second fresh" >/dev/null
COMMS_ME=bob $C gc >/dev/null
out=$(COMMS_ME=alice $C read); hold_gc
case "$out" in
  *"second fresh"*) ok "gc leaves current mail alone" ;;
  *) bad "gc ate current mail" ;;
esac

# 7. sending to a retired name fails loudly rather than into a dead inbox
COMMS_ME=carol $C register "temp" >/dev/null; hold_gc
sed 's/^seen: .*/seen: 2026-01-02T03-04-05Z/' "$T/agents/carol.md" > "$T/agents/carol.tmp"
mv "$T/agents/carol.tmp" "$T/agents/carol.md"
COMMS_ME=bob $C gc >/dev/null
if COMMS_ME=bob $C send carol "are you there" >/dev/null 2>"$T/err"; then
  bad "send to a retired agent silently succeeded"
else
  grep -q retired "$T/err" && ok "send to a retired agent explains itself" \
    || bad "send to a retired agent failed with the wrong message"
fi

# 8. re-registering un-retires and restores reachability
COMMS_ME=carol $C register "back" >/dev/null; hold_gc
{ [ -f "$T/agents/carol.md" ] && [ ! -f "$T/agents/retired/carol.md" ]; } \
  && ok "re-register un-retires" || bad "re-register did not un-retire"
COMMS_ME=bob $C send carol "welcome back" >/dev/null \
  && ok "revived agent is reachable again" || bad "revived agent unreachable"

# 9. re-registering must not disturb an existing cursor
cp "$T/inbox/bob/.broadcast-seen" "$T/cur.before"
COMMS_ME=bob $C register "builder" >/dev/null; hold_gc
cmp -s "$T/cur.before" "$T/inbox/bob/.broadcast-seen" \
  && ok "re-register preserves the broadcast cursor" || bad "re-register moved the cursor"

# 10. with the throttle clear, a plain read sweeps on its own
free_gc
printf 'another ancient one\n' > "$T/broadcast/2026-01-03T03-04-05Z--bob--ddd444.md"
COMMS_ME=bob $C read >/dev/null
[ -e "$T/broadcast/2026-01-03T03-04-05Z--bob--ddd444.md" ] \
  && bad "read did not sweep with the throttle clear" || ok "read sweeps on its own"
[ -f "$STAMP" ] && ok "read records a throttle stamp" || bad "no throttle stamp written"

# 11. and does not sweep twice in one day
printf 'planted after the sweep\n' > "$T/broadcast/2026-01-04T03-04-05Z--bob--eee555.md"
COMMS_ME=bob $C read >/dev/null
[ -e "$T/broadcast/2026-01-04T03-04-05Z--bob--eee555.md" ] \
  && ok "throttle holds for the rest of the day" || bad "read swept twice in one day"

# 12. read still exits 0 even if gc cannot compute a cutoff
free_gc
out=$(COMMS_TTL_DAYS=notanumber COMMS_ME=bob $C read >/dev/null 2>&1; echo "rc=$?")
[ "$out" = "rc=0" ] && ok "a broken retention setting cannot break read" \
  || bad "read exited nonzero when gc failed ($out)"

echo
[ "$fail" = 0 ] && echo "ALL TESTS PASSED" || echo "SOME TESTS FAILED"
exit "$fail"
