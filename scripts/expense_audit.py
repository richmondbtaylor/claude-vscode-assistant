"""
Comprehensive Expense Spreadsheet Audit
Reads all tabs, audits income, expenses, categories, signs, duplicates.
Fixes issues and rebuilds Summary tab.
"""

import gspread
import json
import random
import re
from collections import defaultdict

# Connect using authorized_user credentials
gc = gspread.oauth(
    credentials_filename=r"C:\Users\richm\AppData\Roaming\gspread\authorized_user.json",
    authorized_user_filename=r"C:\Users\richm\AppData\Roaming\gspread\authorized_user.json",
)

SPREADSHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
sh = gc.open_by_key(SPREADSHEET_ID)

# Read all worksheets
worksheets = sh.worksheets()
print("=== WORKSHEETS FOUND ===")
for ws in worksheets:
    print(f"  Tab: '{ws.title}' - {ws.row_count} rows x {ws.col_count} cols")

# Read all data from each tab
all_data = {}
for ws in worksheets:
    data = ws.get_all_values()
    all_data[ws.title] = data
    print(f"\n  '{ws.title}': {len(data)} rows (including header)")
    if data:
        print(f"    Headers: {data[0]}")

print("\n" + "="*80)
print("SECTION A: INCOME AUDIT - Checking Tab")
print("="*80)

# Find the Checking tab
checking_tab = None
bishop_tab = None
summary_tab = None

for name, data in all_data.items():
    nl = name.lower()
    if 'checking' in nl:
        checking_tab = (name, data)
    elif 'bishop' in nl:
        bishop_tab = (name, data)
    elif 'summary' in nl:
        summary_tab = (name, data)

if not checking_tab:
    print("WARNING: No 'Checking' tab found!")
    # Try to identify tabs
    for name in all_data:
        print(f"  Available: '{name}'")

# Helper to parse dollar amounts
def parse_amount(val):
    if not val or val.strip() == '':
        return 0.0
    val = str(val).strip()
    val = val.replace('$', '').replace(',', '').strip()
    if val == '' or val == '-':
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

