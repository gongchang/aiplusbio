#!/usr/bin/env python3
"""
Install Selenium and Chrome WebDriver for JavaScript rendering
"""

import subprocess
import sys
import os

def install_selenium():
    """Install Selenium package"""
    print("📦 Installing Selenium...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        print("✅ Selenium installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Selenium: {e}")
        return False

def check_chrome_installed():
    """Check if Chrome is installed"""
    print("🔍 Checking for Chrome browser...")
    
    # Common Chrome paths
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/google-chrome-stable",  # Linux
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"  # Windows
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at: {path}")
            return path
    
    print("❌ Chrome not found in common locations")
    print("Please install Google Chrome from: https://www.google.com/chrome/")
    return None

def install_chromedriver():
    """Install ChromeDriver using webdriver-manager"""
    print("📦 Installing webdriver-manager...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
        print("✅ webdriver-manager installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install webdriver-manager: {e}")
        return False

def test_selenium_setup():
    """Test if Selenium setup works"""
    print("🧪 Testing Selenium setup...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test with a simple page
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"✅ Selenium test successful! Page title: {title}")
        return True
        
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        return False

def main():
    """Main installation function"""
    print("🚀 Setting up Selenium for JavaScript Rendering")
    print("=" * 50)
    
    # Check Chrome
    chrome_path = check_chrome_installed()
    if not chrome_path:
        print("\n❌ Please install Google Chrome first")
        return False
    
    # Install Selenium
    if not install_selenium():
        return False
    
    # Install webdriver-manager
    if not install_chromedriver():
        return False
    
    # Test setup
    if not test_selenium_setup():
        return False
    
    print("\n🎉 Selenium setup complete!")
    print("You can now scrape JavaScript-heavy websites")
    return True

if __name__ == "__main__":
    main()










