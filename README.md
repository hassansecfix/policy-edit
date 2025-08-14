# Automated Tracked Edits for DOCX

Apply find/replace edits to DOCX files with **automated tracked changes** that can be accepted or rejected in LibreOffice Writer or Microsoft Word.

## 🎯 What This Does

- ✅ **Input**: DOCX file + CSV of find/replace rules
- ✅ **Output**: DOCX with tracked changes (suggestions you can accept/reject)
- ✅ **Zero manual work** - fully automated via GitHub Actions
- ✅ **Professional results** - works exactly like manual track changes
- ✅ **AI-powered policy customization** - from questionnaire to tracked changes

## 🚀 Two Ways to Use This System

### Option A: Basic Usage (Any Document)

For any DOCX document with simple find/replace needs.

#### 1. Prepare Your Files
**Input Document**: Place your DOCX file in `docs/` directory

**Edit Rules**: Create a CSV file in `edits/` directory with this format:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards
ACME,Acme,TRUE,TRUE,FALSE
Company,Corporation,FALSE,TRUE,FALSE
2023,2024,FALSE,FALSE,FALSE
```

#### 2. Run Automation
1. **Go to GitHub Actions**: Click "Actions" tab in this repository
2. **Find workflow**: "Redline DOCX (LibreOffice headless)"
3. **Click "Run workflow"**
4. **Fill in paths** and click "Run workflow"

### Option B: AI-Powered Policy Processing (Advanced)

For policy documents with questionnaire data - fully automated from customer responses to tracked changes.

#### 1. Convert Questionnaire Data
```bash
# Convert Excel questionnaire to CSV for AI processing
python3 scripts/xlsx_to_csv_converter.py \
  data/your_questionnaire.xlsx \
  data/questionnaire_responses.csv
```

#### 2. Generate Edits with AI
- **Give AI these inputs**:
  - `data/updated_policy_instructions_v4.0.md` (AI prompt)
  - `data/questionnaire_responses.csv` (customer data)
  - Your policy DOCX file
- **AI outputs**: Ready-to-use CSV with all policy customizations
- **Save result** as `edits/policy_edits.csv`

#### 3. Apply Automated Tracking
Run the same GitHub Actions workflow with your generated CSV!

## 📁 Project Structure

```
.
├── README.md                           # This file
├── RUN_AUTOMATION.md                  # Basic usage guide
├── REAL_POLICY_WORKFLOW.md            # Advanced policy processing guide
├── scripts/
│   ├── apply_tracked_edits_libre.py       # Main automation script
│   ├── find_replace_list_to_csv.py        # Text-to-CSV converter
│   └── xlsx_to_csv_converter.py           # Excel-to-CSV converter
├── edits/
│   ├── edits_sample.csv                   # Example CSV format
│   └── edits_example.txt                  # Example text format
├── docs/
│   ├── test_input.docx                    # Sample input file
│   └── test_input_content.txt             # Sample content
├── data/                                  # Real policy processing files
│   ├── updated_policy_instructions_v4.0.md    # AI prompt for policy processing
│   ├── v5 Freya POL-11 Access Control.docx    # Real policy document
│   ├── secfix_questionnaire_responses_saas.xlsx # Sample questionnaire
│   └── questionnaire_responses.csv            # Converted questionnaire data
├── build/                                 # Output directory
└── .github/workflows/
    └── redline-docx.yml                   # GitHub Actions workflow
```

## 📋 CSV Format Reference

### Basic Format
- **Find**: Text to search for
- **Replace**: Text to replace with
- **MatchCase**: TRUE/FALSE for case sensitivity
- **WholeWord**: TRUE/FALSE for whole word matching
- **Wildcards**: TRUE/FALSE for regex patterns (ICU format)

### Extended Format (AI-Generated)
```csv
Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule
[Company Name],Acme Corp,FALSE,TRUE,FALSE,"Company name replacement",RULE_01
[Policy Owner],IT Manager,FALSE,TRUE,FALSE,"Policy owner role",RULE_10
```

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

**AI-generated policy customization**:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule
[Company Name],Secfix GmbH,FALSE,TRUE,FALSE,"Company name replacement",RULE_01
[Company Address],"Salvatorplatz 3, 80333 München",FALSE,TRUE,FALSE,"Company address replacement",RULE_02
[Version Control System],GitLab,FALSE,TRUE,FALSE,"Version control tool",RULE_05
[Password Manager],1Password,FALSE,TRUE,FALSE,"Password management tool",RULE_06
```

## 🎉 Results

### What You Get
1. **Download the result** from GitHub Actions artifacts
2. **Open in LibreOffice Writer**:
   - Go to Edit → Track Changes → Manage
   - Review each suggested change
   - Accept ✅ or reject ❌ as needed
3. **Professional tracked changes** that work exactly like manual editing

### Expected Results
- ✅ **Professional tracked changes** in policy documents
- ✅ **Accept/reject interface** for each customization  
- ✅ **Automated application** of customer-specific data
- ✅ **Audit trail** of what was changed and why
- ✅ **Time savings** - minutes instead of hours

## 📖 Detailed Guides

- **Basic Usage**: See `RUN_AUTOMATION.md` for step-by-step instructions
- **Policy Processing**: See `REAL_POLICY_WORKFLOW.md` for AI-powered workflow
- **Technical Details**: Check the scripts and workflow files

## 🔧 Requirements

- GitHub repository with Actions enabled
- LibreOffice Writer (for viewing results)
- Python 3 + pandas + openpyxl (for Excel conversion)

This system transforms manual document customization into an automated, auditable process that saves hours of work while improving accuracy! 🎉