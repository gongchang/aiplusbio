#!/usr/bin/env python3
"""
Simple script to demonstrate adding a new website to the monitoring list.
This shows how you can add new URLs without changing any code.
"""

def add_new_website(url, description=""):
    """Add a new website to the monitoring list"""
    
    print(f"🌐 Adding new website: {url}")
    if description:
        print(f"📝 Description: {description}")
    
    # Read current websites
    try:
        with open('websites_to_watch.txt', 'r') as f:
            current_websites = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        current_websites = []
    
    # Check if website is already in the list
    if url in current_websites:
        print("⚠️  Website is already in the monitoring list!")
        return False
    
    # Add the new website
    with open('websites_to_watch.txt', 'a') as f:
        f.write(f"\n# {description}\n" if description else "\n")
        f.write(f"{url}\n")
    
    print(f"✅ Successfully added {url} to websites_to_watch.txt")
    print(f"📊 Total websites now being monitored: {len(current_websites) + 1}")
    print("\n💡 The system will automatically pick up this new website on the next scrape!")
    
    return True

def show_current_websites():
    """Show all currently monitored websites"""
    print("\n📋 Currently monitored websites:")
    print("-" * 50)
    
    try:
        with open('websites_to_watch.txt', 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    print(f"{i:2d}. {line}")
    except FileNotFoundError:
        print("No websites file found.")
    
    print("-" * 50)

if __name__ == '__main__':
    print("🚀 Website Addition Demo")
    print("=" * 50)
    
    # Show current websites
    show_current_websites()
    
    # Example: Add a new website (commented out to avoid actually adding it)
    # Uncomment the line below to actually add a website
    # add_new_website("https://example-new-events.com/calendar", "Example new events calendar")
    
    print("\n💡 To add a new website:")
    print("1. Edit 'websites_to_watch.txt'")
    print("2. Add the URL on a new line")
    print("3. Save the file")
    print("4. The system will automatically detect it!")
    
    print("\n🎯 Example websites you might want to add:")
    print("- https://events.mit.edu/")
    print("- https://calendar.harvard.edu/")
    print("- https://events.brown.edu/")
    print("- https://events.columbia.edu/")
