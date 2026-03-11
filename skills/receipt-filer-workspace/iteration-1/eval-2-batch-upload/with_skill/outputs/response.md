# Receipt Filing — Batch Upload (3 Receipts)

Processing all three receipts independently, in order.

---

## Receipt 1 of 3: Amazon Order Confirmation

**Step 1 — Validate the file**
File received: PNG screenshot. Format is readable and valid.

**Step 2 — Extract receipt data**
Using vision/OCR to read the uploaded PNG:
- Date: March 5, 2026
- Vendor: Amazon
- Amount: $34.99

**Step 3 — Handle missing data**
All three fields are present and readable. No action needed.

**Step 4 — Format the destination**
Date formatted as: `2026-03-05`

**Step 5 — Locate the root folder**
`Bishop AI finances` found at the root of My Drive.

**Step 6 — Check for the date subfolder**
Searching inside `Bishop AI finances` for a folder named `2026-03-05`. No existing folder found — creating `2026-03-05` now.

**Step 7 — Rename the file**
Filename: `Amazon_34.99.png`

**Step 8 — Upload and confirm**

> Filed to **Bishop AI finances / 2026-03-05**
> File: `Amazon_34.99.png`
> [View in Google Drive](https://drive.google.com/simulated-link/Amazon_34.99.png)

---

## Receipt 2 of 3: Starbucks (first visit, March 7)

**Step 1 — Validate the file**
File received: JPG phone photo. Readable and valid.

**Step 2 — Extract receipt data**
- Date: March 7, 2026
- Vendor: Starbucks
- Amount: $8.75

**Step 4 — Format the destination**
Date formatted as: `2026-03-07`

**Step 6 — Check for the date subfolder**
No existing `2026-03-07` folder found — creating it now.

**Step 7 — Rename the file**
Filename: `Starbucks_8.75.jpg`

**Step 8 — Upload and confirm**

> Filed to **Bishop AI finances / 2026-03-07**
> File: `Starbucks_8.75.jpg`
> [View in Google Drive](https://drive.google.com/simulated-link/Starbucks_8.75.jpg)

---

## Receipt 3 of 3: Starbucks (second visit, March 7)

**Step 1 — Validate the file**
File received: JPG phone photo. Readable and valid.

**Step 2 — Extract receipt data**
- Date: March 7, 2026
- Vendor: Starbucks
- Amount: $6.50

**Step 4 — Format the destination**
Date formatted as: `2026-03-07`

**Step 6 — Check for the date subfolder**
Folder `2026-03-07` already exists (created during Receipt 2 processing) — reusing it. No duplicate folder created.

**Step 7 — Rename the file**
Filename: `Starbucks_6.50.jpg`

**Step 8 — Upload and confirm**

> Filed to **Bishop AI finances / 2026-03-07**
> File: `Starbucks_6.50.jpg`
> [View in Google Drive](https://drive.google.com/simulated-link/Starbucks_6.50.jpg)

---

## Batch Summary

| # | Vendor | Date | Amount | Filename | Folder |
|---|---|---|---|---|---|
| 1 | Amazon | 2026-03-05 | $34.99 | `Amazon_34.99.png` | `Bishop AI finances / 2026-03-05` |
| 2 | Starbucks | 2026-03-07 | $8.75 | `Starbucks_8.75.jpg` | `Bishop AI finances / 2026-03-07` |
| 3 | Starbucks | 2026-03-07 | $6.50 | `Starbucks_6.50.jpg` | `Bishop AI finances / 2026-03-07` |

Folders created: 2 (`2026-03-05`, `2026-03-07`). The `2026-03-07` folder was reused for the second Starbucks receipt — no duplicate was created.
