import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

class Database:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                normalized_title TEXT,
                description TEXT,
                date TEXT NOT NULL,
                time TEXT,
                location TEXT,
                url TEXT NOT NULL,
                source_url TEXT NOT NULL,
                is_virtual BOOLEAN DEFAULT FALSE,
                requires_registration BOOLEAN DEFAULT FALSE,
                categories TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add normalized_title column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE events ADD COLUMN normalized_title TEXT')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Create computing_events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS computing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                normalized_title TEXT,
                description TEXT,
                date TEXT NOT NULL,
                time TEXT,
                location TEXT,
                url TEXT NOT NULL,
                source_url TEXT NOT NULL,
                is_virtual BOOLEAN DEFAULT FALSE,
                requires_registration BOOLEAN DEFAULT FALSE,
                categories TEXT DEFAULT '[]',
                host TEXT DEFAULT 'Other',
                cost_type TEXT DEFAULT 'Unknown',
                source TEXT DEFAULT 'Unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add source column if it doesn't exist (for existing databases)
        cursor.execute('''
            SELECT COUNT(*) FROM pragma_table_info('computing_events') 
            WHERE name='source'
        ''')
        has_source = cursor.fetchone()[0] == 1
        if not has_source:
            cursor.execute('ALTER TABLE computing_events ADD COLUMN source TEXT DEFAULT "Unknown"')
        
        # Create scraping_log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                status TEXT NOT NULL,
                events_found INTEGER DEFAULT 0,
                error_message TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create indexes for better performance
        self.create_indexes()
    
    def add_event(self, event: Dict[str, Any]) -> int:
        """Add a new event to the database with enhanced duplicate detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check for duplicates based on multiple criteria
            title = event.get('title', '').strip()
            date = event.get('date', '')
            source_url = event.get('source_url', '')
            event_url = event.get('url', '')
            
            # Create a normalized title for better duplicate detection
            normalized_title = self.normalize_title(title)
            
            # Check for exact duplicates first
            cursor.execute('''
                SELECT id FROM events 
                WHERE normalized_title = ? AND date = ? AND source_url = ?
            ''', (normalized_title, date, source_url))
            
            existing_event = cursor.fetchone()
            
            if existing_event:
                # Update existing event instead of creating duplicate
                event_id = existing_event[0]
                # Determine institution from source URL
                institution = self.get_institution_from_url(source_url)
                
                cursor.execute('''
                    UPDATE events 
                    SET description = ?, time = ?, location = ?, url = ?, 
                        is_virtual = ?, requires_registration = ?, 
                        categories = ?, institution = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    event.get('description', ''),
                    event.get('time', ''),
                    event.get('location', ''),
                    event.get('url', ''),
                    event.get('is_virtual', False),
                    event.get('requires_registration', False),
                    json.dumps(event.get('categories', [])),
                    institution,
                    datetime.now().isoformat(),
                    event_id
                ))
                conn.commit()
                return event_id
            
            # Check for similar events (same date, similar title, same source)
            if normalized_title:
                cursor.execute('''
                    SELECT id, title, url FROM events 
                    WHERE date = ? AND source_url = ? AND normalized_title LIKE ?
                ''', (date, source_url, f'%{normalized_title[:20]}%'))
                
                similar_events = cursor.fetchall()
                
                for similar_id, similar_title, similar_url in similar_events:
                    # Check if URLs are similar (might be the same event with different URLs)
                    if self.urls_are_similar(event_url, similar_url):
                        # Update existing event
                        # Determine institution from source URL
                        institution = self.get_institution_from_url(source_url)
                        
                        cursor.execute('''
                            UPDATE events 
                            SET title = ?, description = ?, time = ?, location = ?, url = ?, 
                                is_virtual = ?, requires_registration = ?, 
                                categories = ?, institution = ?, updated_at = ?
                            WHERE id = ?
                        ''', (
                            title,
                            event.get('description', ''),
                            event.get('time', ''),
                            event.get('location', ''),
                            event_url,
                            event.get('is_virtual', False),
                            event.get('requires_registration', False),
                            json.dumps(event.get('categories', [])),
                            institution,
                            datetime.now().isoformat(),
                            similar_id
                        ))
                        conn.commit()
                        return similar_id
            
            # Determine institution from source URL
            institution = self.get_institution_from_url(source_url)
            
            # Insert new event
            cursor.execute('''
                INSERT INTO events 
                (title, normalized_title, description, date, time, location, url, source_url, 
                 is_virtual, requires_registration, categories, institution, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                normalized_title,
                event.get('description', ''),
                date,
                event.get('time', ''),
                event.get('location', ''),
                event_url,
                source_url,
                event.get('is_virtual', False),
                event.get('requires_registration', False),
                json.dumps(event.get('categories', [])),
                institution,
                datetime.now().isoformat()
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            return event_id
        finally:
            conn.close()
    
    def get_institution_from_url(self, source_url: str) -> str:
        """Determine institution from source URL"""
        if not source_url:
            return 'Unknown'
        
        # Institution mapping based on source URLs
        institution_mapping = {
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
        
        source_lower = source_url.lower()
        
        # Check each mapping
        for domain_key, institution in institution_mapping.items():
            if domain_key in source_lower:
                return institution
        
        return 'Others'
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for better duplicate detection"""
        if not title:
            return ""
        
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove common punctuation and extra spaces
        normalized = normalized.replace('-', ' ').replace('_', ' ')
        normalized = re.sub(r'[^\w\s]', ' ', normalized)  # Remove all punctuation
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Remove common words that don't help with identification
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'from', 'into', 'during', 'including', 'until', 'against', 'among', 'throughout', 'despite',
            'towards', 'upon', 'concerning', 'about', 'like', 'through', 'over', 'before', 'between',
            'after', 'since', 'without', 'under', 'within', 'along', 'following', 'across', 'behind',
            'beyond', 'plus', 'except', 'but', 'up', 'out', 'off', 'above', 'below', 'near', 'far',
            'event', 'events', 'seminar', 'colloquium', 'talk', 'lecture', 'presentation', 'workshop',
            'conference', 'meeting', 'session', 'series', 'program', 'webinar', 'symposium'
        }
        
        words = normalized.split()
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Sort words to make comparison more consistent
        words.sort()
        
        return ' '.join(words)
    
    def get_events(self, days_ahead: int = 365) -> List[Dict[str, Any]]:
        """Get all events from today onwards with optimized query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate date range
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        # Optimized query with indexing hints
        cursor.execute('''
            SELECT id, title, description, date, time, location, url, source_url,
                   is_virtual, requires_registration, categories, institution, created_at
            FROM events 
            WHERE date >= ? AND date <= ?
            ORDER BY date ASC, time ASC
            LIMIT 1000
        ''', (today.isoformat(), future_date.isoformat()))
        
        events = []
        for row in cursor.fetchall():
            event = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'date': row[3],
                'time': row[4],
                'location': row[5],
                'url': row[6],
                'source_url': row[7],
                'is_virtual': bool(row[8]),
                'requires_registration': bool(row[9]),
                'categories': self._parse_categories(row[10]) if row[10] else [],
                'institution': row[11] or 'Others',
                'created_at': row[12]
            }
            events.append(event)
        
        conn.close()
        return events
    
    def _parse_categories(self, categories_str):
        """Parse categories string that might be in various formats"""
        if not categories_str:
            return []
        
        try:
            # Try to parse as JSON first
            return json.loads(categories_str)
        except json.JSONDecodeError:
            try:
                # Try to parse as Python literal (handles single quotes)
                import ast
                return ast.literal_eval(categories_str)
            except (ValueError, SyntaxError):
                # If all else fails, return empty list
                return []
    
    def create_indexes(self):
        """Create database indexes for better performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_normalized ON events(normalized_title)')
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
        finally:
            conn.close()
    
    def update_event_categories(self, event_id: int, categories: List[str]):
        """Update categories for a specific event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE events 
            SET categories = ?, updated_at = ?
            WHERE id = ?
        ''', (json.dumps(categories), datetime.now().isoformat(), event_id))
        
        conn.commit()
        conn.close()
    
    def log_scraping(self, source_url: str, status: str, events_found: int = 0, error_message: str = None):
        """Log scraping activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_log (source_url, status, events_found, error_message)
            VALUES (?, ?, ?, ?)
        ''', (source_url, status, events_found, error_message))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total events
        cursor.execute('SELECT COUNT(*) FROM events')
        total_events = cursor.fetchone()[0]
        
        # Events today and this week
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        cursor.execute('SELECT COUNT(*) FROM events WHERE date = ?', (today.isoformat(),))
        today_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM events WHERE date BETWEEN ? AND ?', 
                      (week_start.isoformat(), week_end.isoformat()))
        week_events = cursor.fetchone()[0]
        
        # Last scraping activity
        cursor.execute('''
            SELECT source_url, status, events_found, scraped_at 
            FROM scraping_log 
            ORDER BY scraped_at DESC 
            LIMIT 10
        ''')
        recent_scrapes = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_events': total_events,
            'today_events': today_events,
            'week_events': week_events,
            'recent_scrapes': recent_scrapes
        }
    
    def cleanup_old_events(self, days_to_keep: int = 30):
        """Remove events older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
        
        cursor.execute('DELETE FROM events WHERE date < ?', (cutoff_date.isoformat(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count 
    
    def add_computing_event(self, event: Dict[str, Any]) -> int:
        """Add a new computing event to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check for duplicates
            title = event.get('title', '').strip()
            date = event.get('date', '')
            source_url = event.get('source_url', '')
            
            normalized_title = self.normalize_title(title)
            
            # Check for exact duplicates
            cursor.execute('''
                SELECT id FROM computing_events 
                WHERE normalized_title = ? AND date = ? AND source_url = ?
            ''', (normalized_title, date, source_url))
            
            existing_event = cursor.fetchone()
            
            if existing_event:
                # Update existing event
                event_id = existing_event[0]
                cursor.execute('''
                    UPDATE computing_events 
                    SET description = ?, time = ?, location = ?, url = ?, 
                        is_virtual = ?, requires_registration = ?, 
                        categories = ?, host = ?, cost_type = ?, source = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    event.get('description', ''),
                    event.get('time', ''),
                    event.get('location', ''),
                    event.get('url', ''),
                    event.get('is_virtual', False),
                    event.get('requires_registration', False),
                    json.dumps(event.get('categories', [])),
                    event.get('host', 'Other'),
                    event.get('cost_type', 'Unknown'),
                    event.get('source', 'Unknown'),
                    datetime.now().isoformat(),
                    event_id
                ))
                conn.commit()
                return event_id
            
            # Insert new event
            cursor.execute('''
                INSERT INTO computing_events 
                (title, normalized_title, description, date, time, location, url, source_url, 
                 is_virtual, requires_registration, categories, host, cost_type, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                normalized_title,
                event.get('description', ''),
                date,
                event.get('time', ''),
                event.get('location', ''),
                event.get('url', ''),
                source_url,
                event.get('is_virtual', False),
                event.get('requires_registration', False),
                json.dumps(event.get('categories', [])),
                event.get('host', 'Other'),
                event.get('cost_type', 'Unknown'),
                event.get('source', 'Unknown'),
                datetime.now().isoformat()
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            return event_id
        finally:
            conn.close()
    
    def get_computing_events(self, days_ahead: int = 365) -> List[Dict[str, Any]]:
        """Get all computing events from today onwards"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate date range
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        cursor.execute('''
            SELECT id, title, description, date, time, location, url, source_url,
                   is_virtual, requires_registration, categories, host, cost_type, source, created_at
            FROM computing_events 
            WHERE date >= ? AND date <= ? AND date LIKE '____-__-__'
            ORDER BY date ASC, time ASC
            LIMIT 1000
        ''', (today.isoformat(), future_date.isoformat()))
        
        events = []
        for row in cursor.fetchall():
            event = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'date': row[3],
                'time': row[4],
                'location': row[5],
                'url': row[6],
                'source_url': row[7],
                'is_virtual': bool(row[8]),
                'requires_registration': bool(row[9]),
                'categories': self._parse_categories(row[10]) if row[10] else [],
                'host': row[11] or 'Other',
                'cost_type': row[12] or 'Unknown',
                'source': row[13] or 'Unknown',
                'created_at': row[14]
            }
            events.append(event)
        
        conn.close()
        return events
    
    def get_computing_event_stats(self) -> Dict[str, Any]:
        """Get statistics for computing events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total events
        cursor.execute('SELECT COUNT(*) FROM computing_events')
        total_events = cursor.fetchone()[0]
        
        # Events by cost type
        cursor.execute('SELECT cost_type, COUNT(*) FROM computing_events GROUP BY cost_type')
        cost_type_stats = dict(cursor.fetchall())
        
        # Events by host
        cursor.execute('SELECT host, COUNT(*) FROM computing_events GROUP BY host ORDER BY COUNT(*) DESC LIMIT 10')
        host_stats = dict(cursor.fetchall())
        
        # Events by source
        cursor.execute('SELECT source, COUNT(*) FROM computing_events GROUP BY source ORDER BY COUNT(*) DESC')
        source_stats = dict(cursor.fetchall())
        
        # Events today and this week
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        cursor.execute('SELECT COUNT(*) FROM computing_events WHERE date = ?', (today.isoformat(),))
        today_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM computing_events WHERE date BETWEEN ? AND ?', 
                      (week_start.isoformat(), week_end.isoformat()))
        week_events = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_events': total_events,
            'today_events': today_events,
            'week_events': week_events,
            'cost_type_stats': cost_type_stats,
            'host_stats': host_stats,
            'source_stats': source_stats
        }

    def urls_are_similar(self, url1: str, url2: str) -> bool:
        """Check if two URLs are similar (might be the same event)"""
        if not url1 or not url2:
            return False
        
        # Parse URLs
        try:
            from urllib.parse import urlparse
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            
            # Same domain and similar path
            if parsed1.netloc == parsed2.netloc:
                path1 = parsed1.path.lower()
                path2 = parsed2.path.lower()
                
                # Check if paths are similar (one might be a redirect or variation)
                if path1 == path2:
                    return True
                
                # Check if one path contains the other
                if path1 in path2 or path2 in path1:
                    return True
                
                # Check if they share common path segments
                segments1 = [s for s in path1.split('/') if s]
                segments2 = [s for s in path2.split('/') if s]
                
                if segments1 and segments2:
                    # If they share the last segment (often the event ID)
                    if segments1[-1] == segments2[-1]:
                        return True
                    
                    # If they share multiple segments
                    common_segments = set(segments1) & set(segments2)
                    if len(common_segments) >= 2:
                        return True
            
            return False
        except Exception:
            return False 