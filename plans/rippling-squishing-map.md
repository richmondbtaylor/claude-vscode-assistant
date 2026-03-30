# Plan: Expense Classifier Skill (TAXSORT Framework)

## Context

Rich needs a reusable Claude Code skill that reads bank-exported CSV files, classifies each transaction as business or personal, and produces a clean 4-section tax-prep report. The skill must support a learning mechanism (user corrections update the rules file) and flag incomplete transactions for manual review without halting processing.

---

## Skill Identity

- **Name:** `expense-classifier`
- **Framework:** TAXSORT (Transaction Analysis and eXpense Sorting for tax-Optimized Review of Transactions)
- **Trigger phrases:** "classify my expenses", "categorize this CSV", "sort my transactions", "prepare expense report", "tax expense report", "review my bank statement", "which expenses are business"

---

## Files to Create

```
skills/expense-classifier/
├── SKILL.md                         ← Main skill instruction file
├── scripts/
│   └── classify_expenses.py         ← Core classification script
└── rules/
    └── classification_rules.csv     ← Editable keyword/merchant rules
```

Plus root-level shortcut:
```
skills/expense-classifier.md         ← Single-line redirect (points to SKILL.md)
```

---

## SKILL.md Structure

### Frontmatter
```yaml
---
name: expense-classifier
description: >
  Classifies bank CSV transactions as 'business' or 'personal' for tax prep.
  Flags incomplete/ambiguous transactions. Supports user corrections that update
  the rules file for future runs.

  Use whenever user: shares a bank CSV, asks to categorize expenses, wants a
  tax expense report, or says "which of these are business expenses".

  Trigger on: 'classify my expenses', 'categorize transactions', 'expense report',
  'which are business expenses', 'tax prep', 'sort my bank statement'.
---
```

### TAXSORT Framework Sections in SKILL.md
1. **Inputs** — CSV path (required), rules file path (optional, defaults to `rules/classification_rules.csv`)
2. **Execution** — Run `scripts/classify_expenses.py` with args, capture output
3. **Output Format** — 4 sections (see below)
4. **Learning Mechanism** — How user corrections get saved to rules file
5. **Error Handling** — What to do for bad CSV, missing file, parse errors

---

## Python Script: `classify_expenses.py`

### Arguments
```
python classify_expenses.py <csv_path> [--rules <rules_path>] [--output <output_csv>]
```

### Logic
1. **Parse CSV** — detect common bank formats (Date, Description, Amount columns; handle varying column names)
2. **Load rules** — read `classification_rules.csv` with columns: `keyword`, `category`, `match_type` (exact/contains), `merchant_name`
3. **Classify each row:**
   - Match description against merchant list (exact) first
   - Then match against keywords (contains, case-insensitive)
   - If no match → flag as `REVIEW` with reason `"No matching rule"`
   - If amount is 0 or description is empty → flag as `REVIEW` with reason `"Missing data"`
4. **Output:**
   - Print structured report to stdout (4 sections)
   - Write `_classified.csv` alongside input file (adds `Category`, `Review_Flag`, `Review_Reason` columns)
5. **Logging** — write errors to stderr with row numbers

### Default Rules Categories Built In
- **Business keywords:** adobe, canva, notion, figma, aws, google workspace, zoom, slack, github, anthropic, openai, stripe, godaddy, namecheap, shopify, fiverr, upwork, wix, squarespace, mailchimp, convertkit, calendly, loom, airtable, zapier, make.com, software, subscription, hosting, domain, advertising, marketing, office, courier, postage, linkedin
- **Personal keywords:** grocery, supermarket, restaurant, cafe, coffee, netflix, spotify, amazon prime, cinema, pharmacy, fuel, petrol, gym, clothing, haircut, dentist, doctor, uber, lyft, airbnb

### Learning Mechanism
When user says "change X from personal to business" or similar correction:
- Claude appends a new row to `classification_rules.csv` with the merchant/keyword
- Re-run the script to verify the fix applied
- Confirm to user

---

## Output Report: 4 Sections

```
═══════════════════════════════════════════════════════
  EXPENSE CLASSIFICATION REPORT
  [date range] • [N] transactions • Generated [today]
═══════════════════════════════════════════════════════

## 1. BUSINESS EXPENSES  ($X,XXX.XX total — N transactions)
──────────────────────────────────────────────────────
[bullet list: Date | Vendor | Amount]

> CTA: Export this section as `business_expenses.csv` and share with your accountant — it's pre-formatted for Schedule C.

## 2. PERSONAL EXPENSES  ($X,XXX.XX total — N transactions)
──────────────────────────────────────────────────────
[bullet list: Date | Vendor | Amount]

> CTA: Review this list before filing — some items may qualify as home-office or mixed-use deductions.

## 3. FLAGGED FOR REVIEW  (N items need your attention)
──────────────────────────────────────────────────────
[bullet list: Date | Vendor | Amount | Reason]

> CTA: Respond with corrections in the format "Change [Vendor] to business/personal" — I'll update the rules so it auto-classifies next time.

## 4. SUMMARY & NEXT STEPS
──────────────────────────────────────────────────────
- Total transactions: N
- Business: $X,XXX.XX (N%)
- Personal: $X,XXX.XX (N%)
- Flagged: N items
- Output CSV: [path to _classified.csv]

> CTA: Run `/expense-classifier` again after resolving flagged items to get your final clean report.
```

---

## Classification Rules CSV Format

```csv
keyword,category,match_type,notes
adobe,business,contains,Adobe subscriptions (Creative Cloud etc)
netflix,personal,contains,Streaming - personal
stripe,business,exact,Payment processor fees
```

---

## Critical Files
- `skills/expense-classifier/SKILL.md` — new file
- `skills/expense-classifier/scripts/classify_expenses.py` — new file
- `skills/expense-classifier/rules/classification_rules.csv` — new file (seeded with ~40 default rules)
- `skills/expense-classifier.md` — new root shortcut file

---

## Verification

1. Drop any real bank CSV into the skill and run it
2. Confirm all 4 sections appear with correct totals
3. Tell Claude "change [some vendor] from personal to business"
4. Verify `classification_rules.csv` gets a new row
5. Re-run to confirm the correction applies
6. Check that a `_classified.csv` file was written with the `Category` column added
