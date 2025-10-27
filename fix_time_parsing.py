#!/usr/bin/env python3

import re
import sqlite3


def normalize_time(raw: str) -> str:
    """Normalize a raw time string to canonical 'H:MM AM/PM'.
    Returns empty string if nothing can be inferred.
    Heuristics are biased for local Boston academic events.
    """
    if not raw:
        return ''
    s = raw.strip()
    if not s:
        return ''

    # Normalize dashes/parentheses/timezone notes
    s = re.sub(r'[\u2013\u2014–—]', '-', s)
    s = re.sub(r'\((?:[^()]*?)\)', ' ', s)
    s = re.sub(r'\b(ET|EST|EDT|Eastern Time|Eastern|Boston Time)\b', ' ', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+', ' ', s).strip()

    # Use first part if a range
    if '-' in s:
        s = s.split('-')[0].strip()

    candidates = []

    # 12-hour with am/pm '2:30 PM', '2 PM'
    for m in re.finditer(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', s, flags=re.IGNORECASE):
        h = int(m.group(1))
        mnt = int(m.group(2) or '0')
        ampm = m.group(3).upper()
        if h == 12:
            h24 = 0
        else:
            h24 = h
        if ampm == 'PM':
            h24 += 12
        candidates.append((h24, mnt))

    # attached '2pm', '1030am'
    for m in re.finditer(r'\b(\d{1,2})(\d{2})?(am|pm)\b', s, flags=re.IGNORECASE):
        h = int(m.group(1))
        mnt = int(m.group(2) or '0')
        ampm = m.group(3).upper()
        if h == 12:
            h24 = 0
        else:
            h24 = h
        if ampm == 'PM':
            h24 += 12
        candidates.append((h24, mnt))

    # 24-hour
    for m in re.finditer(r'\b(\d{1,2}):(\d{2})\b', s):
        h24 = int(m.group(1))
        mnt = int(m.group(2))
        candidates.append((h24, mnt))

    # Keywords
    if re.search(r'\bnoon\b', s, flags=re.IGNORECASE):
        candidates.append((12, 0))
    if re.search(r'\bmidnight\b', s, flags=re.IGNORECASE):
        candidates.append((0, 0))

    # Bare ambiguous like '2' or '10:30'
    m = re.match(r'^(\d{1,2})(?::(\d{2}))?$', s)
    if m:
        h = int(m.group(1))
        mnt = int(m.group(2) or '0')
        if 1 <= h <= 6:
            h += 12  # afternoon
        candidates.append((h, mnt))

    if not candidates:
        return ''

    def score(c):
        h, _ = c
        if 8 <= h <= 20:
            return 3
        if 7 <= h <= 21:
            return 2
        if 6 <= h <= 22:
            return 1
        return 0

    best = max(candidates, key=score)
    h24, mnt = best

    # Convert to 12-hour string
    if h24 == 0:
        return f"12:{mnt:02d} AM"
    if 1 <= h24 < 12:
        return f"{h24}:{mnt:02d} AM"
    if h24 == 12:
        return f"12:{mnt:02d} PM"
    return f"{h24 - 12}:{mnt:02d} PM"


def fix_times_in_database(db_path: str = 'events.db') -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT id, time FROM events')
    rows = cur.fetchall()
    updated = 0
    for event_id, t in rows:
        t = t or ''
        new_t = normalize_time(t)
        # Fix placeholder midnight when no explicit time existed; try heuristic default 2 PM for afternoon talks
        if new_t == '12:00 AM':
            # leave empty so frontend hides it, or set to 2:00 PM as a safer assumption
            new_t = ''
        if new_t and new_t != t:
            cur.execute('UPDATE events SET time = ? WHERE id = ?', (new_t, event_id))
            updated += 1
    conn.commit()
    conn.close()
    print(f"Updated times for {updated} events")


if __name__ == '__main__':
    fix_times_in_database()


