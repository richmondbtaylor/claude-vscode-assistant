"""
One-time script to fill in missing categories in the Bishop AI expense sheet.
Uses gspread OAuth (same credentials as the bishop-research-agent).
First run will open a browser to authorize — after that it's cached.
"""
import gspread
import os

SHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
TABS = ["Bishop AI", "Prompt Anything", "Personal"]

# Use the same client_secret as the research agent
CREDS_PATH = os.path.expanduser(
    r"~\.claude\skills\bishop-research-agent"
    r"\client_secret_538050013679-2u4jsv7rglht96qkom62o3a70gcuimog.apps.googleusercontent.com.json"
)

CATEGORY_RULES = [
    (["claude", "chatgpt", "openai", "anthropic", "n8n", "notion", "adobe", "zapier",
      "github", "canva", "figma", "slack", "zoom", "dropbox", "mailchimp", "hubspot",
      "airtable", "linear", "vercel", "netlify", "aws", "azure", "google cloud",
      "digitalocean", "heroku", "twilio", "stripe", "loom", "typeform", "beehiiv",
      "convertkit", "activecampaign", "semrush", "ahrefs", "buffer", "hootsuite",
      "calendly", "descript", "riverside", "transistor", "buzzsprout", "kajabi",
      "teachable", "thinkific", "circle", "skool", "mighty networks", "gpt",
      "midjourney", "runway", "elevenlabs", "synthesia", "heygen"], "Software & Subscriptions"),

    (["meta ads", "facebook ads", "google ads", "linkedin ads", "twitter ads",
      "tiktok ads", "instagram ads", "sponsored", "99designs", "creative market",
      "envato", "shutterstock", "getty", "printing", "vistaprint", "moo"], "Advertising & Marketing"),

    (["starbucks", "dunkin", "mcdonald", "chipotle", "subway", "chick-fil-a",
      "doordash", "uber eats", "grubhub", "postmates", "instacart", "restaurant",
      "cafe", "coffee", "bar ", " bar", "grill", "pizza", "sushi", "taco", "burger",
      "diner", "bistro", "kitchen", "eatery", "food", "capital grille", "ruth's chris",
      "cheesecake factory", "olive garden", "applebee", "panera", "jersey mike",
      "jimmy john", "potbelly", "sweetgreen", "wingstop", "raising cane",
      "shake shack", "five guys", "whataburger", "in-n-out", "culver"], "Meals & Entertainment"),

    (["amazon", "staples", "office depot", "best buy", "costco", "walmart",
      "target", "b&h", "adorama", "newegg", "micro center", "apple store",
      "dell", "hp ", "logitech", "belkin", "anker", "monitor", "keyboard",
      "mouse", "headset", "webcam", "printer", "desk", "chair", "supplies"], "Office & Supplies"),

    (["upwork", "fiverr", "toptal", "contractor", "freelance", "consulting",
      "virtual assistant"], "Contractors & Freelancers"),

    (["airline", "delta", "united", "american airlines", "southwest", "spirit",
      "jetblue", "frontier", "alaska air", "lufthansa", "british airways",
      "hotel", "marriott", "hilton", "hyatt", "sheraton", "westin", "ihg",
      "holiday inn", "airbnb", "vrbo", "lyft", "hertz", "enterprise rental",
      "avis", "budget rental", "amtrak", "parking", "shell", "bp ", "chevron",
      "exxon", "speedway", "wawa", "7-eleven", "circle k"], "Travel"),

    (["udemy", "coursera", "skillshare", "linkedin learning", "masterclass",
      "pluralsight", "treehouse", "codecademy", "datacamp", "conference",
      "summit", "workshop", "seminar", "training", "audible", "barnes",
      "course", "bootcamp", "certification", "kindle"], "Education & Training"),
]

def infer_category(vendor: str) -> str:
    v = vendor.lower()
    for keywords, category in CATEGORY_RULES:
        for kw in keywords:
            if kw in v:
                return category
    return "Miscellaneous"

def find_column(headers: list, name: str) -> int | None:
    """Find column index by header name (case-insensitive)."""
    for i, h in enumerate(headers):
        if h.strip().lower() == name.lower():
            return i
    return None

def main():
    print("Connecting to Google Sheets...")
    print("(A browser may open for first-time authorization)\n")

    gc = gspread.oauth(credentials_filename=CREDS_PATH)
    spreadsheet = gc.open_by_key(SHEET_ID)

    total_filled = 0
    total_skipped = 0

    for tab_name in TABS:
        print(f"--- Tab: {tab_name} ---")
        try:
            ws = spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            print(f"  Tab '{tab_name}' not found, skipping.\n")
            continue

        all_values = ws.get_all_values()
        if not all_values:
            print(f"  Empty tab, skipping.\n")
            continue

        headers = all_values[0]
        vendor_col = find_column(headers, "Vendor")
        category_col = find_column(headers, "Category")

        if vendor_col is None or category_col is None:
            print(f"  Could not find Vendor or Category column. Headers found: {headers}")
            print(f"  Skipping.\n")
            continue

        updates = []
        for row_idx, row in enumerate(all_values[1:], start=2):  # 1-indexed, skip header
            vendor = row[vendor_col].strip() if vendor_col < len(row) else ""
            existing_category = row[category_col].strip() if category_col < len(row) else ""

            if not vendor:
                continue  # skip empty rows

            if existing_category:
                total_skipped += 1
                continue  # already has a category

            category = infer_category(vendor)
            # gspread uses A1 notation — category_col is 0-indexed, convert to letter
            col_letter = chr(ord('A') + category_col)
            cell = f"{col_letter}{row_idx}"
            updates.append({"range": cell, "values": [[category]]})
            print(f"  Row {row_idx}: '{vendor}' → {category}")

        if updates:
            ws.batch_update(updates)
            print(f"  Filled {len(updates)} categories.\n")
            total_filled += len(updates)
        else:
            print(f"  No empty categories found.\n")

    print(f"Done! Filled {total_filled} categories, skipped {total_skipped} already-filled rows.")

if __name__ == "__main__":
    main()
