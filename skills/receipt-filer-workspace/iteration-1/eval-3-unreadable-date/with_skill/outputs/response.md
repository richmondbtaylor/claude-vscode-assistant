# Receipt Filing Attempt — Unreadable Date

## File Received

A JPG image described as a crumpled receipt photo has been submitted for filing.

---

## Step 1: Validate the File

The file is a JPG image — a valid format for receipt processing. The file appears readable (not corrupted), so processing continues.

---

## Step 2: Extract Receipt Data

Using vision/OCR to read the receipt:

- **Date** — Unreadable. The date field is blurry due to the crumpled condition of the receipt. No date can be extracted with confidence.
- **Vendor name** — FedEx Office (visible/provided)
- **Amount** — $22.13 (visible/provided)

---

## Step 3: Handle Missing Data

The date is unreadable. Per the skill's instructions, processing stops here and the user is asked to provide the date manually.

---

## Response to User

I couldn't read the date on this receipt. Please type the date in **YYYY-MM-DD format** so I can file it correctly.

Once you provide the date, I'll file the receipt as:

- **Folder:** `Bishop AI finances / YYYY-MM-DD`
- **Filename:** `FedEx_Office_22.13.jpg`

---

## What Happens Next (once date is provided)

When the user supplies the date (e.g., `2026-02-14`), the skill will resume at Step 4:

1. Format the destination — Use the provided date as the subfolder name
2. Locate root folder — Find `Bishop AI finances` in My Drive
3. Check/create date subfolder — Look for the date folder; create it if it doesn't exist
4. Rename the file — `FedEx_Office_22.13.jpg`
5. Upload and confirm — Upload to the date subfolder and provide a confirmation with folder path and Drive link

---

## Summary

Filing was paused at the date extraction step. The skill does not guess or substitute today's date — it requires the actual receipt date from the user before proceeding. This ensures receipts are filed accurately and not misfiled under an incorrect date.
