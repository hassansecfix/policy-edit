# Automated Tracked Edits for DOCX

Apply find/replace edits to DOCX files with **automated tracked changes** that can be accepted or rejected in LibreOffice Writer or Microsoft Word.

## 🎯 What This Does

- ✅ **Input**: DOCX file + CSV of find/replace rules
- ✅ **Output**: DOCX with tracked changes (suggestions you can accept/reject)
- ✅ **Zero manual work** - fully automated via GitHub Actions
- ✅ **Professional results** - works exactly like manual track changes

## 🚀 How to Use

### 1. Prepare Your Files

**Input Document**: Place your DOCX file in `docs/` directory

**Edit Rules**: Create a CSV file in `edits/` directory with this format:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards
ACME,Acme,TRUE,TRUE,FALSE
Company,Corporation,FALSE,TRUE,FALSE
2023,2024,FALSE,FALSE,FALSE
```

### 2. Run Automation

1. **Go to GitHub Actions**: Click "Actions" tab in this repository
2. **Find workflow**: "Redline DOCX (LibreOffice headless)"
3. **Click "Run workflow"**
4. **Fill in paths**:
   - Input DOCX: `docs/your-file.docx`
   - Edits CSV: `edits/your-edits.csv`
   - Output DOCX: `build/output-with-changes.docx`
5. **Click "Run workflow"**

### 3. Get Results

1. **Wait 1-2 minutes** for completion
2. **Download artifact** "redlined-docx" from the workflow run
3. **Extract ZIP** to get your DOCX with automated tracked changes

### 4. Review Changes

**In LibreOffice Writer**:
1. Open the output DOCX
2. Go to **Edit → Track Changes → Manage**
3. Accept ✅ or reject ❌ each suggested change

**In Microsoft Word**:
1. Open the output DOCX
2. Go to **Review → Track Changes → All Markup**
3. Accept or reject each suggested change

## 📁 Project Structure

```
.
├── README.md                   # This file
├── RUN_AUTOMATION.md          # Detailed usage guide
├── scripts/
│   ├── apply_tracked_edits_libre.py  # Main automation script
│   └── find_replace_list_to_csv.py   # Text-to-CSV converter
├── edits/
│   ├── edits_sample.csv             # Example CSV format
│   └── edits_example.txt            # Example text format
├── docs/
│   ├── test_input.docx              # Sample input file
│   └── test_input_content.txt       # Sample content
├── build/                           # Output directory
└── .github/workflows/
    └── redline-docx.yml             # GitHub Actions workflow
```

## 📋 CSV Format

- **Find**: Text to search for
- **Replace**: Text to replace with
- **MatchCase**: TRUE/FALSE for case sensitivity
- **WholeWord**: TRUE/FALSE for whole word matching
- **Wildcards**: TRUE/FALSE for regex patterns (ICU format)

## ✨ Examples

**Simple replacement**:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards
ACME,Acme,TRUE,TRUE,FALSE
```

**Regex pattern**:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards
v1\.([0-9]+),v2.\1,FALSE,FALSE,TRUE
```

## 🎉 Result

You get a DOCX file with professional tracked changes that work exactly like manual editing in Word or LibreOffice - but created automatically from your CSV rules!

## 📖 More Help

See `RUN_AUTOMATION.md` for detailed step-by-step instructions.