# Analyze Checking tab
def analyze_checking(name, data):
    if not data:
        print("No data in Checking tab!")
        return

    headers = [h.strip().lower() for h in data[0]]
    print(f"\nHeaders: {data[0]}")

    # Identify column indices
    date_col = None
    desc_col = None
    amount_col = None
    category_col = None
    type_col = None

    for i, h in enumerate(headers):
        if 'date' in h:
            date_col = i
        elif 'description' in h or 'vendor' in h or 'memo' in h or 'name' in h:
            if desc_col is None:
                desc_col = i
        elif 'amount' in h or 'debit' in h:
            if amount_col is None:
                amount_col = i
        elif 'category' in h or 'type' in h:
            if 'type' in h:
                type_col = i
            else:
                category_col = i

    # If we can't find by keywords, try positional
    print(f"\n  Detected columns: date={date_col}, desc={desc_col}, amount={amount_col}, category={category_col}, type={type_col}")

    # Print first 5 data rows for context
    print("\n  Sample rows:")
    for row in data[1:6]:
        print(f"    {row}")

    # Find ALL positive amounts (credits/income)
    positive_entries = []
    negative_entries = []
    all_entries = []

    for i, row in enumerate(data[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue

        # Try to find amount - check all columns for numeric values
        amt = 0
        amt_col_used = None

        if amount_col is not None:
            amt = parse_amount(row[amount_col] if amount_col < len(row) else '')
            amt_col_used = amount_col

        # Also check if there are separate credit/debit columns
        for j, h in enumerate(headers):
            if 'credit' in h:
                credit_val = parse_amount(row[j] if j < len(row) else '')
                if credit_val != 0:
                    amt = abs(credit_val)
                    amt_col_used = j
            elif 'debit' in h and amount_col is None:
                debit_val = parse_amount(row[j] if j < len(row) else '')
                if debit_val != 0:
                    amt = -abs(debit_val)
                    amt_col_used = j

        date_val = row[date_col].strip() if date_col is not None and date_col < len(row) else ''
        desc_val = row[desc_col].strip() if desc_col is not None and desc_col < len(row) else ''
        cat_val = row[category_col].strip() if category_col is not None and category_col < len(row) else ''
        type_val = row[type_col].strip() if type_col is not None and type_col < len(row) else ''

        entry = {
            'row': i,
            'date': date_val,
            'desc': desc_val,
            'amount': amt,
            'category': cat_val,
            'type': type_val,
            'raw': row
        }
        all_entries.append(entry)

        if amt > 0:
            positive_entries.append(entry)
        elif amt < 0:
            negative_entries.append(entry)

    return all_entries, positive_entries, negative_entries, headers

# Run checking analysis
if checking_tab:
    check_entries, check_positives, check_negatives, check_headers = analyze_checking(*checking_tab)

    print(f"\n\nTotal entries in Checking: {len(check_entries)}")
    print(f"Positive (credit) entries: {len(check_positives)}")
    print(f"Negative (debit) entries: {len(check_negatives)}")

    # Classify positive entries
    w2_payroll = []
    biz_revenue = []
    client_payments = []
    personal_income = []
    transfers_not_income = []
    unclassified_positive = []

    w2_keywords = ['DRVN', 'CRANE STATIONERY', 'CRANE STATION', 'AEROTEK', 'FBO VARIOUS', 'LA FONDATION',
                   'PAYROLL', 'DIRECT DEP', 'SALARY', 'WAGE']
    biz_keywords = ['STRIPE']
    client_keywords = ['ZELLE.*AS DEVELOPME', 'ZELLE.*AS DEV', 'AS DEVELOPME']
    personal_income_keywords = ['ERIN TAYLOR']
    transfer_keywords = ['VENMO', 'CASH APP', 'CASHAPP', 'PAYPAL', 'DEPOSIT', 'MICRO-DEPOSIT',
                         'REWARD', 'REFUND', 'FIRECRAWL', 'TRANSFER', 'ZELLE']

    for entry in check_positives:
        desc_upper = entry['desc'].upper()
        cat_upper = entry['category'].upper()
        type_upper = entry['type'].upper()
        combined = f"{desc_upper} {cat_upper} {type_upper}"

        classified = False

        # W-2/Payroll
        for kw in w2_keywords:
            if re.search(kw, desc_upper):
                w2_payroll.append(entry)
                classified = True
                break
        if classified:
            continue

        # Business revenue (Stripe)
        for kw in biz_keywords:
            if kw in desc_upper:
                biz_revenue.append(entry)
                classified = True
                break
        if classified:
            continue

        # Client payments (Zelle AS DEVELOPME specifically)
        for kw in client_keywords:
            if re.search(kw, desc_upper):
                client_payments.append(entry)
                classified = True
                break
        if classified:
            continue

        # Personal income (Erin Taylor)
        for kw in personal_income_keywords:
            if kw in desc_upper:
                personal_income.append(entry)
                classified = True
                break
        if classified:
            continue

        # Transfers/not-income
        for kw in transfer_keywords:
            if kw in desc_upper:
                transfers_not_income.append(entry)
                classified = True
                break
        if classified:
            continue

        # Unclassified positive
        unclassified_positive.append(entry)

    def print_group(title, entries):
        total = sum(e['amount'] for e in entries)
        print(f"\n--- {title} ({len(entries)} entries, total: ${total:,.2f}) ---")
        for e in entries:
            print(f"  Row {e['row']}: {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:60]}  [{e['category']}] [{e['type']}]")
        return total

    t1 = print_group("W-2/PAYROLL INCOME", w2_payroll)
    t2 = print_group("BUSINESS REVENUE (Stripe)", biz_revenue)
    t3 = print_group("CLIENT PAYMENTS (Zelle AS DEVELOPME)", client_payments)
    t4 = print_group("PERSONAL INCOME (Erin Taylor)", personal_income)
    t5 = print_group("TRANSFERS/NOT INCOME", transfers_not_income)
    t6 = print_group("UNCLASSIFIED POSITIVE", unclassified_positive)

    real_income = t1 + t4
    business_income = t2 + t3
    not_income = t5

    print(f"\n\n=== INCOME SUMMARY ===")
    print(f"  Real W-2/Payroll Income:     ${t1:>12,.2f}")
    print(f"  Business Revenue (Stripe):   ${t2:>12,.2f}")
    print(f"  Client Payments:             ${t3:>12,.2f}")
    print(f"  Personal Income (Erin):      ${t4:>12,.2f}")
    print(f"  Transfers (NOT income):      ${t5:>12,.2f}")
    print(f"  Unclassified:                ${t6:>12,.2f}")
    print(f"  ---")
    print(f"  TRUE Total Income:           ${real_income + business_income:>12,.2f}")
    print(f"  (Excl. transfers/unclass.)")

print("\n" + "="*80)
print("SECTION B: BISHOP AI (BUSINESS) EXPENSES")
print("="*80)

if bishop_tab:
    bname, bdata = bishop_tab
    bheaders = [h.strip().lower() for h in bdata[0]]
    print(f"\nBishop AI Headers: {bdata[0]}")
    print(f"Sample rows:")
    for row in bdata[1:6]:
        print(f"  {row}")

    # Find amount column
    b_amt_col = None
    b_date_col = None
    b_desc_col = None
    b_cat_col = None

    for i, h in enumerate(bheaders):
        if 'amount' in h:
            b_amt_col = i
        elif 'date' in h:
            b_date_col = i
        elif 'description' in h or 'vendor' in h or 'memo' in h or 'merchant' in h:
            if b_desc_col is None:
                b_desc_col = i
        elif 'category' in h or 'type' in h:
            if b_cat_col is None:
                b_cat_col = i

    print(f"\n  Detected: date={b_date_col}, desc={b_desc_col}, amount={b_amt_col}, category={b_cat_col}")

    bishop_entries = []
    bishop_positive = 0
    bishop_negative = 0
    bishop_sign_issues = []

    for i, row in enumerate(bdata[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        amt = parse_amount(row[b_amt_col] if b_amt_col is not None and b_amt_col < len(row) else '')
        date_val = row[b_date_col].strip() if b_date_col is not None and b_date_col < len(row) else ''
        desc_val = row[b_desc_col].strip() if b_desc_col is not None and b_desc_col < len(row) else ''
        cat_val = row[b_cat_col].strip() if b_cat_col is not None and b_cat_col < len(row) else ''

        entry = {
            'row': i,
            'date': date_val,
            'desc': desc_val,
            'amount': amt,
            'category': cat_val,
            'raw': row
        }
        bishop_entries.append(entry)

        if amt > 0:
            bishop_positive += 1
            bishop_sign_issues.append(entry)
        elif amt < 0:
            bishop_negative += 1

    bishop_total = sum(e['amount'] for e in bishop_entries)
    print(f"\n  Total Bishop AI entries: {len(bishop_entries)}")
    print(f"  Total Bishop AI amount: ${bishop_total:,.2f}")
    print(f"  Positive amounts: {bishop_positive}")
    print(f"  Negative amounts: {bishop_negative}")

    # SIGN CONVENTION CHECK
    print(f"\n--- SIGN CONVENTION CHECK ---")
    if bishop_positive > 0 and bishop_negative > 0:
        print(f"  WARNING: Mixed signs! {bishop_positive} positive, {bishop_negative} negative")
        print(f"  Positive entries (potential issues):")
        for e in bishop_sign_issues:
            print(f"    Row {e['row']}: {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:60]}  [{e['category']}]")
    elif bishop_positive > 0:
        print(f"  All amounts positive ({bishop_positive} entries). Expenses stored as positive numbers.")
    elif bishop_negative > 0:
        print(f"  All amounts negative ({bishop_negative} entries). Expenses stored as negative numbers.")

    # Category breakdown
    bishop_categories = defaultdict(float)
    bishop_cat_counts = defaultdict(int)
    for e in bishop_entries:
        cat = e['category'] if e['category'] else '(blank)'
        bishop_categories[cat] += abs(e['amount'])
        bishop_cat_counts[cat] += 1

    print(f"\n  Bishop AI Category Breakdown:")
    for cat in sorted(bishop_categories.keys()):
        print(f"    {cat:30s}: ${bishop_categories[cat]:>10,.2f} ({bishop_cat_counts[cat]} entries)")
    print(f"    {'TOTAL':30s}: ${sum(bishop_categories.values()):>10,.2f}")

# Now find business expenses in Checking tab
print(f"\n--- BUSINESS EXPENSES IN CHECKING TAB ---")
if checking_tab:
    biz_in_checking = []
    for e in check_entries:
        cat_upper = e['category'].upper()
        type_upper = e['type'].upper()
        if 'BUSINESS' in cat_upper or 'BUSINESS' in type_upper or 'BIZ' in cat_upper:
            biz_in_checking.append(e)

    biz_check_total = sum(e['amount'] for e in biz_in_checking)
    print(f"  Business entries in Checking: {len(biz_in_checking)}")
    print(f"  Total: ${biz_check_total:,.2f}")
    for e in biz_in_checking:
        print(f"    Row {e['row']}: {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:60]}  [{e['category']}] [{e['type']}]")

print("\n" + "="*80)
print("SECTION C: PERSONAL EXPENSES")
print("="*80)

if checking_tab:
    personal_categories = defaultdict(float)
    personal_cat_counts = defaultdict(int)
    personal_entries_list = []

    for e in check_entries:
        cat = e['category'] if e['category'] else '(blank)'
        type_val = e['type'] if e['type'] else ''
        cat_upper = cat.upper()
        type_upper = type_val.upper()

        # Skip business entries and positive (income) entries for personal expense calc
        if 'BUSINESS' in cat_upper or 'BUSINESS' in type_upper or 'BIZ' in cat_upper:
            continue
        if e['amount'] > 0:
            continue

        personal_categories[cat] += abs(e['amount'])
        personal_cat_counts[cat] += 1
        personal_entries_list.append(e)

    print(f"\n  Personal Expense Categories in Checking:")
    for cat in sorted(personal_categories.keys()):
        print(f"    {cat:30s}: ${personal_categories[cat]:>10,.2f} ({personal_cat_counts[cat]} entries)")
    print(f"    {'TOTAL':30s}: ${sum(personal_categories.values()):>10,.2f}")

print("\n" + "="*80)
print("SECTION D: SIGN CONVENTION CHECK (already done above for Bishop AI)")
print("="*80)

# Also check Checking tab sign conventions
if checking_tab:
    # For expenses, should be negative. For income, should be positive.
    sign_issues_checking = []
    for e in check_entries:
        cat_upper = e['category'].upper()
        type_upper = e['type'].upper()

        # Income labeled but negative amount
        if ('INCOME' in cat_upper or 'INCOME' in type_upper or 'PAYROLL' in cat_upper) and e['amount'] < 0:
            sign_issues_checking.append(('Income but negative', e))

        # Check for expense categories with positive amounts (might be refunds - ok)

    if sign_issues_checking:
        print(f"\n  Sign issues in Checking: {len(sign_issues_checking)}")
        for issue_type, e in sign_issues_checking:
            print(f"    {issue_type}: Row {e['row']} {e['date']} ${e['amount']:,.2f} {e['desc'][:50]} [{e['category']}]")
    else:
        print(f"\n  No sign issues found in Checking tab.")

print("\n" + "="*80)
print("SECTION E: DUPLICATE CHECK")
print("="*80)

# Check for duplicates: same date + similar amount across/within tabs
all_combined = []
if checking_tab:
    for e in check_entries:
        all_combined.append({**e, 'tab': checking_tab[0]})
if bishop_tab:
    for e in bishop_entries:
        all_combined.append({**e, 'tab': bishop_tab[0]})

dupes_found = []
for i in range(len(all_combined)):
    for j in range(i+1, len(all_combined)):
        a = all_combined[i]
        b = all_combined[j]

        if a['date'] == b['date'] and a['date'] != '' and abs(abs(a['amount']) - abs(b['amount'])) < 0.01 and abs(a['amount']) > 0:
            # Check if descriptions are similar
            desc_a = a['desc'].upper()[:20]
            desc_b = b['desc'].upper()[:20]

            dupes_found.append((a, b))

if dupes_found:
    print(f"\n  Potential duplicates found: {len(dupes_found)}")
    for a, b in dupes_found[:30]:
        print(f"    DUPE: [{a['tab']}] Row {a['row']} {a['date']} ${a['amount']:,.2f} '{a['desc'][:40]}'")
        print(f"      vs  [{b['tab']}] Row {b['row']} {b['date']} ${b['amount']:,.2f} '{b['desc'][:40]}'")
        print()
else:
    print(f"\n  No exact duplicates found (same date + same amount).")

print("\n" + "="*80)
print("SECTION F: CATEGORY SPOT CHECK")
print("="*80)

# Check random rows for correct categorization
def spot_check_categorization(entries, tab_name, sample_size=50):
    if len(entries) < sample_size:
        sample = entries
    else:
        sample = random.sample(entries, sample_size)

    issues = []
    for e in sample:
        desc_upper = e['desc'].upper()
        cat = e['category'].upper() if e['category'] else ''

        # Known categorization rules
        # Subscriptions/software
        software_keywords = ['OPENAI', 'ANTHROPIC', 'GITHUB', 'NOTION', 'FIGMA', 'CANVA', 'ADOBE',
                           'MIDJOURNEY', 'CHATGPT', 'SLACK', 'ZOOM', 'ZAPIER', 'MAKE.COM', 'N8N',
                           'CURSOR', 'VERCEL', 'NETLIFY', 'AWS', 'GOOGLE CLOUD', 'DIGITAL OCEAN',
                           'HEROKU', 'SUPABASE', 'FIREBASE', 'MONGODB', 'AIRTABLE', 'WEBFLOW',
                           'CLOUDFLARE', 'NAMECHEAP', 'GODADDY', 'SQUARESPACE', 'SHOPIFY',
                           'MAILCHIMP', 'CONVERTKIT', 'SUBSTACK', 'GUMROAD', 'TEACHABLE',
                           'FIRECRAWL', 'REPLICATE', 'HUGGING', 'COLAB', 'REPLIT']

        food_keywords = ['DOORDASH', 'UBER EATS', 'GRUBHUB', 'MCDONALD', 'STARBUCKS', 'CHICK-FIL',
                        'CHIPOTLE', 'SUBWAY', 'PANERA', 'WENDY', 'TACO BELL', 'PIZZA',
                        'RESTAURANT', 'DINER', 'CAFE', 'COFFEE', 'BURGER']

        # Check for obvious mismatches
        for kw in software_keywords:
            if kw in desc_upper and cat and 'SOFTWARE' not in cat and 'SUBSCRIPTION' not in cat and 'BUSINESS' not in cat and 'TECH' not in cat and 'SaaS' not in cat.upper() and 'TOOL' not in cat:
                issues.append(f"  Row {e['row']}: '{e['desc'][:50]}' categorized as '{e['category']}' - might be Software/Subscription")
                break

        for kw in food_keywords:
            if kw in desc_upper and cat and 'FOOD' not in cat and 'DINING' not in cat and 'RESTAURANT' not in cat and 'MEAL' not in cat and 'EAT' not in cat:
                if 'PERSONAL' not in cat:
                    issues.append(f"  Row {e['row']}: '{e['desc'][:50]}' categorized as '{e['category']}' - might be Food/Dining")
                    break

    return issues

if checking_tab:
    issues_c = spot_check_categorization(check_entries, checking_tab[0])
    print(f"\n  Checking tab spot check ({min(50, len(check_entries))} rows):")
    if issues_c:
        for iss in issues_c:
            print(f"    {iss}")
    else:
        print(f"    No obvious categorization issues found.")

if bishop_tab:
    issues_b = spot_check_categorization(bishop_entries, bishop_tab[0])
    print(f"\n  Bishop AI tab spot check ({min(50, len(bishop_entries))} rows):")
    if issues_b:
        for iss in issues_b:
            print(f"    {iss}")
    else:
        print(f"    No obvious categorization issues found.")

print("\n" + "="*80)
print("SECTION G: SUMMARY TAB COMPARISON")
print("="*80)

if summary_tab:
    sname, sdata = summary_tab
    print(f"\nSummary Tab Contents:")
    for i, row in enumerate(sdata):
        print(f"  Row {i+1}: {row}")

print("\n" + "="*80)
print("FULL RAW DATA DUMP FOR VERIFICATION")
print("="*80)

# Print all checking entries
if checking_tab:
    print(f"\n--- ALL CHECKING ENTRIES ---")
    for e in check_entries:
        print(f"  R{e['row']:3d}: {e['date']:12s} ${e['amount']:>10,.2f}  {e['desc'][:55]:55s} [{e['category']}] [{e['type']}]")
    print(f"  TOTAL: ${sum(e['amount'] for e in check_entries):,.2f}")

if bishop_tab:
    print(f"\n--- ALL BISHOP AI ENTRIES ---")
    for e in bishop_entries:
        print(f"  R{e['row']:3d}: {e['date']:12s} ${e['amount']:>10,.2f}  {e['desc'][:55]:55s} [{e['category']}]")
    print(f"  TOTAL: ${sum(e['amount'] for e in bishop_entries):,.2f}")
