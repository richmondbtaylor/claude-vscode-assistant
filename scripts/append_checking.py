import gspread
from datetime import datetime

# Auth
creds_path = r"C:\Users\richm\AppData\Roaming\gspread\authorized_user.json"
gc = gspread.oauth(credentials_filename=creds_path, authorized_user_filename=creds_path)

SHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
sh = gc.open_by_key(SHEET_ID)
ws = sh.worksheet("Checking")

# Get existing data to check for duplicates
existing = ws.get_all_values()
print(f"Existing rows (incl header): {len(existing)}")
if existing:
    print(f"Header: {existing[0]}")
    print(f"First data row: {existing[1] if len(existing) > 1 else 'none'}")
    print(f"Last data row: {existing[-1]}")

# Build a set of existing rows for dedup (date, description, amount)
existing_set = set()
for row in existing[1:]:
    if len(row) >= 3:
        existing_set.add((row[0], row[1], row[2]))

print(f"\nExisting unique keys: {len(existing_set)}")

# CSV data - parsed transactions
raw_txns = [
    ("06/02/2025", "PAYPAL INST XFER RICHMOND TAYLO VUDU LLC", -4.37),
    ("06/02/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER EATS", -4.38),
    ("06/02/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER", -10.20),
    ("06/02/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER", -13.71),
    ("06/02/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER EATS", -18.86),
    ("06/02/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER EATS", -21.52),
    ("06/03/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER EATS", -3.59),
    ("06/03/2025", "Ludlam OP RENT Richmond Taylo 240550163", -2103.00),
    ("06/03/2025", "FREEDOM MTG PYMTS RICHMOND B TAY xxxxxx2242", -2666.10),
    ("06/04/2025", "STRIPE TRANSFER RICHMOND TAYLO ST-D1L5E7Y9R1K9", 193.02),
    ("06/04/2025", "AMEX EPAYMENT ACH PMT RICHMOND TAYLO M2118", -1358.44),
    ("06/05/2025", "CHASE CREDIT CRD EPAY RICHMOND B TAY xxxxxx9128", -401.78),
    ("06/06/2025", "DRVN PAYROLL RICHMOND B TAY", 2467.33),
    ("06/09/2025", "VENMO CASHOUT RICHMOND TAYLO", 1500.00),
    ("06/09/2025", "PAYPAL INST XFER RICHMOND TAYLO APPLE.COM BILL", -0.99),
    ("06/09/2025", "PAYPAL INST XFER RICHMOND TAYLO APPLE.COM BILL", -7.67),
    ("06/09/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx74827", -32.00),
    ("06/09/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -50.00),
    ("06/10/2025", "Cash App Richmond B Richmond B Tay", 1500.00),
    ("06/10/2025", "Woods At Montice L2281784 Richmond Taylo", -48.00),
    ("06/11/2025", "PAYPAL TRANSFER RICHMOND TAYLO", 800.00),
    ("06/11/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/11/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx42502", -27.89),
    ("06/11/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -50.00),
    ("06/12/2025", "PAYPAL INST XFER RICHMOND TAYLO APPLE.COM BILL", -16.45),
    ("06/13/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/13/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/13/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/13/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/16/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/16/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/16/2025", "OPENAI OPENAI *CH LINK ST-V2K3J0H8R9W5", -21.95),
    ("06/16/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx42121", -52.11),
    ("06/16/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx05729", -52.88),
    ("06/16/2025", "FPL DIRECT DEBIT ELEC PYMT RICHMOND BISHO", -84.03),
    ("06/16/2025", "HOSTINGER INTERN IAT PAYPAL RICHMOND TAYLO xxxxxxxx26955", -38.40),
    ("06/17/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("06/18/2025", "AMEX EPAYMENT ACH PMT RICHMOND TAYLO M1266", -981.82),
    ("06/20/2025", "DRVN PAYROLL RICHMOND B TAY", 2429.66),
    ("06/20/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx03217", -31.00),
    ("06/23/2025", "GOOGLE ACCTVERIFY Richmond Taylo", 0.21),
    ("06/23/2025", "Rocket Money Premium ROCKET MONEY I ST-W7G9P9E6C5Y6", -3.29),
    ("06/23/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx87151", -25.00),
    ("06/23/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx77128", -65.90),
    ("06/23/2025", "MONTHLY FEE MONTHLY FEE", -8.00),
    ("06/25/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx83187", -100.00),
    ("06/30/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER EATS", -4.00),
    ("06/30/2025", "PAYPAL INST XFER RICHMOND TAYLO UBER EATS", -19.69),
    ("06/30/2025", "PAYPAL INST XFER RICHMOND TAYLO LINKEDIN", -131.69),
    ("06/30/2025", "NORTHWEST FCU BILLPAY RICHMOND B TAY", -485.40),
    ("07/01/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx56591", -20.00),
    ("07/01/2025", "Ludlam OP RENT Richmond Taylo 242079195", -2103.00),
    ("07/02/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx87618", -20.32),
    ("07/02/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx86354", -29.82),
    ("07/02/2025", "ZELLE DEBIT TO VICTOR UMAN REF# 518300B0IEPD", -200.00),
    ("07/03/2025", "DRVN PAYROLL RICHMOND B TAY", 2335.64),
    ("07/03/2025", "FREEDOM MTG PYMTS RICHMOND B TAY xxxxxx2242", -2666.10),
    ("07/07/2025", "PAYPAL INST XFER RICHMOND TAYLO APPLE.COM BILL", -0.99),
    ("07/07/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("07/07/2025", "PAYPAL INST XFER RICHMOND TAYLO GAMINGFUNDS", -20.00),
    ("07/07/2025", "VENMO PAYMENT RICHMOND TAYLO xxxxxxxx99652", -26.25),
    ("07/07/2025", "CHASE CREDIT CRD EPAY RICHMOND B TAY xxxxxx6997", -83.97),
    ("07/07/2025", "AMEX EPAYMENT ACH PMT RICHMOND TAYLO M3708", -1179.47),
]


def categorize(desc):
    d = desc.upper()
    if "DRVN PAYROLL" in d:
        return ("Business - Income", "Business")
    if "STRIPE TRANSFER" in d:
        return ("Business - Income", "Business")
    if "OPENAI" in d:
        return ("Business - R&D Software", "Business")
    if "PADDLE.COM" in d:
        return ("Business - Software/Tools", "Business")
    if "HOSTINGER INTERN" in d:
        return ("Business - Software/Tools", "Business")
    if "LINKEDIN" in d:
        return ("Business - Marketing", "Business")
    if "VENMO CASHOUT" in d:
        return ("Personal - Income", "Personal")
    if "CASH APP" in d:
        return ("Personal - Income", "Personal")
    if "PAYPAL TRANSFER" in d:
        return ("Personal - Income", "Personal")
    if "GOOGLE ACCTVERIFY" in d:
        return ("Personal - Income", "Personal")
    if "LUDLAM OP RENT" in d:
        return ("Personal - Housing", "Personal")
    if "FREEDOM M" in d:
        return ("Personal - Housing", "Personal")
    if "FPL" in d or "FLORIDA POWER" in d:
        return ("Personal - Utilities", "Personal")
    if "WOODS AT MONTICE" in d:
        return ("Personal - Utilities", "Personal")
    if "APPLE.COM BILL" in d:
        return ("Personal - Bills/Subscriptions", "Personal")
    if "ROCKET MONEY" in d:
        return ("Personal - Bills/Subscriptions", "Personal")
    if "MONTHLY FEE" in d:
        return ("Personal - Bills/Subscriptions", "Personal")
    if "AMEX EPAYMENT" in d:
        return ("Personal - Credit Card Payment", "Personal")
    if "CHASE CREDIT CRD" in d:
        return ("Personal - Credit Card Payment", "Personal")
    if "NORTHWEST FCU BILLPAY" in d:
        return ("Personal - Credit Card Payment", "Personal")
    if "VENMO PAYMENT" in d:
        return ("Personal - Transfers", "Personal")
    if "ZELLE DEBIT" in d:
        return ("Personal - Transfers", "Personal")
    if "GAMINGFUNDS" in d:
        return ("Personal - Gaming", "Personal")
    # UBER EATS must come before UBER
    if "UBER EATS" in d:
        return ("Personal - Transportation", "Personal")
    if "UBER" in d:
        return ("Personal - Transportation", "Personal")
    if "VUDU LLC" in d:
        return ("Personal - Entertainment", "Personal")
    return ("Uncategorized", "Unknown")


# Build rows
new_rows = []
for date_str, desc, amount in raw_txns:
    cat, biz_personal = categorize(desc)
    amt_str = f"{amount:.2f}"

    # Check for duplicate
    key = (date_str, desc, amt_str)
    if key in existing_set:
        print(f"SKIP duplicate: {key}")
        continue

    new_rows.append([date_str, desc, amt_str, cat, biz_personal])

print(f"\nNew rows to append: {len(new_rows)}")

if new_rows:
    # Append rows
    ws.append_rows(new_rows, value_input_option="USER_ENTERED")
    print("Rows appended successfully.")

    # Now re-sort entire sheet by date (column A)
    all_data = ws.get_all_values()
    header = all_data[0]
    data_rows = all_data[1:]

    def parse_date(row):
        try:
            return datetime.strptime(row[0], "%m/%d/%Y")
        except Exception:
            try:
                return datetime.strptime(row[0], "%m/%d/%y")
            except Exception:
                return datetime.max

    data_rows.sort(key=parse_date)

    sorted_all = [header] + data_rows
    ws.update(sorted_all, "A1")
    print(f"Sheet sorted. Total rows (incl header): {len(sorted_all)}")
else:
    print("No new rows to add.")

print("Done!")
