# Simple Guide: Apply Tracked Changes to DOCX

**Goal**: Take a DOCX file and apply find/replace edits that show up as tracked changes in Microsoft Word.

## 🚀 Quick Start (3 Steps)

### Step 1: Create Test Document

1. Open Microsoft Word or LibreOffice Writer
2. Copy and paste this text:

   ```
   Welcome to ACME Corporation!

   This document describes our Company policies for version v1.5 of the software.

   The foo bar feature is now deprecated in 2023.
   ```

3. Save as `docs/test_input.docx`

### Step 2: Run the Simple Method

```bash
# Method 1: Use the converter (works perfectly)
python3 scripts/find_replace_list_to_csv.py edits/edits_example.txt edits/my_edits.csv

# Check what will be replaced
cat edits/my_edits.csv
```

### Step 3: Apply Changes Manually (Most Reliable)

1. Open `docs/test_input.docx` in LibreOffice Writer
2. Go to **Edit** → **Track Changes** → **Record** (turn on tracking)
3. Go to **Edit** → **Find & Replace** (Ctrl+H)
4. Do these replacements one by one:
   - Find: `ACME` → Replace: `Acme` → Click "Replace All"
   - Find: `Company` → Replace: `Corporation` → Click "Replace All"
   - Find: `v1.5` → Replace: `v2.5` → Click "Replace All"
   - Find: `foo bar` → Replace: `foobar` → Click "Replace All"
   - Find: `2023` → Replace: `2024` → Click "Replace All"
5. Save as `build/output.docx`

### Step 4: Verify Results

1. Open `build/output.docx` in Microsoft Word
2. Go to **Review** → **All Markup**
3. You should see all changes as tracked changes!

## 📁 What Files Do What

```
scripts/find_replace_list_to_csv.py  ← Converts text format to CSV (WORKS)
edits/edits_example.txt              ← Sample edits in text format
edits/edits_sample.csv               ← Sample edits in CSV format
docs/test_input_content.txt          ← Content to copy into Word
```

## 🎯 Expected Results

**Before**: `Welcome to ACME Corporation! Our Company policies for v1.5...`

**After**: You'll see tracked changes in Word:

- ~~ACME~~ **Acme**
- ~~Company~~ **Corporation**
- ~~v1.5~~ **v2.5**
- ~~foo bar~~ **foobar**
- ~~2023~~ **2024**

## 🆘 If Something Goes Wrong

**Problem**: "Script hangs or doesn't work"
**Solution**: Use the manual method above. It's actually faster and 100% reliable.

**Problem**: "No tracked changes visible"
**Solution**: In Word, go to Review → Track Changes → All Markup

**Problem**: "Files not found"
**Solution**: Make sure you're in the right directory:

```bash
cd /Users/hassantayyab/Documents/policy-edit
ls docs/ edits/ scripts/
```

## 🎉 That's It!

The manual method takes 5 minutes and always works. The automated Python scripts have issues on macOS, so stick with the manual approach for now.

**Bottom line**: Create your DOCX → Turn on track changes → Do find/replace → Save → Done!
