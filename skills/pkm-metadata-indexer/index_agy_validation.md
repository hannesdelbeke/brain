# Validating `index_agy.py` on a machine with a real agy history

Instructions for an agent to run unattended. `index_agy.py` was written and
measured against 18 conversations on one machine, which is enough to prove the
parser runs and not enough to prove it is right. This is the check to run
somewhere with hundreds.

Every step below has a pass rule and a failure signature. Run them in order,
record the number each one produced, and stop at the first hard failure — a
wrong field map makes every later number meaningless.

Report at the end using the template at the bottom. Do not fix anything unless
the step says to; the point is a measurement, not a repair.

## 0. Setup

```
cd <the pkm-metadata-indexer directory>
python -c "import sys; print(sys.version)"
ls ~/.gemini/antigravity-cli/conversations/*.db | wc -l
du -sh ~/.gemini/antigravity-cli/conversations
```

Record the conversation count and the size on disk. Python must be 3.10 or
later, since the source uses `X | None` annotations.

Nothing is written to the agy directory except `.pkm_index.db` and
`.pkm_agy_state.json`, and both are safe to delete. The conversation databases
are opened read-only.

## 1. Selfcheck

```
python index_agy.py --selfcheck
```

**Pass:** the last line is `selfcheck ok`. Everything before it is the indexer
building a three-step fixture and is expected output.

**Fail:** an `AssertionError` whose message names what broke. This runs against
a synthetic database, so a failure here is a bug in the scanner and not in the
data — report it and stop.

## 2. The field map, which is the thing most likely to be wrong

The payload in `steps.step_payload` is protobuf with no schema published
anywhere, so the field numbers holding prose were read off one machine's
conversations. A different agy version can move them. This is the single check
that matters most.

```
python index_agy.py --probe --root ~/.gemini/antigravity-cli
```

The output is one block per step type, listing the payload fields by how many
characters of text they hold, with a sample of each. The two lines marked `*`
are what `PROSE_FIELDS` currently claims:

```
== step_type 14: 47 steps  <- prose
  *19.2: 16,927 chars | see pkm, i have https://github.com/...
== step_type 15: 680 steps  <- prose
   20.7.3: 578,157 chars | {"CommandLine":"gh auth status","Cwd":"C:\\Users\\...
  *20.1: 120,648 chars | I have started checking the GitHub CLI authentication status...
```

**Pass:** the sample beside each `*` is a sentence a person or the model wrote.
Step type 14 must sample something the user typed; step type 15 must sample
something the assistant said.

**Fail:** the sample beside a `*` is a UUID, a file path, a JSON object, or the
field is missing from the listing entirely. Then agy's payload has changed
shape. Find the replacement: in the block for step type 14, the prose field is
the highest-volume one whose sample reads as a user's own words; in the block
for step type 15, it is the highest-volume one that is neither a JSON object nor
the model's thinking. Thinking looks like `**Initiating Project Research** I've
started...` and is deliberately excluded. Report the two field paths you would
use instead of editing `PROSE_FIELDS`, and stop.

Also read the block list for a step type carrying prose that is not 14 or 15,
which would mean turns are being dropped. On the reference machine, step type 23
holds subagent task prompts at `30.19` and is knowingly not indexed. Report any
other step type whose top field samples as a sentence.

## 3. Index the corpus

```
python index_agy.py --root ~/.gemini/antigravity-cli
```

Record the note, section and link counts and the total run duration.

**Pass:** notes are within a few of the conversation count from step 0, and
sections are in the low hundreds per conversation at most.

**Fail, notes far below the conversation count:** the scanner is finding no
prose in most conversations, which is step 2's failure arriving late. A
conversation is skipped only when it produced no indexable text at all, which on
the reference machine happened once out of 18, for a conversation whose only
prompt was `/usage`.

Find out which ones were skipped and why:

```
python - <<'EOF'
import sqlite3, index_agy
from pathlib import Path
root = Path.home() / ".gemini/antigravity-cli"
have = {path for (path,) in sqlite3.connect(root / ".pkm_index.db").execute(
    "SELECT path FROM notes")}
for conversation in sorted(root.glob("conversations/*.db")):
    relative = conversation.relative_to(root).as_posix()
    if relative not in have:
        print("skipped", relative, "steps:", index_agy.step_count(conversation))
EOF
```

A skipped conversation with more than about 20 steps is a real miss. Report how
many there are and paste the output of the same probe over one of them.

## 4. What actually landed in the index

```
python - <<'EOF'
import sqlite3
from pathlib import Path
db = sqlite3.connect(Path.home() / ".gemini/antigravity-cli/.pkm_index.db")
print("notes    ", db.execute("SELECT count(*), sum(word_count) FROM notes").fetchone())
print("sections ", db.execute("SELECT count(*) FROM sections").fetchone()[0])
print("edges    ", db.execute("SELECT count(*) FROM edges").fetchone()[0])
print("by category")
for row in db.execute("SELECT category, count(*) FROM notes GROUP BY 1 ORDER BY 2 DESC LIMIT 8"):
    print("  ", row)
