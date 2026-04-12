"""
One-time interactive setup for TARSEN's persistent X (Twitter) browser session.

Run this ONCE before flipping --live. It opens a Chromium window pointed at
x.com/login. You log in (with 2FA if needed). Once you see the home timeline,
press ENTER in this terminal and the script saves the persistent context to
skills/tarsen/x_session/.

After this, --live mode will reuse that session without asking for credentials.
"""
import sys
from playwright.sync_api import sync_playwright

from config import X_SESSION_DIR


def main():
    X_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Opening Chromium with persistent context at: {X_SESSION_DIR}")
    print("Please log in to X (with 2FA if needed). When you see your home")
    print("timeline, come back here and press ENTER.")
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(X_SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()
        page.goto("https://x.com/login", wait_until="domcontentloaded")
        try:
            input("\nWhen logged in and the home timeline is visible, press ENTER to save and quit...\n")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)
        ctx.close()
    print("Session saved. You can now run: python main.py --live")


if __name__ == "__main__":
    main()
