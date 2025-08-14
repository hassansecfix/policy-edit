# Automated Tracked Edits for DOCX (LibreOffice Headless)

Create a zero-touch pipeline that takes a list of edits and outputs a **.docx** with **accept/rejectable suggestions** (tracked changes) — without opening Word.

This system uses **LibreOffice headless + UNO** (no Word needed) to apply find/replace operations as tracked changes that appear in Microsoft Word's Review mode.

## Features

- ✅ Cross-platform Python runner using LibreOffice headless + UNO
- ✅ Convert "Find: ... / Replace with: ..." text lists to CSV
- ✅ Apply edits as tracked changes (accept/rejectable in Word)
- ✅ Support for regex patterns, case sensitivity, whole word matching
- ✅ GitHub Actions workflow for CI/CD
- ✅ No Microsoft Word required

## How it works

1. Run LibreOffice **headless** and connect via the UNO bridge
2. Open your input `.docx` and enable **Record Changes**
3. Perform global **find/replace** using LibreOffice's `ReplaceDescriptor`
4. Each replacement becomes a **suggested change** (insertions/deletions)
5. Save the output DOCX with tracked changes that show in Microsoft Word

## Project Structure

```
.
├── README.md                      # Setup and usage instructions
├── scripts/
│   ├── apply_tracked_edits_libre.py  # Main script for applying edits
│   └── find_replace_list_to_csv.py   # Convert text format to CSV
├── edits/
│   ├── edits_sample.csv              # Sample CSV with edits
│   └── edits_example.txt             # Sample text format
├── docs/                             # Place your input DOCX files here
├── build/                            # Output directory
└── .github/
    └── workflows/
        └── redline-docx.yml          # GitHub Actions workflow
```

## Installation & Setup

### Prerequisites

