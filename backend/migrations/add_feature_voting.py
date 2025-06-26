
"""
Feature Voting System Migration

This migration creates the tables needed for the feature voting board:
- feature_requests: Core feature request data
- feature_votes: User votes on features  
- feature_comments: Comments on feature requests
"""

import sqlite3
from datetime import datetime
import uuid

def run_migration():
    try:
        print("🗳️ Adding Feature Voting System...")
        
        # Connect to database
        conn = sqlite3.connect('backend/tradesense.db')
        cursor = conn.cursor()
        
        # Create feature_requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_requests (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'proposed',
            priority TEXT DEFAULT 'medium',
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            user_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            effort_estimate TEXT,
            business_value TEXT,
            admin_notes TEXT,
            estimated_completion TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create feature_votes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_votes (
            id TEXT PRIMARY KEY,
            feature_request_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            vote_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feature_request_id) REFERENCES feature_requests (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(feature_request_id, user_id)
        )
        ''')
        
        # Create feature_comments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_comments (
            id TEXT PRIMARY KEY,
            feature_request_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (feature_request_id) REFERENCES feature_requests (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_requests_category ON feature_requests(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_requests_status ON feature_requests(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_requests_votes ON feature_requests(upvotes, downvotes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_votes_user ON feature_votes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_comments_request ON feature_comments(feature_request_id)')
        
        # Add some sample feature requests
        sample_user_id = str(uuid.uuid4())
        
        sample_features = [
            {
                'id': str(uuid.uuid4()),
                'title': 'Advanced Portfolio Analytics',
                'description': 'Add more sophisticated portfolio analysis including sector allocation, correlation analysis, and risk attribution.',
                'category': 'analytics',
                'status': 'proposed',
                'priority': 'high',
                'upvotes': 15,
                'downvotes': 2,
                'user_id': sample_user_id
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Dark Mode Theme',
                'description': 'Implement a dark mode theme for better usability during evening trading sessions.',
                'category': 'ui',
                'status': 'approved',
                'priority': 'medium',
                'upvotes': 28,
                'downvotes': 1,
                'user_id': sample_user_id
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Real-time Market Data Integration',
                'description': 'Integrate with market data providers to show real-time quotes and news alongside trade analysis.',
                'category': 'integration',
                'status': 'reviewing',
                'priority': 'high',
                'upvotes': 22,
                'downvotes': 5,
                'user_id': sample_user_id
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Mobile App',
                'description': 'Create a mobile app for iOS and Android to view analytics and add trades on the go.',
                'category': 'ui',
                'status': 'proposed',
                'priority': 'critical',
                'upvotes': 45,
                'downvotes': 3,
                'user_id': sample_user_id
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'API Rate Limiting',
                'description': 'Implement proper rate limiting to prevent API abuse and ensure fair usage.',
                'category': 'security',
                'status': 'in_progress',
                'priority': 'high',
                'upvotes': 8,
                'downvotes': 0,
                'user_id': sample_user_id
            }
        ]
        
        for feature in sample_features:
            cursor.execute('''
            INSERT OR IGNORE INTO feature_requests 
            (id, title, description, category, status, priority, upvotes, downvotes, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature['id'], feature['title'], feature['description'],
                feature['category'], feature['status'], feature['priority'],
                feature['upvotes'], feature['downvotes'], feature['user_id']
            ))
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'feature_%'")
        tables = cursor.fetchall()
        print(f"✅ Created {len(tables)} feature voting tables")
        
        # Verify sample data
        cursor.execute("SELECT COUNT(*) FROM feature_requests")
        count = cursor.fetchone()[0]
        print(f"✅ Added {count} sample feature requests")
        
        conn.commit()
        conn.close()
        
        print("✅ Feature voting system migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()
