# Tau

Tau is a small, deliberately unusual programming language. Programs work directly on **memory cells of fixed size**
and a handful of registers, instead of variables and types. This repository is the **reference implementation in
Python** (`tau.py`). A faster C++ implementation with a Windows IDE lives in its own repository, **Tau++**.

Current version: **0.2**. Requires Python 3.9 or newer. Released under the MIT License (see `LICENSE`).

```
python3 tau.py hello.tau
```

## Hello world

```
tau
Define tau 0x01 "01001000 01100101 01101100 01101100 01101111 00100000 01010111 01101111 01110010 01101100 01100100 00100001"
Ta
Define Ta 0x02 "00000000"
```

`Define` writes raw bytes (as 8-bit groups) into the cell at an address. A program made only of `Define`/`Text`
lines prints its `Tau` cells as text when it ends, so this prints `Hello World!`.

## Memory

Memory is a set of **cells** at numeric addresses. Every cell has a type that fixes its size:

| Type | Size |
|------|------|
| `T`   | 1 byte |
| `Ta`  | 50 bytes |
| `Tau` | 100 bytes |

Writing shorter data into a cell pads it with zero bytes. Data longer than the cell is an error. Defining an
address again replaces the cell. There are also sixteen signed 32-bit registers, `r0` to `r15` (arithmetic wraps
around on overflow).

## Values

A *value* is a register (`r3`), a number (`10`, `0x1F`, `0b101`, `-4`) or a character (`'a'`, `'\n'`).
Addresses are values too.

## Statements

One statement per line. `#` starts a comment. Statement and type names are not case-sensitive.

| Statement | What it does |
|---|---|
| `Define <T\|Ta\|Tau> <addr> "<bits>"` | Write bytes given as 8-bit binary groups |
| `Text <T\|Ta\|Tau> <addr> "<text>"` | Write text (escapes `\n \t \r \0 \\ \" \xHH`) |
| `Set` / `Add` / `Sub` / `Mul` / `Div` / `Mod` `rD <v>` | Arithmetic on a register (`Div` and `Mod` truncate toward zero) |
| `Load rD <addr> <idx>` | `rD` = byte number `idx` of the cell at `addr` |
| `Store <addr> <idx> <v>` | Set byte `idx` of the cell at `addr` to `v & 255` |
| `Len rD <addr>` | `rD` = number of bytes before the first zero byte of the cell |
| `name:` | A label |
| `Jump L` | Go to label `L` |
| `Jeq` / `Jne` / `Jlt` / `Jgt` / `Jle` / `Jge` `<v> <v> L` | Go to `L` if the comparison holds |
| `Call L` / `Ret` | Subroutines (up to 256 deep) |
| `Halt` | Stop |
| `Print <addr>` | Print the cell as text, up to its first zero byte |
| `PrintChar <v>` / `PrintInt <v>` / `Newline` | Print a character, a number, a line break |
| `Host <function> <args...>` | Call a function of the program that embeds Tau |
| `tau`, `ta`, `t` on a line alone | Section header, no effect |

Loading, storing or printing from an address that has no cell is an error, as is an index outside the cell.
Errors stop the program and name the line: `Tau error: line 2: index 5 outside T cell`.

## Host functions

When Tau runs inside another program (Tau++'s IDE, or `tau.py --text file`) the program can read the document that
host provides. Each takes registers or values and returns its result in the first register:

| Call | Result |
|---|---|
| `Host TextLen rD` | length of the document |
| `Host CharAt rD <idx>` | character code at `idx`, or 0 outside the document |
| `Host CaretLine rD` / `Host CaretCol rD` | caret position (1-based) |
| `Host LineCount rD` | number of lines |
| `Host Paint <start> <len> <colour>` | colour a range (on the command line this prints `paint start len colour`) |

## Examples

| File | Shows |
|---|---|
| `examples/fact.tau` | loops and arithmetic (10!) |
| `examples/fizzbuzz.tau` | text cells, `Mod`, jumps |
| `examples/reverse.tau` | `Len`, `Load`, `Store` |
| `examples/calls.tau` | `Call` and `Ret` |
| `examples/math.tau` | signed division, overflow, character values |
| `examples/badindex.tau` | the error message for a bad index |

## textstats: a real tool written in Tau

`tools/textstats.tau` analyses a text file: lines, words, characters, letters, digits, empty lines, the longest
line, and a bar chart of how often each letter appears.

```
python3 tau.py tools/textstats.tau --text notes.txt
cat notes.txt | python3 tau.py tools/textstats.tau --text -
```

`programs/wc.tau` is a smaller counter in the style of `wc`.

## Command line

```
python3 tau.py program.tau [--text file|-] [--caret N] [--steps N]
```

- `--text file` gives the program a document to read through the `Host` functions (`-` reads standard input).
- `--caret N` sets the caret position that `Host CaretLine` and `Host CaretCol` report.
- `--steps N` sets the step limit (default 5 million, or 50 million when `--text` is used).

## Tests

```
python3 tests/run_tests.py
```

The Tau++ repository runs its own tests that check its C++ implementation against this one.
