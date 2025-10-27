#!/usr/bin/env python3
"""
Add sample events with different dates to make the calendar more interesting
"""

from database import Database
from datetime import datetime, timedelta
import random

def add_sample_events():
    db = Database()
    
    # Sample events with different dates
    sample_events = [
        {
            'title': 'Google Cloud Next 2025',
            'description': 'Google Cloud Next is the premier cloud computing conference featuring the latest innovations in cloud technology, AI, and machine learning.',
            'url': 'https://cloud.withgoogle.com/next',
            'source_url': 'https://cloud.withgoogle.com/next',
            'is_virtual': False,
            'requires_registration': True,
            'categories': ['Cloud Computing', 'AI'],
            'host': 'Google',
            'cost_type': 'Paid',
            'date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'time': '09:00',
            'location': 'Boston Convention Center',
            'source': 'Sample'
        },
        {
            'title': 'Microsoft Build 2025',
            'description': 'Microsoft Build is the annual developer conference showcasing the latest tools, technologies, and innovations from Microsoft.',
            'url': 'https://build.microsoft.com',
            'source_url': 'https://build.microsoft.com',
            'is_virtual': True,
            'requires_registration': True,
            'categories': ['Cloud Computing', 'AI'],
            'host': 'Microsoft',
            'cost_type': 'Free',
            'date': (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'),
            'time': '10:00',
            'location': 'Virtual',
            'source': 'Sample'
        },
        {
            'title': 'AWS re:Invent 2025',
            'description': 'AWS re:Invent is the largest cloud computing conference featuring the latest AWS services and cloud innovations.',
            'url': 'https://reinvent.awsevents.com',
            'source_url': 'https://reinvent.awsevents.com',
            'is_virtual': False,
            'requires_registration': True,
            'categories': ['Cloud Computing'],
            'host': 'Amazon Web Services',
            'cost_type': 'Paid',
            'date': (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d'),
            'time': '08:30',
            'location': 'Las Vegas Convention Center',
            'source': 'Sample'
        },
        {
            'title': 'DockerCon 2025',
            'description': 'DockerCon is the premier container technology conference featuring the latest in containerization and DevOps.',
            'url': 'https://docker.events.cube365.net/dockercon',
            'source_url': 'https://docker.events.cube365.net/dockercon',
            'is_virtual': True,
            'requires_registration': True,
            'categories': ['DevOps', 'Cloud Computing'],
            'host': 'Docker',
            'cost_type': 'Free',
            'date': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'time': '09:00',
            'location': 'Virtual',
            'source': 'Sample'
        },
        {
            'title': 'Kubernetes Community Days Boston 2025',
            'description': 'Kubernetes Community Days Boston brings together the local Kubernetes community for learning and networking.',
            'url': 'https://community.cncf.io/events/details/cncf-kcd-boston-2025',
            'source_url': 'https://community.cncf.io/events/details/cncf-kcd-boston-2025',
            'is_virtual': False,
            'requires_registration': True,
            'categories': ['DevOps', 'Cloud Computing'],
            'host': 'CNCF',
            'cost_type': 'Free',
            'date': (datetime.now() + timedelta(days=55)).strftime('%Y-%m-%d'),
            'time': '09:00',
            'location': 'MIT Campus',
            'source': 'Sample'
        },
        {
            'title': 'Hugging Face Transformers Summit 2025',
            'description': 'The Hugging Face Transformers Summit showcases the latest advances in transformer models and NLP.',
            'url': 'https://huggingface.co/summit',
            'source_url': 'https://huggingface.co/summit',
            'is_virtual': True,
            'requires_registration': True,
            'categories': ['AI', 'Machine Learning'],
            'host': 'Hugging Face',
            'cost_type': 'Free',
            'date': (datetime.now() + timedelta(days=65)).strftime('%Y-%m-%d'),
            'time': '10:00',
            'location': 'Virtual',
            'source': 'Sample'
        },
        {
            'title': 'GitHub Universe 2025',
            'description': 'GitHub Universe is the annual developer conference showcasing the latest in software development and collaboration.',
            'url': 'https://githubuniverse.com',
            'source_url': 'https://githubuniverse.com',
            'is_virtual': True,
            'requires_registration': True,
            'categories': ['Software Development', 'DevOps'],
            'host': 'GitHub',
            'cost_type': 'Free',
            'date': (datetime.now() + timedelta(days=75)).strftime('%Y-%m-%d'),
            'time': '09:00',
            'location': 'Virtual',
            'source': 'Sample'
        },
        {
            'title': 'Red Hat Summit 2025',
            'description': 'Red Hat Summit is the premier open source technology conference featuring enterprise solutions and innovations.',
            'url': 'https://www.redhat.com/en/summit',
            'source_url': 'https://www.redhat.com/en/summit',
            'is_virtual': False,
            'requires_registration': True,
            'categories': ['Open Source', 'Enterprise'],
            'host': 'Red Hat',
            'cost_type': 'Paid',
            'date': (datetime.now() + timedelta(days=85)).strftime('%Y-%m-%d'),
            'time': '08:00',
            'location': 'Boston Convention Center',
            'source': 'Sample'
        }
    ]
    
    print("Adding sample events to database...")
    added_count = 0
    
    for event in sample_events:
        try:
            event_id = db.add_computing_event(event)
            if event_id:
                added_count += 1
                print(f"Added: {event['title']} on {event['date']}")
        except Exception as e:
            print(f"Error adding event {event['title']}: {e}")
    
    print(f"\nSuccessfully added {added_count} sample events")
    
    # Show total events
    all_events = db.get_computing_events()
    print(f"Total events in database: {len(all_events)}")

if __name__ == "__main__":
    add_sample_events()



