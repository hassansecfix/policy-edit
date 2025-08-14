# Real Policy Processing Workflow

Complete workflow for processing real policy documents with automated tracked changes.

## 📁 Files Overview

- **`data/v5 Freya POL-11 Access Control.docx`** - Real policy document to customize
- **`data/secfix_questionnaire_responses_saas.xlsx`** - Customer questionnaire responses  
- **`data/updated_policy_instructions_v4.0.md`** - Updated AI prompt for CSV generation
- **`scripts/xlsx_to_csv_converter.py`** - Convert XLSX to CSV for AI processing

## 🚀 Complete Workflow

### Step 1: Convert Questionnaire to CSV

```bash
# Convert XLSX questionnaire to CSV for AI processing
python3 scripts/xlsx_to_csv_converter.py \
  data/secfix_questionnaire_responses_saas.xlsx \
  data/questionnaire_responses.csv
```

### Step 2: Generate Edits CSV with AI

1. **Give AI these inputs**:
   - `data/updated_policy_instructions_v4.0.md` (the prompt)
   - `data/questionnaire_responses.csv` (customer data)
   - `data/v5 Freya POL-11 Access Control.docx` (policy document)

2. **AI will output**:
   - Analysis summary
   - CSV file with all find/replace edits

3. **Save the CSV output** as `data/policy_edits.csv`

### Step 3: Run Automated Tracking

1. **Copy files to correct locations**:
   ```bash
   # Copy policy document to docs/
   cp "data/v5 Freya POL-11 Access Control.docx" docs/real_policy.docx
   
   # Copy generated edits CSV to edits/
   cp data/policy_edits.csv edits/real_policy_edits.csv
   ```

2. **Run GitHub Actions automation**:
   - Go to Actions → "Redline DOCX (LibreOffice headless)"
   - Click "Run workflow"
   - Fill in:
     - Input DOCX: `docs/real_policy.docx`
     - Edits CSV: `edits/real_policy_edits.csv`
     - Output DOCX: `build/customized_policy_with_tracking.docx`

### Step 4: Review and Finalize

1. **Download the result** from GitHub Actions artifacts
2. **Open in LibreOffice Writer**:
   - Go to Edit → Track Changes → Manage
   - Review each suggested change
   - Accept ✅ or reject ❌ as needed
3. **Manual steps** (if any):
   - Replace company logo
   - Final grammar/spelling check
4. **Save final version** as PDF

## 🎯 Expected Results

### What the AI Will Generate:

```csv
Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule
[Company Name],Customer Company Inc,FALSE,TRUE,FALSE,"Company name replacement",RULE_01
[Company Address],"123 Customer St, City, State",FALSE,TRUE,FALSE,"Company address replacement",RULE_02
[Version Control System],Git,FALSE,TRUE,FALSE,"Version control tool",RULE_05
[Password Manager],1Password,FALSE,TRUE,FALSE,"Password management tool",RULE_06
[Ticketing System],Jira,FALSE,TRUE,FALSE,"Ticket management system",RULE_07
[Access Request Method],Email to IT team,FALSE,TRUE,FALSE,"Access request process",RULE_07
[Review Frequency],quarterly,FALSE,TRUE,FALSE,"Access review frequency",RULE_08
[Termination Timeframe],24 hours,FALSE,TRUE,FALSE,"Account termination timeframe",RULE_09
[Policy Owner],IT Manager,FALSE,TRUE,FALSE,"Policy owner role",RULE_10
[Exception Approver],CISO,FALSE,TRUE,FALSE,"Exception approval authority",RULE_11
[Violations Reporter],HR Manager,FALSE,TRUE,FALSE,"Violations reporting contact",RULE_12
```

### What You'll Get:

- ✅ **Professional tracked changes** in the policy document
- ✅ **Accept/reject interface** for each customization
- ✅ **Automated application** of all customer-specific data
- ✅ **Audit trail** of what was changed and why
- ✅ **Time savings** - minutes instead of hours

## 🔧 Advanced Tips

### Custom Edits
Add custom find/replace rules to the CSV:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule
"old department name","new department name",FALSE,TRUE,FALSE,"Department name update",CUSTOM_01
```

### Regex Patterns
For complex replacements, use Wildcards=TRUE:
```csv
Find,Replace,MatchCase,WholeWord,Wildcards,Description,Rule
"v\d+\.\d+","v2.1",FALSE,FALSE,TRUE,"Version number update",CUSTOM_02
```

### Testing First
Always test with a small subset before processing the full document:
1. Create a test CSV with 2-3 edits
2. Run on a copy of the document
3. Verify results before full processing

## 📋 Quality Checklist

Before finalizing:
- [ ] All placeholder text replaced
- [ ] Company-specific information accurate
- [ ] Policy logic still makes sense
- [ ] Grammar and spelling correct
- [ ] Logo updated (if applicable)
- [ ] Document saved as final PDF
- [ ] Tracked changes accepted/rejected appropriately

This workflow transforms a manual, error-prone process into an automated, auditable system that saves hours of work while improving accuracy! 🎉
