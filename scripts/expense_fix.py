"""
Comprehensive Expense Spreadsheet Audit & Fix
Phase 2: Apply fixes and rebuild Summary tab
"""

import gspread
import re
from collections import defaultdict

gc = gspread.oauth(
    credentials_filename=r"C:\Users\richm\AppData\Roaming\gspread\authorized_user.json",
    authorized_user_filename=r"C:\Users\richm\AppData\Roaming\gspread\authorized_user.json",
)

SPREADSHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
sh = gc.open_by_key(SPREADSHEET_ID)

# Read all data
checking_ws = sh.worksheet('Checking')
bishop_ws = sh.worksheet('Bishop AI')
summary_ws = sh.worksheet('Summary')

checking_data = checking_ws.get_all_values()
bishop_data = bishop_ws.get_all_values()
summary_data = summary_ws.get_all_values()

def parse_amount(val):
    if not val or val.strip() == '':
        return 0.0
    val = str(val).strip().replace('$', '').replace(',', '').strip()
    if val == '' or val == '-':
        return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

print("=" * 80)
print("COMPLETE AUDIT REPORT")
print("=" * 80)

# ============================================================
# 1. BISHOP AI TAB - SIGN CONVENTION FIX
# ============================================================
print("\n### ISSUE 1: Bishop AI Sign Convention ###")
print("Rows 2-8 have NEGATIVE amounts (credit card charges).")
print("Rows 9+ have POSITIVE amounts (same type of charges).")
print("These are all EXPENSES and should be stored consistently as POSITIVE (absolute value).")

bishop_fixes = []
for i, row in enumerate(bishop_data[1:], start=2):
    if not any(cell.strip() for cell in row):
        continue
    amt = parse_amount(row[3])
    if amt < 0:
        bishop_fixes.append((i, row[3], abs(amt)))
        print(f"  FIX Row {i}: {row[3]} -> {abs(amt)}")

# Apply Bishop AI sign fixes
if bishop_fixes:
    cells_to_update = []
    for row_num, old_val, new_val in bishop_fixes:
        cells_to_update.append(gspread.Cell(row_num, 4, str(new_val)))
    bishop_ws.update_cells(cells_to_update)
    print(f"  FIXED {len(bishop_fixes)} sign issues in Bishop AI tab.")

# Re-read bishop data after fixes
bishop_data = bishop_ws.get_all_values()

# ============================================================
# 2. FULL INCOME ANALYSIS - CHECKING TAB
# ============================================================
print("\n### ISSUE 2: Income Classification ###")
print("Summary tab lumps transfers as 'Other Income' - this inflates income.")

# Parse all checking entries
check_entries = []
for i, row in enumerate(checking_data[1:], start=2):
    if not any(cell.strip() for cell in row):
        continue
    amt = parse_amount(row[3])
    check_entries.append({
        'row': i,
        'date': row[0].strip(),
        'desc': row[1].strip(),
        'vendor': row[2].strip() if len(row) > 2 else '',
        'amount': amt,
        'category': row[4].strip() if len(row) > 4 else '',
        'subcategory': row[5].strip() if len(row) > 5 else '',
        'biz_personal': row[6].strip() if len(row) > 6 else '',
        'tax_deductible': row[7].strip() if len(row) > 7 else '',
        'notes': row[8].strip() if len(row) > 8 else '',
    })

# Classify ALL positive entries
w2_payroll = []
schedule_c_income = []
transfers = []
rewards_refunds_micro = []
unclassified = []

for e in check_entries:
    if e['amount'] <= 0:
        continue

    desc_upper = e['desc'].upper()
    vendor_upper = e['vendor'].upper()

    # W-2 Payroll
    if any(kw in desc_upper for kw in ['DRVN', 'CRANE STATIONERY', 'AEROTEK', 'FBO VARIOUS', 'LA FONDATION']):
        w2_payroll.append(e)
    # Business/Schedule C (Stripe, Zelle AS DEVELOPME)
    elif 'STRIPE' in desc_upper:
        schedule_c_income.append(e)
    elif 'ZELLE' in desc_upper and 'AS DEVELOPME' in desc_upper:
        schedule_c_income.append(e)
    # Transfers (Venmo, Cash App, PayPal, Deposits)
    elif any(kw in desc_upper for kw in ['VENMO', 'CASH APP', 'CASHAPP', 'PAYPAL', 'DEPOSIT', 'TRANSFER']):
        transfers.append(e)
    # Zelle from individuals (not AS DEVELOPME)
    elif 'ZELLE' in desc_upper:
        transfers.append(e)
    # Rewards, refunds, micro-deposits, account verification
    elif any(kw in desc_upper for kw in ['ACCTVERIFY', 'REWARD', 'RWD', 'UPSIDE', 'REGULATION E',
                                          'REAL TIME PAYMENT', 'GUIDELINE', 'FIRECRAWL', 'CHASE CREDIT CRD']):
        rewards_refunds_micro.append(e)
    else:
        unclassified.append(e)

