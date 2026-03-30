#!/usr/bin/env python3
"""
TAXSORT Expense Classifier
Classifies bank CSV transactions as business or personal for tax preparation.
"""

import argparse
import csv
import os
import sys
import re
from datetime import datetime
from pathlib import Path


# ── Column name aliases ────────────────────────────────────────────────────────
DATE_ALIASES = ["date", "transaction date", "trans date", "posted date", "value date",
                "posting date", "settlement date"]
DESC_ALIASES = ["description", "merchant", "name", "payee", "details", "narrative",
                "transaction description", "memo", "reference", "particulars",
                "transaction details", "merchant name", "payee name"]
AMOUNT_ALIASES = ["amount", "debit", "credit", "transaction amount", "value", "sum",
                  "withdrawal", "payment", "charge"]


def normalize_header(h: str) -> str:
    return h.strip().lower().replace("_", " ")


def find_column(headers: list[str], aliases: list[str]) -> str | None:
    normalized = {normalize_header(h): h for h in headers}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


# ── Rules loader ───────────────────────────────────────────────────────────────
def load_rules(rules_path: str) -> list[dict]:
    rules = []
    try:
        with open(rules_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keyword = row.get("keyword", "").strip().lower()
                category = row.get("category", "").strip().lower()
                match_type = row.get("match_type", "contains").strip().lower()
                if keyword and category in ("business", "personal"):
                    rules.append({
                        "keyword": keyword,
                        "category": category,
                        "match_type": match_type,
                    })
    except FileNotFoundError:
        print(f"ERROR: Rules file not found: {rules_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR loading rules file: {e}", file=sys.stderr)
        sys.exit(1)
    return rules


# ── Classifier ─────────────────────────────────────────────────────────────────
def classify(description: str, rules: list[dict]) -> str | None:
    desc_lower = description.strip().lower()
    # Exact match first
    for rule in rules:
        if rule["match_type"] == "exact" and rule["keyword"] == desc_lower:
            return rule["category"]
    # Contains match
    for rule in rules:
        if rule["match_type"] == "contains" and rule["keyword"] in desc_lower:
            return rule["category"]
    return None


# ── Amount parser ──────────────────────────────────────────────────────────────
def parse_amount(raw: str) -> float | None:
    cleaned = re.sub(r"[^\d.\-]", "", raw.strip())
    if not cleaned or cleaned in (".", "-", "-."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


# ── CSV parser ─────────────────────────────────────────────────────────────────
def parse_csv(csv_path: str) -> tuple[list[dict], str, str, str]:
    """Returns (rows, date_col, desc_col, amount_col)."""
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Detect delimiter
    delimiter = ","
    if sample.count("\t") > sample.count(","):
        delimiter = "\t"

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames or []
            rows = list(reader)
    except Exception as e:
        print(f"ERROR parsing CSV: {e}", file=sys.stderr)
        sys.exit(1)

    if not headers:
        print("ERROR: CSV file appears to be empty or has no headers.", file=sys.stderr)
        sys.exit(1)

    date_col = find_column(headers, DATE_ALIASES)
    desc_col = find_column(headers, DESC_ALIASES)
    amount_col = find_column(headers, AMOUNT_ALIASES)

    missing = []
    if not date_col:
        missing.append("date")
    if not desc_col:
        missing.append("description")
    if not amount_col:
        missing.append("amount")

    if missing:
        print(
            f"ERROR: Could not identify these required columns: {', '.join(missing)}\n"
            f"Found headers: {', '.join(headers)}\n"
            f"Rename your columns to include one of: date, description, amount",
            file=sys.stderr,
        )
        sys.exit(1)

    return rows, date_col, desc_col, amount_col


# ── Main processing ────────────────────────────────────────────────────────────
def process(csv_path: str, rules_path: str, output_path: str | None):
    rules = load_rules(rules_path)
    rows, date_col, desc_col, amount_col = parse_csv(csv_path)

    business = []
    personal = []
    flagged = []
    parse_errors = []
    all_dates = []

    for i, row in enumerate(rows, start=2):  # row 1 = header
        date_raw = row.get(date_col, "").strip()
        desc_raw = row.get(desc_col, "").strip()
        amount_raw = row.get(amount_col, "").strip()

        row["Category"] = ""
        row["Review_Flag"] = ""
        row["Review_Reason"] = ""

        # Validate: missing description
        if not desc_raw:
            row["Review_Flag"] = "YES"
            row["Review_Reason"] = "Missing Description"
            row["Category"] = "REVIEW"
            flagged.append({"row": i, "date": date_raw, "description": "(none)", "amount": amount_raw, "reason": "Missing Description"})
            parse_errors.append(f"Row {i}: Missing description")
            continue

        # Validate: amount
        amount = parse_amount(amount_raw)
        if amount is None:
            row["Review_Flag"] = "YES"
            row["Review_Reason"] = "Invalid Amount"
            row["Category"] = "REVIEW"
            flagged.append({"row": i, "date": date_raw, "description": desc_raw, "amount": amount_raw, "reason": "Invalid Amount"})
            parse_errors.append(f"Row {i}: Invalid amount '{amount_raw}' for '{desc_raw}'")
            continue

        if amount == 0:
            row["Review_Flag"] = "YES"
            row["Review_Reason"] = "Zero Amount"
            row["Category"] = "REVIEW"
            flagged.append({"row": i, "date": date_raw, "description": desc_raw, "amount": "$0.00", "reason": "Zero Amount"})
            continue

        # Classify
        category = classify(desc_raw, rules)

        if category is None:
            row["Review_Flag"] = "YES"
            row["Review_Reason"] = "No Matching Rule"
            row["Category"] = "REVIEW"
            flagged.append({"row": i, "date": date_raw, "description": desc_raw, "amount": f"${abs(amount):.2f}", "reason": "No Matching Rule"})
        else:
            row["Review_Flag"] = "NO"
            row["Category"] = category.upper()
            entry = {"date": date_raw, "description": desc_raw, "amount": f"${abs(amount):.2f}"}
            if category == "business":
                business.append((abs(amount), entry))
                all_dates.append(date_raw)
            else:
                personal.append((abs(amount), entry))
                all_dates.append(date_raw)

    # Write classified CSV
    if rows:
        out_path = output_path or str(Path(csv_path).with_suffix("_classified.csv")).replace(
            Path(csv_path).suffix, "_classified.csv"
        )
        try:
            original_headers = list(rows[0].keys())
            extra_cols = ["Category", "Review_Flag", "Review_Reason"]
            base_cols = [c for c in original_headers if c not in extra_cols]
            fieldnames = base_cols + extra_cols
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            out_path = None
            print(f"WARNING: Could not write classified CSV: {e}", file=sys.stderr)
    else:
        out_path = None

    return business, personal, flagged, parse_errors, out_path


# ── Report printer ─────────────────────────────────────────────────────────────
def print_report(business, personal, flagged, parse_errors, out_path, csv_path):
    total_business = sum(a for a, _ in business)
    total_personal = sum(a for a, _ in personal)
    total_all = total_business + total_personal
    total_count = len(business) + len(personal) + len(flagged)
    today = datetime.now().strftime("%Y-%m-%d")

    pct_b = (total_business / total_all * 100) if total_all > 0 else 0
    pct_p = (total_personal / total_all * 100) if total_all > 0 else 0

    print()
    print("═" * 57)
    print("  EXPENSE CLASSIFICATION REPORT  —  TAXSORT FRAMEWORK")
    print(f"  Source: {os.path.basename(csv_path)}")
    print(f"  {total_count} transactions  •  Generated {today}")
    print("═" * 57)
    print()

    # Section 1: Business
    print(f"## 1. BUSINESS EXPENSES  (${total_business:,.2f} total — {len(business)} transactions)")
    print("─" * 55)
    if business:
        for _, e in sorted(business, key=lambda x: x[1]["date"]):
            print(f"  • {e['date']:<14}  {e['description'][:35]:<35}  {e['amount']}")
    else:
        print("  (none classified as business)")
    print()
    print("  > CTA: Export this section as `business_expenses.csv` and")
    print("         share with your accountant — pre-formatted for Schedule C.")
    print()

    # Section 2: Personal
    print(f"## 2. PERSONAL EXPENSES  (${total_personal:,.2f} total — {len(personal)} transactions)")
    print("─" * 55)
    if personal:
        for _, e in sorted(personal, key=lambda x: x[1]["date"]):
            print(f"  • {e['date']:<14}  {e['description'][:35]:<35}  {e['amount']}")
    else:
        print("  (none classified as personal)")
    print()
    print("  > CTA: Review this list before filing — some items may qualify")
    print("         as home-office or mixed-use deductions.")
    print()

    # Section 3: Flagged
    print(f"## 3. FLAGGED FOR REVIEW  ({len(flagged)} items need your attention)")
    print("─" * 55)
    if flagged:
        for f in flagged:
            print(f"  • {f['date']:<14}  {f['description'][:30]:<30}  {f['amount']:<10}  [{f['reason']}]")
    else:
        print("  (nothing flagged — all transactions classified)")
    print()
    print("  > CTA: Reply \"Change [Vendor] to business/personal\" — I'll update")
    print("         the rules file so it auto-classifies next time.")
    print()

    # Section 4: Summary
    print("## 4. SUMMARY & NEXT STEPS")
    print("─" * 55)
    print(f"  Total transactions:  {total_count}")
    print(f"  Business:            ${total_business:>10,.2f}  ({pct_b:.1f}%)")
    print(f"  Personal:            ${total_personal:>10,.2f}  ({pct_p:.1f}%)")
    print(f"  Flagged for review:  {len(flagged)} items")
    if out_path:
        print(f"  Classified CSV:      {out_path}")
    print()

    if parse_errors:
        print(f"  Parse warnings ({len(parse_errors)}):")
        for err in parse_errors:
            print(f"    ! {err}")
        print()

    print("  > CTA: Run /expense-classifier again after resolving flagged items")
    print("         to get your final clean report ready for your accountant.")
    print()
    print("═" * 57)
    print()


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="TAXSORT: Classify bank CSV expenses as business or personal."
    )
    parser.add_argument("csv_path", help="Path to the input bank CSV file")
    parser.add_argument(
        "--rules",
        default=None,
        help="Path to classification_rules.csv (default: rules/ alongside this script)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path for the classified output CSV (default: <input>_classified.csv)",
    )
    args = parser.parse_args()

    # Default rules path: same directory as this script's parent /rules/
    if args.rules is None:
        script_dir = Path(__file__).parent.parent
        args.rules = str(script_dir / "rules" / "classification_rules.csv")

    if not os.path.isfile(args.csv_path):
        print(f"ERROR: Input file not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    business, personal, flagged, parse_errors, out_path = process(
        args.csv_path, args.rules, args.output
    )
    print_report(business, personal, flagged, parse_errors, out_path, args.csv_path)


if __name__ == "__main__":
    main()
