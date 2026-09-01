#!/usr/bin/env python3
"""Block a commit that reintroduces a private term into this public vault.

Three leaks of the same shape reached this repository's history before this
existed, each fixed by a `git filter-repo` rewrite and a force push. Every one
of them would have been caught by grepping the staged diff for a literal
string, so that is all this does.

The term list cannot be stored in plaintext here -- a file naming the strings
would be the leak it is meant to prevent. Terms are stored as HMAC-SHA256 of
the lowercased term, keyed by a file that lives outside this repository, and
the scanner digests every 1-, 2- and 3-word window of the text it is given and
looks for a match. Without the key the list is opaque: an unkeyed hash of a
short word falls to a dictionary run in seconds, a keyed one does not.

Because the key is not here, this scanner fails closed. No key means no
commit, rather than a check that silently passes -- a gate nobody notices is
switched off is what let the three leaks through.

The key path is per-clone local config, set once alongside `core.hooksPath`:

    git config brain.leakKeyPath /path/to/the/key/file

or the `BRAIN_LEAK_KEY` environment variable, which wins if both are set.

To add a term:

    python .githooks/leak_scan.py --hash "the term in lowercase"

and paste the digest into TERM_DIGESTS. Multi-word terms are joined by single
spaces with punctuation dropped, so `Some Project V4.md` is added as the three
words `some project v4`, and a term of more than MAX_WORDS words will never
match.

Deliberately not on the list: `evergreen` and `onyx`, which are ordinary
vocabulary and the name of a real search product respectively, both used
legitimately in public notes here. Only their `.md` filename forms ever
leaked, and blocking the bare words would have cost more false positives than
it is worth.

Usage:
    leak_scan.py --staged            scan added lines of the staged diff
    leak_scan.py --message <file>    scan a commit message file
    leak_scan.py --hash <term>       print the digest of one term
    leak_scan.py --selftest          run the built-in checks, no key needed
"""

import hashlib
import hmac
import os
import re
import subprocess
import sys

# HMAC-SHA256 of each lowercased private term. See the docstring to add one.
TERM_DIGESTS = {
    "29ddcc1c909e8cbb755aac6b2d7a27eab694952cc2be3d761e7d71912375be21",
    "4730a3cff64f5fff39133e0ee379b716de51e9620f7cb6481c50569218a2187c",
    "4d9e631494da27bbf7a12ea3152db59a270124cdd5d957aa8b06df35faa6245d",
    "5036755867f017b3878e942f1e544da0d30d6ab9527537493f5ce0fdef1b1ee9",
    "5ba28ec1760de177e97c77b27c53583793db650e45b23d778ca91b6425a894cc",
    "5bb7b45ba8053836886a9f1906a6acb2d4690c5755a62fef9d8b9fc78a4e9571",
    "7fbb6420cdb0cf0d8e6a6c9e9a003ee018863ed5ccda863aa04d5679b1594cdc",
    "9183323baf1a42f31331e543ce64dc0cda83f5feef7d0b87f10b9ca271c3596a",
    "951e8919e53bb622fa64b1690c22c92034372b8ecdff322a8a4229a1b03c8ab9",
    "98f55f81118d858b98b30175497fd341b6539452bd7a32587f612e278363f542",
    "b48a1c2064e482384eb8a0fa2a04aeb65309e028c380f60e3c5e522ae80d2acd",
    "bf8aee3a6948cb5767600d1bcd300ce8904e70050041619551bc6d5b72bb7615",
    "c23df6a00ac82e2f5b25831c9ec77b19eb31169698dcefdacfc61c1476d5d5df",
    "c964d23d7ac296440839b83a46f4723c7bd61f75cd34ebabfb9db31079472c3c",
    "ca41f3f6e477e26184ac0e220629e9282ec21d19645cace370b7b465b2c8d946",
    "f0a517fddb541089a8f2614503ac180e86e21e764c04c353a953bb4faa7f4ad0",
    "fd6ab6ad8922d3ddfa402604d9e6f75ef9d8dff84d87dcd265a051a35b1d9bca",
    "fe3ca6908b0e13a07849ef2f2004a2d88b73b5665216dad07547d2e24fc71e50",
}

MAX_WORDS = 3
WORD = re.compile(r"[a-z0-9]+")

NO_KEY = """%s: the private-term key is not reachable, refusing to commit.

The term list here is keyed, and the key lives outside this public repository.
Point this clone at it, once:

    git config brain.leakKeyPath /path/to/the/key/file

or set BRAIN_LEAK_KEY to the same path. To commit without the check:

    PKM_ALLOW_LEAK_TERM=1 git commit ...
"""


SIBLING_KEY = os.path.join("..", ".brain-leak-key")


def key_path():
    """Return the key path, or None.

    Environment first, then per-clone config, then the parent directory. The
    last one covers the layout where this repository is checked out inside the
    one holding the key, so that clone needs no configuration at all; every
    other machine sets `brain.leakKeyPath` once.
    """
    env = os.environ.get("BRAIN_LEAK_KEY")
    if env:
        return env
    got = subprocess.run(
        ["git", "config", "--get", "brain.leakKeyPath"], capture_output=True
    )
    configured = got.stdout.decode().strip()
    if configured:
        return configured
    return SIBLING_KEY if os.path.exists(SIBLING_KEY) else None


def load_key():
    """Return the key bytes, or None if it is unset or unreadable."""
    path = key_path()
    if not path:
        return None
    try:
        with open(path, "rb") as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def digest(key, text):
    return hmac.new(key, text.encode(), hashlib.sha256).hexdigest()


def hits(key, text, digests=TERM_DIGESTS):
    """Return the private terms found in text, in plaintext, for local output."""
    words = WORD.findall(text.lower())
    found = []
    for size in range(1, MAX_WORDS + 1):
        for i in range(len(words) - size + 1):
            window = " ".join(words[i:i + size])
            if digest(key, window) in digests:
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
    # Probes and a throwaway key, not the real ones -- writing either here
    # would put them in the public checkout, which is what this file prevents.
    key = b"selftest key, not the real one"
    one, two = "zorbex", "quux v9"
    probes = {digest(key, t) for t in (one, two)}
    scan = lambda text: hits(key, text, probes)

    assert scan("nothing to see here") == []
    assert scan("the Zorbex vault") == [one], "case folding"
    assert scan("C:\\Users\\H\\Documents\\GitHub\\Zorbex") == [one], "windows path"
    assert scan("proj-incubator-zorbex") == [one], "hyphenated slug"
    assert scan("`quux v9.md` and `evergreen.md`") == [two], "multi-word term"
    assert scan("zorbexes") == [], "no substring matching, terms are whole words"
    assert scan("Onyx (formerly Danswer) is a search product") == []
    assert scan("an evergreen concept note") == []
    assert digest(key, one) != digest(b"a different key", one), "digest is keyed"
    print("leak_scan selftest ok")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0

    key = load_key()
    if key is None:
        print(NO_KEY % ("commit-msg" if "--message" in argv else "pre-commit"), file=sys.stderr)
        return 1

    if "--hash" in argv:
        term = argv[argv.index("--hash") + 1].lower()
        print(digest(key, " ".join(WORD.findall(term))))
        return 0

    if "--message" in argv:
        with open(argv[argv.index("--message") + 1], encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        found = hits(key, text)
        return report([("commit message", found, text.splitlines()[0])] if found else [])

    offences = []
    for path, line in staged_additions():
        found = hits(key, line)
        if found:
            offences.append((path, found, line))
    return report(offences)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