def sum_group(entries):
    return sum(e['amount'] for e in entries)

print(f"\n  W-2 Payroll Income:        ${sum_group(w2_payroll):>12,.2f} ({len(w2_payroll)} entries)")
for e in w2_payroll:
    print(f"    {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:55]}")

print(f"\n  Schedule C Income (Stripe): ${sum_group(schedule_c_income):>12,.2f} ({len(schedule_c_income)} entries)")
for e in schedule_c_income:
    print(f"    {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:55]}")

print(f"\n  Transfers (NOT income):    ${sum_group(transfers):>12,.2f} ({len(transfers)} entries)")
for e in transfers:
    print(f"    {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:55]}")

print(f"\n  Rewards/Refunds/Micro:     ${sum_group(rewards_refunds_micro):>12,.2f} ({len(rewards_refunds_micro)} entries)")
for e in rewards_refunds_micro:
    print(f"    {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:55]}")

print(f"\n  Unclassified:              ${sum_group(unclassified):>12,.2f} ({len(unclassified)} entries)")
for e in unclassified:
    print(f"    {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:55]}")

total_real_income = sum_group(w2_payroll) + sum_group(schedule_c_income)
total_transfers = sum_group(transfers)
total_rewards = sum_group(rewards_refunds_micro)
total_unclass = sum_group(unclassified)

print(f"\n  === CORRECTED INCOME ===")
print(f"  TRUE W-2 Income:              ${sum_group(w2_payroll):>12,.2f}")
print(f"  TRUE Schedule C Income:       ${sum_group(schedule_c_income):>12,.2f}")
print(f"  TRUE Total Earned Income:     ${total_real_income:>12,.2f}")
print(f"  Transfers (excluded):         ${total_transfers:>12,.2f}")
print(f"  Rewards/Refunds (excluded):   ${total_rewards:>12,.2f}")
print(f"  ")
print(f"  Summary tab currently says:   $    87,412.27")
print(f"  ACTUAL income:                ${total_real_income:>12,.2f}")
print(f"  OVERSTATED BY:                ${87412.27 - total_real_income:>12,.2f}")

# ============================================================
# 3. BUSINESS EXPENSES ANALYSIS
# ============================================================
print("\n\n### ISSUE 3: Business Expenses ###")

# Bishop AI tab - separate business vs personal
bishop_business = []
bishop_personal = []

for i, row in enumerate(bishop_data[1:], start=2):
    if not any(cell.strip() for cell in row):
        continue
    amt = parse_amount(row[3])
    cat = row[4].strip() if len(row) > 4 else ''
    biz = row[6].strip() if len(row) > 6 else ''

    entry = {
        'row': i, 'date': row[0].strip(), 'desc': row[1].strip(),
        'vendor': row[2].strip(), 'amount': amt, 'category': cat,
        'biz_personal': biz
    }

    if 'Business' in cat or 'Business' in biz:
        bishop_business.append(entry)
    else:
        bishop_personal.append(entry)

print(f"  Bishop AI Business entries: {len(bishop_business)}, total: ${sum(e['amount'] for e in bishop_business):,.2f}")
print(f"  Bishop AI Personal entries: {len(bishop_personal)}, total: ${sum(e['amount'] for e in bishop_personal):,.2f}")

# Checking tab business expenses
check_business = []
for e in check_entries:
    if e['amount'] >= 0:
        continue
    cat_upper = e['category'].upper()
    biz_upper = e['biz_personal'].upper()
    subcat = e['subcategory'].upper()

    # Business categories in checking
    if any(kw in subcat for kw in ['AI/ML', 'DEVELOPER', 'DOMAIN', 'HOSTING', 'LEAD GEN',
                                    'CONTRACT LABOR', 'PRODUCTIVITY', 'WEB SCRAPING']):
        check_business.append(e)
    elif any(kw in cat_upper for kw in ['BUSINESS']):
        check_business.append(e)
    elif any(kw in biz_upper for kw in ['BUSINESS']):
        check_business.append(e)

