#!/usr/bin/env python3
"""
Convert a plain text list like:

Find: [foo]
Replace with: [bar]

Find: [baz]
Replace with: [qux]

...into edits.csv suitable for apply_tracked_edits_libre.py

Usage:
  python scripts/find_replace_list_to_csv.py edits/edits_example.txt edits/edits.csv
"""
import sys, csv

def strip_brackets(s: str) -> str:
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        return s[1:-1]
    return s

def main():
    if len(sys.argv) < 3:
        print("Usage: python find_replace_list_to_csv.py INPUT.txt OUTPUT.csv")
        sys.exit(2)

    inp, outp = sys.argv[1], sys.argv[2]
    with open(inp, "r", encoding="utf-8") as f:
        lines = [l.rstrip("\r\n") for l in f]

    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.lower().startswith("find:"):
            find_text = strip_brackets(line.split(":",1)[1])
            # find the next non-empty line for "Replace with:"
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].lower().startswith("replace with:"):
                repl_text = strip_brackets(lines[j].split(":",1)[1])
                pairs.append((find_text, repl_text))
                i = j + 1
                continue
        i += 1

    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Find", "Replace", "MatchCase", "WholeWord", "Wildcards"])
        for ftxt, rtxt in pairs:
            w.writerow([ftxt, rtxt, "", "", ""])

    print(f"Wrote {len(pairs)} pairs to {outp}")

if __name__ == "__main__":
    main()
