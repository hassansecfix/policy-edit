# Automated Tracked Edits for DOCX (LibreOffice Headless)

Create a zero-touch pipeline that takes a list of edits and outputs a **.docx** with **accept/rejectable suggestions** (tracked changes) — without opening Word.

This spec tells Cursor to generate all files. It includes:

- A cross-platform Python runner using **LibreOffice headless + UNO** (no Word needed)
- A converter for your “**Find:** … / **Replace with:** …” text lists → CSV
- Sample data and a GitHub Actions workflow

---

## How it works (high level)

- We run LibreOffice **headless** and connect via the UNO bridge.
- The script opens your input `.docx`, enables **Record Changes**, and performs global **find/replace** using a `ReplaceDescriptor`.
- Each replacement becomes a **suggested change** (insertions/deletions) that will show in Microsoft Word under **Review** → **Accept/Reject**.

> Note: LibreOffice’s replace API operates on the main body by default. If you need headers/footers/comments too, see the TODO notes inside the script (it can be extended later to traverse those containers explicitly).

---

## Project structure

```
.
├── README.md                      # (this file)
├── scripts/
│   ├── apply_tracked_edits_libre.py
│   └── find_replace_list_to_csv.py
├── edits/
│   ├── edits_sample.csv
│   └── edits_example.txt
└── .github/
    └── workflows/
        └── redline-docx.yml
```

---

## Requirements

- **LibreOffice** installed (provides `soffice` and the UNO bridge).
- Use **LibreOffice’s Python** to ensure the `uno` module is available:

  - macOS: `/Applications/LibreOffice.app/Contents/Resources/python`
  - Linux: `/usr/lib/libreoffice/program/python` (or similar)
  - Windows: `C:\Program Files\LibreOffice\program\python.exe`

You can also try system Python if `pyuno` is installed, but the bundled Python is the simplest.

---

## Usage

```bash
# Convert your "Find:/Replace with:" text list to CSV (if needed)
# (or provide your own CSV directly)
<path-to-lo-python> scripts/find_replace_list_to_csv.py edits/edits_example.txt edits/edits.csv

# Run the headless redline job (auto-launches a headless LibreOffice listener)
<path-to-lo-python> scripts/apply_tracked_edits_libre.py \
  --in path/to/input.docx \
  --csv edits/edits.csv \
  --out path/to/output.docx \
  --launch
```

**CSV format** (`edits/*.csv`):

```
Find,Replace,MatchCase,WholeWord,Wildcards
ACME,Acme,TRUE,TRUE,FALSE
v1\.([0-9]+),v2.\1,FALSE,FALSE,TRUE
"foo bar","foobar",FALSE,TRUE,FALSE
```

- `Wildcards=TRUE` → **ICU regex** (standard regex) in LibreOffice.
- `WholeWord`/`MatchCase` behave as expected.

---

## Files

### File: `scripts/apply_tracked_edits_libre.py`