check_biz_total = sum(abs(e['amount']) for e in check_business)
print(f"\n  Checking tab Business expenses: {len(check_business)}, total: ${check_biz_total:,.2f}")
for e in check_business:
    print(f"    {e['date']}  ${e['amount']:>10,.2f}  {e['desc'][:50]}  [{e['subcategory']}]")

bishop_biz_total = sum(e['amount'] for e in bishop_business)

# Bishop AI business breakdown by category
bishop_biz_cats = defaultdict(float)
for e in bishop_business:
    bishop_biz_cats[e['category']] += e['amount']

print(f"\n  Bishop AI Business by category:")
for cat in sorted(bishop_biz_cats.keys()):
    print(f"    {cat:40s}: ${bishop_biz_cats[cat]:>10,.2f}")

# COMBINED business expenses
print(f"\n  COMBINED Business Expenses:")
print(f"    Bishop AI tab:              ${bishop_biz_total:>10,.2f}")
print(f"    Checking tab:               ${check_biz_total:>10,.2f}")
print(f"    TOTAL:                      ${bishop_biz_total + check_biz_total:>10,.2f}")
print(f"    Summary currently says:     $  5,050.31")

# ============================================================
# 4. PERSONAL EXPENSES - Category Totals
# ============================================================
print("\n\n### ISSUE 4: Personal Expenses ###")

# Bishop AI personal by category
bishop_pers_cats = defaultdict(float)
for e in bishop_personal:
    # Normalize category
    cat = e['category']
    if cat.startswith('Personal - '):
        cat = cat[len('Personal - '):]
    bishop_pers_cats[cat] += e['amount']

# Checking personal expenses (negative amounts, non-business)
check_personal = []
for e in check_entries:
    if e['amount'] >= 0:
        continue
    if e in check_business:
        continue
    # Skip transfers
    subcat = e['subcategory'].upper()
    cat = e['category'].upper()
    if 'TRANSFER' in subcat or 'CREDIT CARD PAYMENT' in subcat:
        continue
    if 'CRYPTOCURRENCY' in subcat:
        continue
    check_personal.append(e)

check_pers_cats = defaultdict(float)
for e in check_personal:
    subcat = e['subcategory'] if e['subcategory'] else e['category']
    check_pers_cats[subcat] += abs(e['amount'])

# Combined personal
all_pers_cats = defaultdict(float)
for cat, amt in bishop_pers_cats.items():
    all_pers_cats[cat] += amt
for cat, amt in check_pers_cats.items():
    all_pers_cats[cat] += amt

print(f"  Combined Personal Expense Categories:")
total_personal = 0
for cat in sorted(all_pers_cats.keys()):
    print(f"    {cat:35s}: ${all_pers_cats[cat]:>10,.2f}")
    total_personal += all_pers_cats[cat]
print(f"    {'TOTAL':35s}: ${total_personal:>10,.2f}")

# Checking transfers & crypto (excluded from personal)
check_transfers = []
check_crypto = []
check_cc_payments = []
for e in check_entries:
    if e['amount'] >= 0:
        continue
    subcat = e['subcategory'].upper()
    if 'TRANSFER' in subcat:
        check_transfers.append(e)
    elif 'CREDIT CARD PAYMENT' in subcat:
        check_cc_payments.append(e)
    elif 'CRYPTOCURRENCY' in subcat:
        check_crypto.append(e)

print(f"\n  Excluded from personal expenses:")
print(f"    Transfers out:          ${sum(abs(e['amount']) for e in check_transfers):>10,.2f} ({len(check_transfers)} entries)")
print(f"    Credit card payments:   ${sum(abs(e['amount']) for e in check_cc_payments):>10,.2f} ({len(check_cc_payments)} entries)")
print(f"    Cryptocurrency:         ${sum(abs(e['amount']) for e in check_crypto):>10,.2f} ({len(check_crypto)} entries)")

