"""
Setup script for Clawd Bot
Helps configure the bot with necessary credentials
"""

import os
import shutil


def create_env_file():
    """Create .env file from user input"""
    print("\n" + "="*60)
    print("CLAWD BOT SETUP")
    print("="*60 + "\n")

    print("Let's configure your bot. You'll need:")
    print("1. Anthropic API Key (from https://console.anthropic.com/)")
    print("2. LinkedIn email and password")
    print("3. WhatsApp phone number\n")

    # Get Anthropic API key
    anthropic_key = input("Enter your Anthropic API Key: ").strip()

    # Get LinkedIn credentials
    print("\n--- LinkedIn Credentials ---")
    linkedin_email = input("LinkedIn Email: ").strip()
    linkedin_password = input("LinkedIn Password: ").strip()

    # Get WhatsApp phone
    print("\n--- WhatsApp Configuration ---")
    whatsapp_phone = input("Your phone number (with country code, e.g., +1234567890): ").strip()

    # Bot configuration
    print("\n--- Bot Configuration ---")
    check_interval = input("Check interval in seconds (default: 60): ").strip() or "60"
    max_comments = input("Max comments per day (default: 20): ").strip() or "20"

    # Create .env content
    env_content = f"""# Anthropic API Key
ANTHROPIC_API_KEY={anthropic_key}

# LinkedIn Credentials
LINKEDIN_EMAIL={linkedin_email}
LINKEDIN_PASSWORD={linkedin_password}

# WhatsApp Configuration
WHATSAPP_PHONE={whatsapp_phone}

# Bot Configuration
CHECK_INTERVAL={check_interval}
MAX_COMMENTS_PER_DAY={max_comments}
"""

    # Write to .env file
    with open('.env', 'w') as f:
        f.write(env_content)

    print("\n✓ .env file created successfully!")


def install_dependencies():
    """Install required dependencies"""
    print("\n" + "="*60)
    print("Installing dependencies...")
    print("="*60 + "\n")

    import subprocess

    try:
        # Install Python packages
        print("Installing Python packages...")
        subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)

        # Install Playwright browsers
        print("\nInstalling Playwright browsers...")
        subprocess.run(['playwright', 'install', 'chromium'], check=True)

        print("\n✓ All dependencies installed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error installing dependencies: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ pip or playwright not found. Please install Python and pip first.")
        return False


def main():
    """Main setup function"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              CLAWD BOT - Setup Wizard                     ║
    ║                                                           ║
    ║  LinkedIn Auto-Commenter powered by Claude AI             ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Check if .env exists
    if os.path.exists('.env'):
        response = input(".env file already exists. Recreate it? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    # Create .env file
    create_env_file()

    # Ask about dependencies
    response = input("\nInstall dependencies now? (y/n): ")
    if response.lower() == 'y':
        if install_dependencies():
            print("\n" + "="*60)
            print("SETUP COMPLETE!")
            print("="*60)
            print("\nYou can now run the bot with:")
            print("  python main.py")
            print("\nFor testing individual components:")
            print("  python claude_generator.py   # Test Claude AI")
            print("  python linkedin_commenter.py # Test LinkedIn")
            print("  python whatsapp_monitor.py   # Test WhatsApp")
        else:
            print("\nPlease install dependencies manually:")
            print("  pip install -r requirements.txt")
            print("  playwright install chromium")
    else:
        print("\nRemember to install dependencies before running:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")


if __name__ == "__main__":
    main()