```python
#!/usr/bin/env python3
"""
Apply Find/Replace edits to a DOCX using LibreOffice in headless mode,
recording each change as a tracked change (accept/rejectable).

Run with LibreOffice's bundled Python so the 'uno' module is available, e.g.:
  macOS : /Applications/LibreOffice.app/Contents/Resources/python
  Linux : /usr/lib/libreoffice/program/python
  Win   : "C:\\Program Files\\LibreOffice\\program\\python.exe"

Usage:
  python apply_tracked_edits_libre.py --in input.docx --csv edits.csv --out output.docx [--launch]

Flags:
  --launch  : try to start a headless LibreOffice listener automatically
              (socket: 127.0.0.1:2002, urp)

CSV columns (header optional, but recommended):
  Find,Replace,MatchCase,WholeWord,Wildcards
  - Booleans: TRUE/FALSE, Yes/No, 1/0
  - Wildcards uses ICU regex (standard regex).
"""
import argparse
import csv
import os
import sys
import time
import subprocess
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Apply tracked edits to DOCX via LibreOffice (headless UNO).")
    p.add_argument("--in", dest="in_path", required=True, help="Input .docx")
    p.add_argument("--csv", dest="csv_path", required=True, help="CSV with columns: Find,Replace,MatchCase,WholeWord,Wildcards")
    p.add_argument("--out", dest="out_path", required=True, help="Output .docx (will be overwritten)")
    p.add_argument("--launch", action="store_true", help="Launch a headless LibreOffice UNO listener if not already running")
    return p.parse_args()

def bool_from_str(s, default=False):
    if s is None: return default
    s = str(s).strip().lower()
    return s in ("1","true","yes","y")

def rows_from_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) < 2:
            # No header: assume simple CSV
            f.seek(0)
            reader2 = csv.reader(f)
            for row in reader2:
                if not row: continue
                yield {
                    "Find": row[0],
                    "Replace": row[1] if len(row) > 1 else "",
                    "MatchCase": row[2] if len(row) > 2 else "",
                    "WholeWord": row[3] if len(row) > 3 else "",
                    "Wildcards": row[4] if len(row) > 4 else "",
                }
        else:
            for rec in reader:
                yield {
                    "Find": (rec.get("Find") or rec.get("find") or rec.get("FIND") or "").strip(),
                    "Replace": rec.get("Replace") or rec.get("replace") or rec.get("REPLACE") or "",
                    "MatchCase": rec.get("MatchCase") or rec.get("matchcase") or rec.get("MATCHCASE") or "",
                    "WholeWord": rec.get("WholeWord") or rec.get("wholeword") or rec.get("WHOLEWORD") or "",
                    "Wildcards": rec.get("Wildcards") or rec.get("wildcards") or rec.get("WILDCARDS") or "",
                }

def ensure_listener():
    # Start a headless LibreOffice UNO listener on port 2002 if not already running.
    # Harmless if one is already up.
    try:
        subprocess.Popen([
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            '--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    except FileNotFoundError:
        print("ERROR: 'soffice' not found on PATH. Install LibreOffice or add it to PATH.", file=sys.stderr)

def main():
    args = parse_args()
    in_path = os.path.abspath(args.in_path)
    out_path = os.path.abspath(args.out_path)
    csv_path = os.path.abspath(args.csv_path)

    if not os.path.exists(in_path):
        print("Input DOCX not found:", in_path, file=sys.stderr); sys.exit(2)
    if not os.path.exists(csv_path):
        print("CSV not found:", csv_path, file=sys.stderr); sys.exit(2)

    if args.launch:
        ensure_listener()

    try:
        import uno
        from com.sun.star.beans import PropertyValue
    except Exception:
        print("ERROR: UNO bridge not available. Run with LibreOffice's Python (recommended).", file=sys.stderr)
        sys.exit(1)

    # Connect to running LibreOffice
    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_ctx)
    try:
        ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
    except Exception:
        print("Could not connect to LibreOffice listener. Start it with --launch or externally.", file=sys.stderr)
        sys.exit(1)

    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    def mkprop(name, value):
        p = PropertyValue()
        p.Name = name
        p.Value = value
        return p

    def to_url(path):
        return Path(path).absolute().as_uri()

    # Load hidden
    in_props = (mkprop("Hidden", True),)
    doc = desktop.loadComponentFromURL(to_url(in_path), "_blank", 0, in_props)

    # Ensure Track Changes on
    try:
        # For Writer documents this should be available:
        doc.RecordChanges = True
    except Exception:
        pass

    # Apply replacements (main body). Extend for headers/footers if needed (see TODO).
    try:
        for row in rows_from_csv(csv_path):
            find = (row.get("Find") or "").strip()
            repl = (row.get("Replace") or "")
            if not find:
                continue
            match_case = bool_from_str(row.get("MatchCase"))
            whole_word = bool_from_str(row.get("WholeWord"))
            wildcards  = bool_from_str(row.get("Wildcards"))

            rd = doc.createReplaceDescriptor()
            rd.SearchString = find
            rd.ReplaceString = repl
            rd.SearchCaseSensitive = match_case
            rd.SearchWords = whole_word
            # Use ICU regex if requested
            try:
                rd.setPropertyValue("RegularExpressions", bool(wildcards))
            except Exception:
                pass

            doc.replaceAll(rd)
    finally:
        # Save as DOCX (Word 2007+ XML)
        out_props = (mkprop("FilterName", "MS Word 2007 XML"),)
        doc.storeToURL(to_url(out_path), out_props)
        doc.close(True)

    print("Done. Wrote:", out_path)

if __name__ == "__main__":
    main()
```