# ============================================================
# 5. CROSS-TAB DUPLICATES
# ============================================================
print("\n\n### ISSUE 5: Cross-Tab Duplicates ###")
print("Items appearing in BOTH Bishop AI and Checking with same date+amount:")

cross_dupes = []
for be in bishop_personal + bishop_business:
    for ce in check_entries:
        if be['date'] == ce['date'] and abs(abs(be['amount']) - abs(ce['amount'])) < 0.02:
            cross_dupes.append((be, ce))

if cross_dupes:
    print(f"  Found {len(cross_dupes)} potential cross-tab matches (may include false positives)")
    for be, ce in cross_dupes[:20]:
        print(f"    Bishop R{be['row']}: {be['date']} ${be['amount']:>8,.2f} '{be['desc'][:35]}'")
        print(f"    Check  R{ce['row']}: {ce['date']} ${ce['amount']:>8,.2f} '{ce['desc'][:35]}'")
        print()
else:
    print("  No cross-tab duplicates found.")

# ============================================================
# 6. SUMMARY TAB - CURRENT vs CORRECTED
# ============================================================
print("\n" + "=" * 80)
print("SUMMARY TAB: CURRENT vs CORRECTED VALUES")
print("=" * 80)

# Current Summary values
print(f"\n{'ITEM':<45} {'CURRENT':>15} {'CORRECTED':>15} {'DELTA':>15}")
print("-" * 90)

current_sched_c = 580.25
current_w2 = 35188.15
current_other = 51643.87
current_total_income = 87412.27
current_biz_exp = 5050.31
current_pers_exp = 67773.64

corrected_sched_c = sum_group(schedule_c_income)
corrected_w2 = sum_group(w2_payroll)
corrected_other = 0.00  # transfers/rewards are NOT income
corrected_total_income = corrected_w2 + corrected_sched_c
corrected_biz_exp = bishop_biz_total + check_biz_total
# For personal expenses, use the bishop personal + checking personal (excluding transfers, CC payments, crypto)
bishop_pers_total = sum(e['amount'] for e in bishop_personal)
check_pers_total = sum(abs(e['amount']) for e in check_personal)
corrected_pers_exp = bishop_pers_total + check_pers_total

print(f"{'Schedule C Income':<45} ${current_sched_c:>14,.2f} ${corrected_sched_c:>14,.2f} ${corrected_sched_c - current_sched_c:>14,.2f}")
print(f"{'W-2 Income':<45} ${current_w2:>14,.2f} ${corrected_w2:>14,.2f} ${corrected_w2 - current_w2:>14,.2f}")
print(f"{'Other Income (transfers/rewards)':<45} ${current_other:>14,.2f} ${corrected_other:>14,.2f} ${corrected_other - current_other:>14,.2f}")
print(f"{'TOTAL INCOME':<45} ${current_total_income:>14,.2f} ${corrected_total_income:>14,.2f} ${corrected_total_income - current_total_income:>14,.2f}")
print(f"{'Business Expenses':<45} ${current_biz_exp:>14,.2f} ${corrected_biz_exp:>14,.2f} ${corrected_biz_exp - current_biz_exp:>14,.2f}")
print(f"{'Personal Expenses':<45} ${current_pers_exp:>14,.2f} ${corrected_pers_exp:>14,.2f} ${corrected_pers_exp - current_pers_exp:>14,.2f}")

net_sched_c = corrected_sched_c - corrected_biz_exp
print(f"\n{'NET Schedule C (Income - Expenses)':<45} ${-4470.06:>14,.2f} ${net_sched_c:>14,.2f}")

# ============================================================
# 7. REBUILD SUMMARY TAB
# ============================================================
print("\n\n" + "=" * 80)
print("REBUILDING SUMMARY TAB...")
print("=" * 80)

# Build detailed business expense breakdown from checking subcategories
biz_by_subcat = defaultdict(lambda: {'amount': 0, 'count': 0, 'items': []})
for e in check_business:
    subcat = e['subcategory'] if e['subcategory'] else 'Other'
    biz_by_subcat[subcat]['amount'] += abs(e['amount'])
    biz_by_subcat[subcat]['count'] += 1
    biz_by_subcat[subcat]['items'].append(e['vendor'] or e['desc'][:30])

for e in bishop_business:
    cat = e['category'].replace('Business/', '').replace('Business - ', '').replace('Business/R&D ', '')
    biz_by_subcat[cat]['amount'] += e['amount']
    biz_by_subcat[cat]['count'] += 1
    biz_by_subcat[cat]['items'].append(e['vendor'] or e['desc'][:30])

