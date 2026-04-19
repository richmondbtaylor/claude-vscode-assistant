"""
Convert an HTML file to PDF using Playwright, then upload to Google Drive.

Usage:
    python generate_pdf.py <html_file_path> [drive_folder_id]

If drive_folder_id is omitted, uploads to the default Bishop AI presentations folder.
Prints the Google Drive webViewLink on success.
"""
import sys
import subprocess
from pathlib import Path

DEFAULT_FOLDER_ID = "1LhCsKe9poKHFdXYfOFmBnX4kPeIpH8AZ"
UPLOAD_SCRIPT = Path(__file__).parent / "upload_gdrive.py"


def html_to_pdf(html_path: Path, landscape: bool = False) -> Path:
    from playwright.sync_api import sync_playwright

    pdf_path = html_path.with_suffix(".pdf")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        if landscape:
            # 16:9 presentation slide dimensions (1280x720 @ 96dpi)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                width="13.33in",
                height="7.5in",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        else:
            page = browser.new_page()
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "20mm", "bottom": "20mm", "left": "16mm", "right": "16mm"},
            )
        browser.close()

    return pdf_path


def upload_to_drive(pdf_path: Path, folder_id: str) -> str:
    result = subprocess.run(
        [sys.executable, str(UPLOAD_SCRIPT), str(pdf_path), folder_id],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Upload error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf.py <html_file> [drive_folder_id]")
        sys.exit(1)

    # Strip flags; remaining positional args are: html_file [folder_id]
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    landscape  = "--landscape" in sys.argv

    html_file = Path(positional[0])
    folder_id = positional[1] if len(positional) > 1 else DEFAULT_FOLDER_ID

    if not html_file.exists():
        print(f"ERROR: File not found: {html_file}", file=sys.stderr)
        sys.exit(1)
    print(f"Converting {html_file.name} to PDF...")
    pdf_file = html_to_pdf(html_file, landscape=landscape)
    print(f"PDF created: {pdf_file}")

    print("Uploading to Google Drive...")
    link = upload_to_drive(pdf_file, folder_id)
    print(f"Done: {link}")