1. **Install LibreOffice**

   - **macOS**: Download from [libreoffice.org](https://www.libreoffice.org/download/download/) or `brew install --cask libreoffice`
   - **Linux**: `sudo apt-get install libreoffice` (Ubuntu/Debian) or equivalent
   - **Windows**: Download installer from [libreoffice.org](https://www.libreoffice.org/download/download/)

2. **Locate LibreOffice Python**
   - **macOS**: `/Applications/LibreOffice.app/Contents/Resources/python`
   - **Linux**: `/usr/lib/libreoffice/program/python`
   - **Windows**: `"C:\Program Files\LibreOffice\program\python.exe"`

### Verify Installation

Test that LibreOffice and UNO are working:

```bash
# Test LibreOffice command line
soffice --version

# Test LibreOffice Python with UNO (replace with your path)
/Applications/LibreOffice.app/Contents/Resources/python -c "import uno; print('UNO module available')"
```

## Usage

### Quick Start

1. **Place your input DOCX file** in the `docs/` directory
2. **Prepare your edits** (see formats below)
3. **Run the pipeline**

### Edit Formats

#### Option 1: CSV Format (Direct)

Create/edit `edits/your_edits.csv`:

```csv
Find,Replace,MatchCase,WholeWord,Wildcards
ACME,Acme,TRUE,TRUE,FALSE
v1\.([0-9]+),v2.\1,FALSE,FALSE,TRUE
"old text","new text",FALSE,TRUE,FALSE
```

- `MatchCase`: TRUE/FALSE (case-sensitive matching)
- `WholeWord`: TRUE/FALSE (match whole words only)
- `Wildcards`: TRUE/FALSE (use ICU regex patterns)

#### Option 2: Text Format (Convert to CSV)

Create `edits/your_edits.txt`:

```txt
Find: [ACME]
Replace with: [Acme]

Find: [v1\.([0-9]+)]
Replace with: [v2.\1]

Find: [old text]
Replace with: [new text]
```

Convert to CSV:

```bash
# macOS
/Applications/LibreOffice.app/Contents/Resources/python scripts/find_replace_list_to_csv.py edits/your_edits.txt edits/your_edits.csv

# Linux
/usr/lib/libreoffice/program/python scripts/find_replace_list_to_csv.py edits/your_edits.txt edits/your_edits.csv
```

### Running the Pipeline

```bash
# macOS
/Applications/LibreOffice.app/Contents/Resources/python scripts/apply_tracked_edits_libre.py \
  --in docs/your_document.docx \
  --csv edits/your_edits.csv \
  --out build/output_with_tracked_changes.docx \
  --launch

# Linux
/usr/lib/libreoffice/program/python scripts/apply_tracked_edits_libre.py \
  --in docs/your_document.docx \
  --csv edits/your_edits.csv \
  --out build/output_with_tracked_changes.docx \
  --launch

# Windows
"C:\Program Files\LibreOffice\program\python.exe" scripts/apply_tracked_edits_libre.py \
  --in docs/your_document.docx \
  --csv edits/your_edits.csv \
  --out build/output_with_tracked_changes.docx \
  --launch
```

### Arguments

- `--in`: Input DOCX file path
- `--csv`: CSV file with Find/Replace rules
- `--out`: Output DOCX file path (will be overwritten)
- `--launch`: Automatically start LibreOffice headless listener

## Testing

### Test with Sample Data

1. **Create a test document** (`docs/test_input.docx`) with this content:

   ```
   Welcome to ACME Corporation!

   This document describes our Company policies for version v1.5 of the software.

   The foo bar feature is now deprecated in 2023.
   ```

2. **Run with sample edits**:

   ```bash
   # macOS
   /Applications/LibreOffice.app/Contents/Resources/python scripts/apply_tracked_edits_libre.py \
     --in docs/test_input.docx \
     --csv edits/edits_sample.csv \
     --out build/test_output.docx \
     --launch
   ```

3. **Expected results** in `build/test_output.docx`:

   - "ACME" → "Acme" (tracked change)
   - "Company" → "Corporation" (tracked change)
   - "v1.5" → "v2.5" (regex replacement, tracked change)
   - "foo bar" → "foobar" (tracked change)
   - "2023" → "2024" (tracked change)

4. **Verify in Microsoft Word**:
   - Open `build/test_output.docx` in Word
   - Go to **Review** → **All Markup** to see tracked changes
   - Each replacement should appear as an accept/reject suggestion

### Test the Converter

```bash
# Convert text format to CSV
/Applications/LibreOffice.app/Contents/Resources/python scripts/find_replace_list_to_csv.py \
  edits/edits_example.txt \
  edits/converted_edits.csv

# Verify the output
cat edits/converted_edits.csv
```

### Troubleshooting

#### LibreOffice not found

```
ERROR: 'soffice' not found on PATH
```

**Solution**: Add LibreOffice to your PATH or use full path to soffice:

- **macOS**: `export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"`
- **Linux**: Usually already in PATH after installation

#### UNO module not available

```
ERROR: UNO bridge not available
```

**Solution**: Use LibreOffice's bundled Python instead of system Python:

```bash
# Instead of: python scripts/apply_tracked_edits_libre.py
# Use: /Applications/LibreOffice.app/Contents/Resources/python scripts/apply_tracked_edits_libre.py
```

#### Cannot connect to LibreOffice listener

```
Could not connect to LibreOffice listener
```

**Solution**:

1. Make sure to use `--launch` flag
2. Or manually start LibreOffice listener:
   ```bash
   soffice --headless --nologo --nodefault \
     --accept='socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager' &
   ```

#### No tracked changes visible in Word

**Solution**: In Microsoft Word, go to **Review** → **Track Changes** → **All Markup**

## Advanced Usage

### Regex Patterns

Set `Wildcards=TRUE` to use ICU regex:

```csv
Find,Replace,MatchCase,WholeWord,Wildcards
\b[Vv]ersion\s+(\d+)\.(\d+),Version \1.\2,FALSE,FALSE,TRUE
\n\n+,\n\n,FALSE,FALSE,TRUE
```

### Custom CSV Columns

The CSV parser is flexible with column names:

- `Find`/`find`/`FIND`
- `Replace`/`replace`/`REPLACE`
- `MatchCase`/`matchcase`/`MATCHCASE`
- `WholeWord`/`wholeword`/`WHOLEWORD`
- `Wildcards`/`wildcards`/`WILDCARDS`

### Headers and Footers (TODO)

Current implementation processes the main document body. To extend for headers/footers:

1. Iterate through page styles
2. Access `HeaderText`/`FooterText` properties
3. Apply `replaceAll` to those text ranges
4. Add `--include-stories` flag (future enhancement)

## CI/CD with GitHub Actions

The included workflow (`/.github/workflows/redline-docx.yml`) allows you to run the pipeline in GitHub Actions:

1. **Trigger**: Go to Actions → "Redline DOCX (LibreOffice headless)" → "Run workflow"
2. **Parameters**:
   - Input DOCX path (e.g., `docs/input.docx`)
   - Edits CSV path (e.g., `edits/edits_sample.csv`)
   - Output DOCX path (e.g., `build/output.docx`)
3. **Result**: Download the processed DOCX from workflow artifacts

## Tips

1. **Always backup** your original documents
2. **Test with sample data** before processing important documents
3. **Use regex carefully** - test patterns with `Wildcards=TRUE`
4. **Review tracked changes** in Word after processing
5. **For large documents**, consider chunking your edits into multiple CSV files

## License

MIT License - see project for details.

## Support

- 📋 **Issues**: Open an issue for bugs or feature requests
- 📖 **Documentation**: LibreOffice UNO API documentation
- 💡 **Regex**: ICU Regular Expression syntax for `Wildcards=TRUE`
