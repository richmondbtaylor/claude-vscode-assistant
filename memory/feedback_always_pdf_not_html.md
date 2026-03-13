---
name: Always output PDF, never HTML
description: When creating pitches, presentations, or any deliverable file, always produce a PDF — never an HTML file or .md file
type: feedback
---

When generating any deliverable (pitch decks, presentations, reports, etc.), always produce a **PDF** as the final output format.

- Never deliver an `.html` file as the end product
- Never deliver a `.md` file as the end product
- HTML can be used as an intermediate step (to convert to PDF via Playwright), but the file given to the user must be `.pdf`
- After generating the PDF, always upload it to Google Drive using `python C:/Users/richm/.claude/scripts/generate_pdf.py "<html_file>"`
