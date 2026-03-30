---
name: expense-classifier
description: >
  Classifies bank CSV transactions as 'business' or 'personal' expenses for tax
  preparation using the TAXSORT Framework. Generates a 4-section scannable report,
  flags ambiguous/incomplete transactions for manual review, and learns from user
  corrections by updating a persistent rules file.

  Use this skill whenever the user:
  - Shares a bank statement or transaction CSV and wants it categorized
  - Asks "which of these are business expenses?", "classify my transactions", "sort my expenses"
  - Wants a tax expense report, expense summary, or Schedule C prep
  - Says "prepare my expenses for my accountant", "categorize my bank CSV", "expense report"
  - Drops a CSV with no instruction but it looks like bank transaction data

  Trigger on: 'classify my expenses', 'categorize transactions', 'expense report',
  'which are business expenses', 'tax prep', 'sort my bank statement',
  'review my expenses', 'business vs personal', 'prepare for accountant',
  'categorize this CSV', 'classify this bank statement'.

  Also trigger if the user uploads or pastes a path to a CSV file and says anything
  about expenses, taxes, or categorization.
---

# Expense Classifier — TAXSORT Framework

Classify bank CSV transactions as business or personal. Generate a 4-section tax-prep
report. Flag unclear items. Learn from corrections.

---

## Inputs

```
$ARGUMENTS
```

If no arguments provided, ask the user for:

1. **CSV file path** (required) — path to their bank export CSV
2. **Rules file path** (optional) — defaults to `~/.claude/skills/expense-classifier/rules/classification_rules.csv`
3. **Output CSV path** (optional) — defaults to `<input_filename>_classified.csv` in the same folder

---

## TAXSORT Framework

### Step 1 — Validate Inputs

Before running, confirm:
- The CSV file exists at the given path
- If not found, provide a clear error: `"ERROR: File not found at [path]. Please check the path and try again."`
- If the file exists but has unrecognized headers, the script will tell you which columns it couldn't find — ask the user to share the first 2 lines of the file so you can identify the right column names

### Step 2 — Run the Classifier

Execute the Python script:

```bash
python "C:\Users\richm\.claude\skills\expense-classifier\scripts\classify_expenses.py" "<csv_path>" [--rules "<rules_path>"] [--output "<output_path>"]
```

If the user didn't provide a rules path, omit the `--rules` flag — the script defaults to the correct location automatically.

Capture both stdout (the report) and stderr (any warnings/errors).

### Step 3 — Present the Report

Output the full report from the script exactly as printed. It is already formatted in 4 clear sections:

1. **BUSINESS EXPENSES** — itemized list with date, vendor, amount + accountant CTA
2. **PERSONAL EXPENSES** — itemized list + mixed-use review CTA
3. **FLAGGED FOR REVIEW** — items with missing data or no matching rule + correction CTA
4. **SUMMARY & NEXT STEPS** — totals, percentages, output CSV path

Do not paraphrase or summarize the report. Print it verbatim.

### Step 4 — Handle Corrections (Learning Mechanism)

If the user responds with a correction like:
> "Change Adobe to business"
> "Adobe should be business, not personal"
> "Mark Starbucks as personal"

Do the following:

1. **Append to the rules file** — add a new row to `classification_rules.csv`:
   ```
   <keyword>,<category>,contains,<user correction note>
   ```
   Use the vendor name (lowercased) as the keyword.

2. **Confirm the update:**
   > "Got it — I've added 'adobe' as a business expense to your rules file. It will auto-classify correctly on all future runs."

3. **Offer to re-run** — ask if they'd like to re-run the classifier so this correction is reflected in the current report.

4. If the user provides multiple corrections at once, batch all updates before re-running.

### Step 5 — Export Business CSV (if requested)

If the user asks for a business-only CSV or says "export this for my accountant":

```python
# Filter the _classified.csv for Category == BUSINESS and save as business_expenses.csv
import csv
with open("<classified_csv_path>") as f:
    rows = [r for r in csv.DictReader(f) if r.get("Category") == "BUSINESS"]
# Write filtered rows to business_expenses.csv
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| File not found | Exit with clear path error, ask user to verify the path |
| Unrecognized CSV headers | Show detected headers, ask user to share first 2 rows |
| Missing description in row | Flag row as REVIEW with reason "Missing Description" — do not stop |
| Invalid or missing amount | Flag row as REVIEW with reason "Invalid Amount" — do not stop |
| Zero amount | Flag row as REVIEW with reason "Zero Amount" — do not stop |
| No matching rule | Flag row as REVIEW with reason "No Matching Rule" — await user correction |
| Rules file not found | Warn user and fall back to built-in rules (script handles this) |

Errors in individual rows never halt the full run. All other transactions are still processed and reported.

---

## Rules File Format

The rules file lives at:
```
C:\Users\richm\.claude\skills\expense-classifier\rules\classification_rules.csv
```

Each row:
```csv
keyword,category,match_type,notes
adobe,business,contains,Adobe Creative Cloud
netflix,personal,contains,Streaming - personal
stripe,business,exact,Payment processor fees
```

- `match_type: exact` — full description must match keyword exactly (case-insensitive)
- `match_type: contains` — description must contain keyword anywhere (case-insensitive)
- Exact matches are checked first; contains matches are checked second
- To add a rule manually: open the CSV and append a row

---

## Correction Format

When appending a user correction to the rules file, use this format:
```python
import csv
with open(rules_path, "a", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([keyword_lowercased, category, "contains", f"User correction: {original_vendor}"])
```

---

## What Honest Results Look Like

The classifier is only as good as its rules. Be transparent:
- If many items land in "Flagged for Review", that's normal on first run — the rules file grows over time
- Corrections the user provides are permanently saved, so each run gets smarter
- The script does **not** use AI to guess categories — it uses deterministic keyword matching only
- For ambiguous vendors (e.g., "Amazon" which could be AWS or personal shopping), always flag for review rather than guess

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| Run classifier | `python classify_expenses.py <csv_path>` |
| Custom rules | `python classify_expenses.py <csv> --rules <rules.csv>` |
| Custom output | `python classify_expenses.py <csv> --output <out.csv>` |
| Add correction | Append row to `classification_rules.csv` |
| View rules | Open `classification_rules.csv` in any spreadsheet |
