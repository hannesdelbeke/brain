#!/usr/bin/env python3
"""Block a commit that reintroduces a private term into this public vault.

Three leaks of the same shape reached this repository's history before this
existed, each fixed by a `git filter-repo` rewrite and a force push. Every one
of them would have been caught by grepping the staged diff for a literal
string, so that is all this does.

The term list cannot be stored in plaintext here -- a file naming the strings
would be the leak it is meant to prevent. Terms are stored as SHA-256 of the
lowercased term instead, and the scanner hashes every 1-, 2- and 3-word window
of the text it is given and looks for a match. That is not encryption and it
would not survive someone who already knows what to guess; it only keeps the
words themselves out of a public checkout and out of search results.

To add a term:

    printf '%s' "the term in lowercase" | sha256sum

and paste the hash into TERM_HASHES. Multi-word terms are joined by single
spaces with punctuation dropped, so `Some Project V4.md` is added as the
three words `some project v4`, and a term of more than MAX_WORDS words will
never match.

Deliberately not on the list: `evergreen` and `onyx`, which are ordinary
vocabulary and the name of a real search product respectively, both used
legitimately in public notes here. Only their `.md` filename forms ever
leaked, and blocking the bare words would have cost more false positives than
it is worth.

Usage:
    leak_scan.py --staged            scan added lines of the staged diff
    leak_scan.py --message <file>    scan a commit message file
    leak_scan.py --selftest          run the built-in checks
"""

import hashlib
import re
import subprocess
import sys

# sha256 of each lowercased private term. See the module docstring to add one.
TERM_HASHES = {
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
    "REDACTED-DIGEST",
}

MAX_WORDS = 3
WORD = re.compile(r"[a-z0-9]+")


def hits(text):
    """Return the private terms found in text, in plaintext, for local output."""
    words = WORD.findall(text.lower())
    found = []
    for size in range(1, MAX_WORDS + 1):
        for i in range(len(words) - size + 1):
            window = " ".join(words[i:i + size])
            if hashlib.sha256(window.encode()).hexdigest() in TERM_HASHES:
                found.append(window)
    return found


def staged_additions():
    """Yield (path, line) for every line the staged diff adds."""
    diff = subprocess.run(
        ["git", "diff", "--cached", "--unified=0", "--diff-filter=ACMR"],
        capture_output=True,
    ).stdout.decode("utf-8", "replace")
    path = "?"
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            yield path, line[1:]


def report(offences):
    """Print the offending lines and return the hook's exit code."""
    if not offences:
        return 0
    print("pre-commit: refusing to commit, private terms found.", file=sys.stderr)
    print("", file=sys.stderr)
    for where, terms, line in offences[:20]:
        print("  %s: %s" % (where, ", ".join(sorted(set(terms)))), file=sys.stderr)
        print("    %s" % line.strip()[:160], file=sys.stderr)
    if len(offences) > 20:
        print("  ... and %d more" % (len(offences) - 20), file=sys.stderr)
    print("", file=sys.stderr)
    print("This repository is public. Generalise the term before committing --", file=sys.stderr)
    print("editing it out in a later commit does not remove it from history.", file=sys.stderr)
    print("", file=sys.stderr)
    print("If this is a false positive:  PKM_ALLOW_LEAK_TERM=1 git commit ...", file=sys.stderr)
    return 1


def selftest():
    # Probes, not real terms -- writing a real one here would put it back in
    # the public checkout, which is the thing this file exists to prevent.
    one, two = "zorbex", "quux v9"
    TERM_HASHES.update(hashlib.sha256(t.encode()).hexdigest() for t in (one, two))

    assert hits("nothing to see here") == []
    assert hits("the Zorbex vault") == [one], "case folding"
    assert hits("C:\\Users\\H\\Documents\\GitHub\\Zorbex") == [one], "windows path"
    assert hits("proj-incubator-zorbex") == [one], "hyphenated slug"
    assert hits("`quux v9.md` and `evergreen.md`") == [two], "multi-word term"
    assert hits("zorbexes") == [], "no substring matching, terms are whole words"
    assert hits("Onyx (formerly Danswer) is a search product") == []
    assert hits("an evergreen concept note") == []
    print("leak_scan selftest ok")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    if "--message" in argv:
        with open(argv[argv.index("--message") + 1], encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        found = hits(text)
        return report([("commit message", found, text.splitlines()[0])] if found else [])
    offences = []
    for path, line in staged_additions():
        found = hits(line)
        if found:
            offences.append((path, found, line))
    return report(offences)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