**Notes / TODOs inside the script**

- To also scan headers/footers, you’d iterate page styles and their `HeaderText`/`FooterText` ranges and call `replaceAll` with the same descriptor on those text objects. Add a `--include-stories` flag if/when needed.

---

### File: `scripts/find_replace_list_to_csv.py`

```python
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
```

---

### File: `edits/edits_sample.csv`

```csv
Find,Replace,MatchCase,WholeWord,Wildcards
ACME,Acme,TRUE,TRUE,FALSE
v1\.([0-9]+),v2.\1,FALSE,FALSE,TRUE
"foo bar","foobar",FALSE,TRUE,FALSE
```

---

### File: `edits/edits_example.txt`

```txt
Find: [ACME]
Replace with: [Acme]

Find: [v1\.([0-9]+)]
Replace with: [v2.\1]

Find: ["foo bar"]
Replace with: ["foobar"]
```

---

### File: `.github/workflows/redline-docx.yml`

```yaml
name: Redline DOCX (LibreOffice headless)

on:
  workflow_dispatch:
    inputs:
      input_docx:
        description: 'Path to input .docx'
        required: true
        default: 'docs/input.docx'
      edits_csv:
        description: 'Path to edits CSV'
        required: true
        default: 'edits/edits_sample.csv'
      output_docx:
        description: 'Path to output .docx'
        required: true
        default: 'build/output.docx'

jobs:
  redline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install LibreOffice
        run: sudo apt-get update && sudo apt-get install -y libreoffice

      # Use the LibreOffice-bundled Python to guarantee 'uno' availability
      - name: Find LibreOffice Python
        id: lo_py
        run: |
          set -e
          LO_PY="/usr/lib/libreoffice/program/python"
          if [ ! -x "$LO_PY" ]; then
            echo "LibreOffice Python not found at $LO_PY" >&2
            exit 1
          fi
          echo "path=$LO_PY" >> $GITHUB_OUTPUT

      - name: Run redline job
        env:
          LO_PY: ${{ steps.lo_py.outputs.path }}
        run: |
          mkdir -p build
          "$LO_PY" scripts/apply_tracked_edits_libre.py \
            --in "${{ github.event.inputs.input_docx }}" \
            --csv "${{ github.event.inputs.edits_csv }}" \
            --out "${{ github.event.inputs.output_docx }}" \
            --launch

      - name: Upload output
        uses: actions/upload-artifact@v4
        with:
          name: redlined-docx
          path: ${{ github.event.inputs.output_docx }}
```

---

## Tips & caveats

- If you don’t see redlines in Word, switch **Review → All Markup**.
- ICU regex examples:

  - Replace version prefix: `Find: v1\.([0-9]+)` → `Replace: v2.\1`
  - Paragraph break = `\n`, tab = `\t`

- To extend to headers/footers/comments:

  - Iterate page styles: access each style’s `HeaderText`/`FooterText` and run `replaceAll` with the same descriptor.
  - Similar for footnotes/endnotes via their respective text fields/collections.

---

## Done

Run the commands under **Usage**, commit the output, or wire into CI with the provided workflow.
