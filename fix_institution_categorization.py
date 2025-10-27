#!/usr/bin/env python3
"""
Script to fix institution categorization for events.
This script properly categorizes events by institution based on their source URLs.
"""

import sqlite3


class InstitutionCategorizationFixer:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        
        # Institution mapping based on source URLs
        self.institution_mapping = {
            'mit.edu': 'MIT',
            'broadinstitute': 'MIT',
            'iaifi.org': 'MIT',
            'ericandwendyschmidtcenter.org': 'MIT',
            'harvard': 'Harvard',
            'bu.edu': 'BU',
            'brown.edu': 'Brown',
            'northeastern.edu': 'Northeastern',
            'tufts.edu': 'Tufts',
            'brandeis.edu': 'Brandeis',
            'wellesley.edu': 'Wellesley',
            'bc.edu': 'Boston College',
            'simmons.edu': 'Simmons',
            'emerson.edu': 'Emerson',
            'berklee.edu': 'Berklee',
            'mgh.harvard.edu': 'Harvard',
            'dfci.harvard.edu': 'Harvard',
            'partners.org': 'Harvard',
            'childrenshospital.org': 'Harvard',
            'brighamandwomens.org': 'Harvard',
            'bwh.harvard.edu': 'Harvard',
            'massgeneral.org': 'Harvard',
            'hms.harvard.edu': 'Harvard',
            'hsph.harvard.edu': 'Harvard',
            'seas.harvard.edu': 'Harvard',
            'fas.harvard.edu': 'Harvard',
            'gsd.harvard.edu': 'Harvard',
            'hbs.harvard.edu': 'Harvard',
            'law.harvard.edu': 'Harvard',
            'ksg.harvard.edu': 'Harvard',
            'kennedy.harvard.edu': 'Harvard'
        }
    
    def get_institution_from_url(self, source_url):
        """Determine institution from source URL"""
        if not source_url:
            return 'Unknown'
        
        source_lower = source_url.lower()
        
        # Check each mapping
        for domain_key, institution in self.institution_mapping.items():
            if domain_key in source_lower:
                return institution
        
        return 'Others'
    
    def fix_institution_categorization(self):
        """Fix institution categorization for all events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🔧 Fixing institution categorization...")
        
        # Get all events
        cursor.execute('SELECT id, title, source_url, institution FROM events ORDER BY id')
        all_events = cursor.fetchall()
        
        updated_count = 0
        
        for event_id, title, source_url, current_institution in all_events:
            # Determine correct institution
            correct_institution = self.get_institution_from_url(source_url)
            
            # Update if different
            if current_institution != correct_institution:
                cursor.execute('''
                    UPDATE events 
                    SET institution = ?, updated_at = ?
                    WHERE id = ?
                ''', (correct_institution, 
                      sqlite3.datetime.datetime.now().isoformat(),
                      event_id))
                
                updated_count += 1
                print(f"✅ Updated: '{title}'")
                print(f"   Source: {source_url}")
                print(f"   Institution: {current_institution} → {correct_institution}")
                print()
        
        conn.commit()
        conn.close()
        
        print(f"🎉 Updated {updated_count} events!")
        
        # Show final statistics
        self.show_stats()
    
    def show_stats(self):
        """Show final statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 FINAL INSTITUTION STATISTICS:")
        cursor.execute('SELECT institution, COUNT(*) FROM events GROUP BY institution ORDER BY COUNT(*) DESC')
        institution_counts = cursor.fetchall()
        
        for institution, count in institution_counts:
            print(f"   {institution}: {count} events")
        
        print(f"\n📊 EVENTS BY SOURCE AND INSTITUTION:")
        cursor.execute('''
            SELECT source_url, institution, COUNT(*) 
            FROM events 
            GROUP BY source_url, institution 
            ORDER BY source_url, COUNT(*) DESC
        ''')
        source_institution_counts = cursor.fetchall()
        
        for source_url, institution, count in source_institution_counts:
            print(f"   {source_url}")
            print(f"     {institution}: {count} events")
        
        conn.close()
    
    def add_missing_institution_column(self):
        """Add institution column if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('ALTER TABLE events ADD COLUMN institution TEXT')
            print("✅ Added institution column to events table")
        except sqlite3.OperationalError:
            print("ℹ️  Institution column already exists")
        
        conn.commit()
        conn.close()


def main():
    """Main function"""
    print("🔧 Institution Categorization Fixer")
    print("=" * 50)
    
    fixer = InstitutionCategorizationFixer()
    fixer.add_missing_institution_column()
    fixer.fix_institution_categorization()


if __name__ == "__main__":
    main()


