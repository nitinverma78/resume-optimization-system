#!/usr/bin/env python3
"""
Interactive LinkedIn authentication setup.
Opens a browser window for you to login, then saves the session state.
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent
auth_file = ROOT / "data" / ".linkedin_auth.json"

print("🌐 Opening LinkedIn login page...")
print("👤 Please sign in to LinkedIn when the browser opens")
print("⏰ You have 5 minutes to complete the login")

with sync_playwright() as p:
    # Launch in HEADED mode (visible browser)
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # Navigate to LinkedIn
    page.goto("https://www.linkedin.com/login")
    
    print("\n✋ Waiting for you to login...")
    print("   When you're done, the browser will close automatically")
    
    # Wait for redirect to feed (indicates successful login)
    try:
        page.wait_for_url("**/feed/**", timeout=300000)  # 5 minutes
        print("✅ Login detected!")
    except:
        print("⏰ Timeout - checking if logged in anyway...")
    
    # Save session state
    auth_file.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(auth_file))
    
    print(f"💾 Session state saved to: {auth_file}")
    
    browser.close()

print("\n🎉 Authentication setup complete!")
print("   You can now run the ingestion script with authenticated access")
