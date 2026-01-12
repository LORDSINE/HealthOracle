#!/usr/bin/env python3
"""Simple script to view database contents"""
import sqlite3
from tabulate import tabulate

DATABASE = 'healthoracle.db'

def view_users():
    """Display all users in a nice table format"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        users = cursor.execute('SELECT patient_id, name, email, phone FROM users').fetchall()
        
        if not users:
            print("\n📊 Database is empty - no users registered yet.\n")
            return
        
        # Convert to list of lists for tabulate
        data = []
        for user in users:
            data.append([
                user['patient_id'],
                user['name'],
                user['email'],
                user['phone'] or 'N/A'
            ])
        
        print("\n" + "="*80)
        print("📊 HEALTH ORACLE - USER DATABASE")
        print("="*80)
        print(tabulate(data, headers=['Patient ID', 'Name', 'Email', 'Phone'], tablefmt='grid'))
        print(f"\nTotal Users: {len(users)}")
        print("="*80 + "\n")
        
        conn.close()
        
    except sqlite3.OperationalError as e:
        print(f"\n❌ Error: {e}")
        print("Database file might not exist yet. Run the app first to create it.\n")
    except Exception as e:
        print(f"\n❌ Error viewing database: {e}\n")

if __name__ == '__main__':
    view_users()
