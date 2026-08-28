---
date: 2026-08-27
tags:
  - technical
  - search
  - pkm
  - performance
---
Reindexing a corpus of append-only files does not need to read the files. It needs to read what was appended. This is how the session index stops reparsing 1.5 GB to find four new turns, written plainly because the idea is simple and the implementation is where it gets interesting. Part of [[pkm-search]], measured in [[2026-08-27 vault index work log]].

## The idea

A session transcript is a file that only grows. Every turn is one line appended to the end, and the lines already there are never touched again.

So reading it from the top every time is reading yesterday's file to find today's sentence. Instead, remember the byte you stopped at. Next run, seek to that byte and read from there. A bookmark, in a book where new pages only ever appear at the back.

That is the whole idea. Everything below is the part that makes it safe.

## The three things that go wrong

**The file got shorter.** Then it was not appended to, it was replaced, and the bookmark points past the end or into the middle of something else. If the size is below what was recorded, read the whole thing.

**The file was rewritten to the same length or longer.** Rarer, and the bookmark still looks valid. So the bookmark also stores a hash of the 4 KB immediately before it: if those bytes changed, the file underneath the bookmark is not the file the bookmark was made in. Hashing the whole prefix would cost exactly the read the bookmark exists to avoid, so it hashes the end of it and accepts that a rewrite which preserves 4 KB at a precise offset is not a thing that happens.

**The last line is half written.** The process appending is still mid-line. A line with no newline at the end of it is not a line yet, so reading stops at the last newline and bookmarks there. The rest arrives next run, when it is whole.

## The part that is not obvious

A bookmark tells you what to skip. It does not tell you what was in the part you skipped, and the indexer needs every row on every run, because it rewrites the search tables from scratch and deletes anything not handed to it.

Storing a second copy of the parsed rows next to the bookmark would work and would be silly: the index already holds every section with its text. So the skipped part is read back out of the index, and only the appended bytes are parsed. The bookmark file holds five numbers per transcript and no content at all.

Which introduces the fourth failure: if a run parses new bytes and then dies before writing them, the bookmark advances while the index does not, and those turns are skipped forever. So the bookmark also records how many sections the transcript had, and disagreeing with the index is a full reread. Cheap, and it turns a silent hole into a slow run.

## The fifth failure, which is the interesting one

Change how the parser works and every row already in the index was produced by the old parser. Resume happily serves them forever, and the corpus quietly becomes a mixture of two parsers with no sign that anything is wrong.

The fix is to make the bookmark file depend on the code that wrote it: it stores a hash of the scanner's own source, plus the chunking version. Edit the scanner, the hash moves, every offset is invalid, the next run is a full pass. No one has to remember to bump a version, which is the point, because no one does.

## What it bought

Over 859 transcripts: parsing drops from 12.46s to 0.78s, and a whole metadata-only pass from 19.24s to 7.78s. The remaining 6.6s is the search tables being rebuilt from scratch, which is now the floor and the next thing worth attacking.

The reason to care is not the seconds. A 55 second reindex is something a person runs occasionally and then stops running, so the index is as fresh as the last time someone remembered. A sub-second parse is something a file watcher can run on every write, which is the difference between a search index and a search index that is true.

## Who did it first

Every log shipper, and Splunk in this exact shape: its fishbucket stores a CRC of a file's first 256 bytes as identity, a byte offset, and a CRC of the content at that offset, and treats a mismatch as a rewrite. Filebeat, Logstash, Fluentd and Vector all keep the same kind of record, and all of them additionally identify a file by inode or by a hash of its head, so a rotated or renamed file is followed rather than reread. That part does not apply to a corpus where every file is named by a session uuid and never rotated, but it is the first thing to add if that ever changes. Surveyed in [[2026-08-27 what already exists, prior art for a local hybrid search engine]].

## Where it applies

Any [[corpus]] whose files only grow: transcripts, logs, append-only exports, chat histories. Not markdown notes, which get edited in the middle, and which is why the vault index still reads every file and invalidates by hash instead. See [[cross-agent session indexing architecture]] for what a transcript scanner does with the bytes once it has them, and [[offline GPU embeddings with incremental cache]] for the same argument one layer down, where the expensive thing is the vector rather than the parse.