print("longest")
for row in db.execute("SELECT filename, word_count FROM notes ORDER BY 2 DESC LIMIT 5"):
    print("  ", row)
EOF
```

**Pass on titles:** the `filename` column reads as the first thing the user
asked in that conversation. A title that is a bare UUID means the conversation
had no user prose and fell back to the file name; a handful is fine, most of
them is a failure.

**Pass on categories:** the category is the basename of the workspace the
conversation ran in, taken from `history.jsonl`, and `agy` for conversations that
file does not cover. `history.jsonl` only records prompts typed in the directory
it was written from, so a large `agy` bucket is expected, not a defect.

**Pass on sections:** the count divided by the note count is between about 20
and 200. Below 20 means turns are being dropped, above 500 means something other
than turns is being indexed.

## 5. Size, which is the check that tool output is not being indexed

```
du -sh ~/.gemini/antigravity-cli/conversations ~/.gemini/antigravity-cli/.pkm_index.db
```

**Pass:** the index is under 15% of the conversations directory. The reference
machine is 2.4 MB against 44 MB, 5.5%.

**Fail:** anything approaching parity means the whitelist has stopped holding
and whole-file tool arguments or tool results are being stored. Confirm with:

```
python - <<'EOF'
import sqlite3
from pathlib import Path
db = sqlite3.connect(Path.home() / ".gemini/antigravity-cli/.pkm_index.db")
rows = db.execute("SELECT length(content), content FROM sections_fts"
                  " ORDER BY 1 DESC LIMIT 3").fetchall()
for size, text in rows:
    print(size, repr(text[:300]))
EOF
```

The longest sections should be prose. A 5,000-character section of source code
or command output is the failure.

## 6. Does it answer questions

Pick three things you actually remember doing in agy on this machine — a
specific bug, a specific repository, a specific command. For each:

```
python search_vault.py --db ~/.gemini/antigravity-cli/.pkm_index.db "<the thing>"
```

**Pass:** at least two of the three return the conversation where it happened in
the top five results. This is the only step that judges usefulness rather than
mechanics, so spend the effort on picking questions with a known answer rather
than on running more of them.

Record the three queries and whether each found its conversation.

## 7. The resume path

The scanner keeps a cursor per conversation, in `.pkm_agy_state.json`, and a
second run reparses only steps at or after it, taking the rest of the rows back
out of the index.

```
python index_agy.py --root ~/.gemini/antigravity-cli
```

**Pass:** the counts are identical to step 3 and `Vault Scan & Parse` is
meaningfully faster. On the reference machine, 0.78s becomes 0.26s.

**Fail on the counts:** rows are being lost or doubled across a resume. Rerun
with `--full` and compare — if `--full` gives the step 3 numbers and the resumed
run does not, the cursor is wrong.

Then use agy for one real turn, and run it again:

**Pass:** exactly one note's section count grew, and the conversation you just
used is the one that grew. The last step is deliberately reread each run, since
agy rewrites it in place while the answer streams.

## 8. Through the daemon

The scanner exists to be a second implementation of the `collect=` contract, so
the last check is that the daemon takes it with no code of its own:

```
python searchd.py --port 44791 --corpus "index_agy.py:scan_agy=agy=$HOME/.gemini/antigravity-cli"
```

In another shell:

```
curl -s "http://127.0.0.1:44791/search?q=<something+from+step+6>&limit=3&vault=agy"
```

**Pass:** JSON results whose `path` is `conversations/<uuid>.db` and whose
`heading` is the conversation title. Then `curl -s -X POST
http://127.0.0.1:44791/shutdown`.

Use port 44791 rather than the default 44771, so a daemon already serving the
vaults is not disturbed.

## Report

Fill this in and return it. Numbers, not adjectives.

```
machine:            <how many conversations, how large>
python:             <version>
1 selfcheck:        pass | fail <message>
2 field map:        pass | changed <old -> new, per step type>
  extra prose:      <step types holding prose that are not indexed>
3 index run:        <notes> notes, <sections> sections, <links> links, <seconds>s
  skipped:          <count> conversations, <the reason for the largest>
4 titles:           <how many of 20 sampled read as a real first question>
  sections/note:    <sections divided by notes>
5 size:             <index size> against <corpus size>, <percent>%
  longest section:  prose | not prose <what it was>
6 questions:        <query> -> found | not found   (three lines)
7 resume:           counts identical | differ <how>; <cold>s -> <warm>s
  after one turn:   <how many notes changed>
8 daemon:           pass | fail <what came back>
verdict:            <one sentence: is this worth registering at logon>
```
