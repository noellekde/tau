#!/usr/bin/env python3
"""Self-tests for tau.py.  Run from anywhere:  python3 tests/run_tests.py"""
import glob
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = os.path.join(ROOT, "tau.py")
failures = 0


def tau(args, stdin=b""):
    p = subprocess.run([sys.executable, "-I", TAU] + args, input=stdin, capture_output=True)
    return p.returncode, p.stdout.decode("latin-1"), p.stderr.decode("latin-1")


def report(name, ok, detail=""):
    global failures
    print(("ok    " if ok else "FAIL  ") + name)
    if not ok:
        failures += 1
        if detail:
            print("   ", detail)


def expect_output(name, args, expected, stdin=b""):
    code, out, err = tau(args, stdin)
    report(name, code == 0 and out == expected and err == "", f"exit={code} stdout={out!r} stderr={err!r}")


def expect_error(name, source, fragment, extra=()):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.tau")
        with open(path, "w") as f:
            f.write(source)
        code, out, err = tau([path] + list(extra))
    report(name, code == 1 and fragment in err, f"exit={code} stderr={err!r}")


# ---- the example programs --------------------------------------------------------
EXAMPLES = {
    "hello.tau": "Hello World!\n",
    "examples/fact.tau": "3628800\n",
    "examples/reverse.tau": "skcor ++uaT\n",
    "examples/math.tau": "-3 -1 -2147483648 970\n",
    "examples/calls.tau": "".join(f"square of {n} is {n * n}!\n" for n in range(1, 6)),
    "examples/fizzbuzz.tau": "".join(
        ("FizzBuzz" if n % 15 == 0 else "Fizz" if n % 3 == 0 else "Buzz" if n % 5 == 0 else str(n)) + "\n"
        for n in range(1, 16)
    ),
}
for rel, expected in EXAMPLES.items():
    expect_output(rel, [os.path.join(ROOT, rel)], expected)

code, out, err = tau([os.path.join(ROOT, "examples", "badindex.tau")])
report("examples/badindex.tau", code == 1 and out == "" and err == "Tau error: line 2: index 5 outside T cell\n",
       f"exit={code} stdout={out!r} stderr={err!r}")

known = set(EXAMPLES) | {"examples/badindex.tau"}
found = {os.path.relpath(p, ROOT).replace(os.sep, "/") for p in glob.glob(os.path.join(ROOT, "examples", "*.tau"))}
found.add("hello.tau")
report("every example has a test", found == known, f"untested: {sorted(found - known)}")


# ---- text tools -----------------------------------------------------------------
def wc_expected(data):
    text = data.decode("latin-1")
    rows = text.split("\n")
    if rows and rows[-1] == "":
        rows.pop()
    longest = max(len(r.rstrip("\r")) for r in rows)
    blank = sum(1 for r in rows if not r.strip())
    return "lines:   %d\nwords:   %d\nchars:   %d\nlongest: %d\nblank:   %d\n" % (
        len(rows), len(text.split()), len(text), longest, blank)


def textstats_expected(data):
    """Independent re-implementation of what tools/textstats.tau should print."""
    text = data.decode("latin-1")
    lens = [len(x.replace("\r", "")) for x in text.split("\n")]
    done, last = lens[:-1], lens[-1]
    rows = [("lines", len(done) + (1 if last > 0 else 0)),
            ("words", len(re.findall(r"[^ \t\r\n]+", text))),
            ("characters", len(data)),
            ("letters", len(re.findall(r"[A-Za-z]", text))),
            ("digits", len(re.findall(r"[0-9]", text))),
            ("empty lines", sum(1 for x in done if x == 0)),
            ("longest line", max(lens))]
    out = [f"{label:<14}{n:>8}\n" for label, n in rows]
    counts = [len(re.findall(chr(97 + i), text, re.I)) for i in range(26)]
    top = max(counts)
    if top:
        out.append("\nletter frequency\n")
        out += [f"{chr(97 + i)} | {'#' * max(1, c * 40 // top)} {c}\n" for i, c in enumerate(counts) if c]
    return "".join(out)


wc_file = os.path.join(ROOT, "tests", "wc_input.txt")
expect_output("programs/wc.tau", [os.path.join(ROOT, "programs", "wc.tau"), "--text", wc_file],
              wc_expected(open(wc_file, "rb").read()))

stats = os.path.join(ROOT, "tools", "textstats.tau")
for rel in ["tests/textstats_sample.txt", "tests/wc_input.txt", "README.md", "tau.py"]:
    path = os.path.join(ROOT, rel)
    expect_output("tools/textstats.tau on " + rel, [stats, "--text", path], textstats_expected(open(path, "rb").read()))

sample = open(os.path.join(ROOT, "tests", "textstats_sample.txt"), "rb").read()
expect_output("tools/textstats.tau reading stdin", [stats, "--text", "-"], textstats_expected(sample), stdin=sample)
expect_output("tools/textstats.tau on an empty document", [stats, "--text", "-"], textstats_expected(b""), stdin=b"")

# ---- language rules ---------------------------------------------------------------
expect_error("undefined label", "Jump nowhere\n", "line 1: undefined label 'nowhere'")
expect_error("unknown statement", "Frobnicate r0\n", "line 1: unknown statement 'Frobnicate'")
expect_error("data too long for its cell", 'Text t 1 "ab"\n', "does not fit in T")
expect_error("bad binary group", 'Define Tau 1 "0101"\n', "not an 8-bit binary group")
expect_error("division by zero", "Set r0 1\nDiv r0 0\n", "line 2: division by zero")
expect_error("step limit", "again:\nJump again\n", "line 2: step limit exceeded", ["--steps", "100"])
expect_error("no cell at address", "Print 7\n", "line 1: no cell at address 7")
expect_error("ret without call", "Ret\n", "line 1: ret without call")
expect_error("duplicate label", "a:\na:\n", "duplicate label 'a'")
expect_error("host function without a host", "Host TextLen r0\n", "no host function 'textlen'")

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "t.tau")
    with open(p, "w") as f:
        f.write("Set r0 -7\nDiv r0 2\nPrintInt r0\nNewline\nSet r1 0x7FFFFFFF\nAdd r1 1\nPrintInt r1\nNewline\n")
    expect_output("division truncates toward zero, 32-bit wraparound", [p], "-3\n-2147483648\n")

print("\nall good" if not failures else f"\n{failures} failure(s)")
sys.exit(1 if failures else 0)