# Personal expense by month from Bishop AI
bishop_pers_by_month_cat = defaultdict(lambda: defaultdict(float))
for e in bishop_personal:
    if e['date']:
        month = e['date'][:7]  # YYYY-MM
        cat = e['category']
        if cat.startswith('Personal - '):
            cat = cat[len('Personal - '):]
        bishop_pers_by_month_cat[month][cat] += e['amount']

# Personal expense by month from Checking
check_pers_by_month_cat = defaultdict(lambda: defaultdict(float))
for e in check_personal:
    if e['date']:
        month = e['date'][:7]
        subcat = e['subcategory'] if e['subcategory'] else e['category']
        check_pers_by_month_cat[month][subcat] += abs(e['amount'])

# Transfer amounts by month
transfer_by_month = defaultdict(float)
for e in transfers:
    if e['date']:
        month = e['date'][:7]
        transfer_by_month[month] += e['amount']
# Outgoing transfers
for e in check_transfers:
    if e['date']:
        month = e['date'][:7]
        transfer_by_month[month] += e['amount']  # negative

# Income by month
income_by_month = defaultdict(float)
for e in w2_payroll + schedule_c_income:
    if e['date']:
        month = e['date'][:7]
        income_by_month[month] += e['amount']

# Build the new Summary tab
new_summary = []

# Section 1: Schedule C Income
new_summary.append(['SCHEDULE C - BUSINESS INCOME', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['Source', 'Type', 'Count', 'Total', '', '', '', '', '', '', '', '', ''])

for e in schedule_c_income:
    vendor = e['vendor'] or e['desc'][:30]
    new_summary.append([vendor, 'Schedule C Gross Receipts', '1', f"${e['amount']:,.2f}", '', '', '', '', '', '', '', '', ''])

new_summary.append([f'SUBTOTAL - Schedule C Income', '', '', f"${corrected_sched_c:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Section 2: W-2 Income
new_summary.append(['W-2 INCOME (Form W-2, not Schedule C)', '', '', '', '', '', '', '', '', '', '', '', ''])

w2_by_employer = defaultdict(lambda: {'count': 0, 'total': 0})
for e in w2_payroll:
    # Normalize employer name
    desc_upper = e['desc'].upper()
    if 'DRVN' in desc_upper:
        emp = 'DRVN Payroll'
    elif 'CRANE' in desc_upper:
        emp = 'Crane Stationery Corp'
    elif 'AEROTEK' in desc_upper:
        emp = 'Aerotek Aviation'
    elif 'FBO' in desc_upper:
        emp = 'FBO Various'
    elif 'FONDATION' in desc_upper:
        emp = 'La Fondation'
    else:
        emp = e['vendor'] or e['desc'][:30]
    w2_by_employer[emp]['count'] += 1
    w2_by_employer[emp]['total'] += e['amount']

for emp in sorted(w2_by_employer.keys()):
    d = w2_by_employer[emp]
    new_summary.append([emp, 'W-2 Wages', str(d['count']), f"${d['total']:,.2f}", '', '', '', '', '', '', '', '', ''])

new_summary.append([f'SUBTOTAL - W-2 Income', '', '', f"${corrected_w2:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Section 3: Transfers & Other (NOT Income)
new_summary.append(['TRANSFERS & OTHER (Not Taxable Income)', '', '', '', '', '', '', '', '', '', '', '', ''])

transfer_groups = defaultdict(lambda: {'count': 0, 'total': 0})
for e in transfers:
    desc_upper = e['desc'].upper()
    if 'VENMO' in desc_upper:
        grp = 'Venmo Transfer In'
    elif 'CASH APP' in desc_upper or 'CASHAPP' in desc_upper:
        grp = 'Cash App Transfer'
    elif 'PAYPAL' in desc_upper:
        grp = 'PayPal Transfer'
    elif 'DEPOSIT' in desc_upper:
        grp = 'Bank Deposit'
    elif 'ZELLE' in desc_upper:
        grp = 'Zelle Credit (personal)'
    else:
        grp = 'Other Transfer'
    transfer_groups[grp]['count'] += 1
    transfer_groups[grp]['total'] += e['amount']

for grp in sorted(transfer_groups.keys()):
    d = transfer_groups[grp]
    new_summary.append([grp, 'Transfer (not income)', str(d['count']), f"${d['total']:,.2f}", '', '', '', '', '', '', '', '', ''])

new_summary.append([f'SUBTOTAL - Transfers', '', '', f"${total_transfers:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Rewards/Refunds
new_summary.append(['REWARDS, REFUNDS & MICRO-DEPOSITS (Not Income)', '', '', '', '', '', '', '', '', '', '', '', ''])
for e in rewards_refunds_micro:
    vendor = e['vendor'] or e['desc'][:40]
    new_summary.append([vendor, 'Not income', '1', f"${e['amount']:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append([f'SUBTOTAL - Rewards/Refunds', '', '', f"${total_rewards:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Total Income
new_summary.append([f'TOTAL EARNED INCOME (W-2 + Schedule C)', '', '', f"${corrected_total_income:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append([f'TOTAL TRANSFERS (not income)', '', '', f"${total_transfers:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append([f'TOTAL REWARDS/REFUNDS (not income)', '', '', f"${total_rewards:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Section 4: Schedule C Business Expenses
new_summary.append(['SCHEDULE C - BUSINESS EXPENSES (Tax Deductible)', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['Category', 'Source', 'Count', 'Amount', '', '', '', '', '', '', '', '', ''])

for subcat in sorted(biz_by_subcat.keys()):
    d = biz_by_subcat[subcat]
    vendors = ', '.join(set(d['items']))[:60]
    new_summary.append([subcat, vendors, str(d['count']), f"${d['amount']:,.2f}", '', '', '', '', '', '', '', '', ''])

new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append([f'TOTAL BUSINESS EXPENSES', '', '', f"${corrected_biz_exp:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Net Schedule C
new_summary.append([f'NET SCHEDULE C INCOME (Gross - Expenses)', '', '', f"${net_sched_c:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Section 5: Personal Expenses by Month
months = sorted(set(
    list(bishop_pers_by_month_cat.keys()) +
    list(check_pers_by_month_cat.keys())
))

# Merge categories
all_cats_set = set()
for m in months:
    all_cats_set.update(bishop_pers_by_month_cat[m].keys())
    all_cats_set.update(check_pers_by_month_cat[m].keys())
all_cats_sorted = sorted(all_cats_set)

# Format month headers
month_labels = []
for m in months:
    parts = m.split('-')
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    label = f"{month_names[int(parts[1])]} {parts[0]}"
    month_labels.append(label)

new_summary.append(['PERSONAL EXPENSE SUMMARY', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Header row: Category + months + TOTAL (pad to 13 cols)
header_row = ['Category'] + month_labels + ['TOTAL']
while len(header_row) < 13:
    header_row.append('')
new_summary.append(header_row[:13])

# Category rows
monthly_totals = [0] * len(months)
grand_total = 0

for cat in all_cats_sorted:
    row = [cat]
    cat_total = 0
    for mi, m in enumerate(months):
        val = bishop_pers_by_month_cat[m].get(cat, 0) + check_pers_by_month_cat[m].get(cat, 0)
        if val > 0:
            row.append(f"${val:,.2f}")
        else:
            row.append('')
        cat_total += val
        monthly_totals[mi] += val
    row.append(f"${cat_total:,.2f}")
    grand_total += cat_total
    while len(row) < 13:
        row.append('')
    new_summary.append(row[:13])

# Monthly total row
total_row = ['MONTHLY TOTAL']
for mi, mt in enumerate(monthly_totals):
    total_row.append(f"${mt:,.2f}")
total_row.append(f"${grand_total:,.2f}")
while len(total_row) < 13:
    total_row.append('')
new_summary.append(total_row[:13])

new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Section 6: Monthly Cash Flow
new_summary.append(['MONTHLY CASH FLOW (Checking Account)', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['Month', 'Earned Income', 'Business Expenses', 'Personal Expenses', 'Transfers Net', 'Net', '', '', '', '', '', '', ''])

total_inc = 0
total_biz = 0
total_pers = 0
total_trans = 0
total_net = 0

for mi, m in enumerate(months):
    inc = income_by_month.get(m, 0)
    biz = 0
    for e in check_business:
        if e['date'][:7] == m:
            biz += abs(e['amount'])
    for e in bishop_business:
        if e['date'][:7] == m:
            biz += e['amount']

    pers = monthly_totals[mi] if mi < len(monthly_totals) else 0
    trans = transfer_by_month.get(m, 0)
    net = inc - biz - pers + trans

    total_inc += inc
    total_biz += biz
    total_pers += pers
    total_trans += trans
    total_net += net

    label = month_labels[mi] if mi < len(month_labels) else m
    new_summary.append([label, f"${inc:,.2f}", f"${biz:,.2f}", f"${pers:,.2f}", f"${trans:,.2f}", f"${net:,.2f}", '', '', '', '', '', '', ''])

new_summary.append(['TOTAL', f"${total_inc:,.2f}", f"${total_biz:,.2f}", f"${total_pers:,.2f}", f"${total_trans:,.2f}", f"${total_net:,.2f}", '', '', '', '', '', '', ''])

new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])

# Section 7: Tax Summary
new_summary.append(['TAX SUMMARY', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['Item', '', '', 'Amount', '', '', '', '', '', '', '', '', ''])
new_summary.append(['Total W-2 Income (Form W-2/1040)', '', '', f"${corrected_w2:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['Total Schedule C Gross Income', '', '', f"${corrected_sched_c:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['Total Schedule C Deductions', '', '', f"${corrected_biz_exp:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['Schedule C Net Profit/Loss', '', '', f"${net_sched_c:,.2f}", '', '', '', '', '', '', '', '', ''])
new_summary.append(['Total Tax-Deductible Expenses', '', '', f"${corrected_biz_exp:,.2f}", '', '', '', '', '', '', '', '', ''])

se_income = max(0, net_sched_c)
se_tax = se_income * 0.153
new_summary.append([f'Estimated Self-Employment Tax (15.3%)', '', '', f"${se_tax:,.2f}", '', '', '', '', '', '', '', '', ''])
quarterly = se_tax / 4
new_summary.append([f'Estimated Quarterly Payment', '', '', f"${quarterly:,.2f}", '', '', '', '', '', '', '', '', ''])

new_summary.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['NOTES:', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- W-2 income reported on Form W-2 from each employer, not Schedule C', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- Schedule C income/expenses for sole proprietorship (Bishop AI)', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- Transfers (Venmo/Cash App/PayPal/Zelle) are NOT taxable income', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- Self-employment tax = 15.3% (12.4% SS + 2.9% Medicare) on net SE income', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- Quarterly estimated payments due: Apr 15, Jun 15, Sep 15, Jan 15', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(["- Home office deduction may apply (Form 8829) for utilities marked 'Partial'", '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- Vehicle expenses: track business mileage for Schedule C Line 9', '', '', '', '', '', '', '', '', '', '', '', ''])
new_summary.append(['- AUDIT: Corrected on 2026-04-02. Previous version overstated income by counting transfers.', '', '', '', '', '', '', '', '', '', '', '', ''])

# Clear existing Summary and write new data
print(f"\n  Writing {len(new_summary)} rows to Summary tab...")
summary_ws.clear()
summary_ws.update(range_name='A1', values=new_summary)
print("  Summary tab rebuilt successfully!")

# ============================================================
# FINAL REPORT
# ============================================================
print("\n\n" + "=" * 80)
print("FINAL CORRECTED NUMBERS")
print("=" * 80)

print(f"""
  W-2 Income:                       ${corrected_w2:>12,.2f}
  Schedule C Gross Income:          ${corrected_sched_c:>12,.2f}
  TOTAL EARNED INCOME:              ${corrected_total_income:>12,.2f}

  Transfers In (not income):        ${total_transfers:>12,.2f}
  Rewards/Refunds (not income):     ${total_rewards:>12,.2f}

  Business Expenses (Schedule C):   ${corrected_biz_exp:>12,.2f}
  Personal Expenses:                ${corrected_pers_exp:>12,.2f}

  Net Schedule C:                   ${net_sched_c:>12,.2f}
  Self-Employment Tax:              ${se_tax:>12,.2f}

  KEY CHANGES:
  - Income REDUCED by ${current_total_income - corrected_total_income:>12,.2f} (transfers removed)
  - Previous income was overstated 2.4x
  - Bishop AI tab: fixed {len(bishop_fixes)} sign-flipped rows
  - Summary tab: completely rebuilt with correct figures
""")
