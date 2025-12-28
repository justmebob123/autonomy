"""
Tests for Pattern Database Optimizer
"""

import unittest
import tempfile
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.pattern_optimizer import PatternOptimizer


class TestPatternOptimizer(unittest.TestCase):
    """Test pattern database optimization."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.optimizer = PatternOptimizer(self.project_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database is properly initialized."""
        self.assertTrue(self.optimizer.db_path.exists())
        
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('patterns', tables)
        self.assertIn('pattern_usage', tables)
        
        conn.close()
    
    def test_json_migration(self):
        """Test migration from JSON to SQLite."""
        # Create legacy JSON file
        json_data = {
            'patterns': {
                'tool_usage': [
                    {
                        'pattern_type': 'tool_usage',
                        'pattern_data': {'tool': 'execute-command', 'success': True},
                        'confidence': 0.8,
                        'occurrences': 5,
                        'first_seen': '2024-01-01T00:00:00',
                        'last_seen': '2024-01-10T00:00:00'
                    }
                ],
                'successes': [
                    {
                        'pattern_type': 'successes',
                        'pattern_data': {'phase': 'execution', 'result': 'success'},
                        'confidence': 0.9,
                        'occurrences': 10,
                        'first_seen': '2024-01-01T00:00:00',
                        'last_seen': '2024-01-15T00:00:00'
                    }
                ]
            }
        }
        
        json_path = self.project_dir / '.pipeline' / 'patterns.json'
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(json_data, f)
        
        # Migrate
        migrated = self.optimizer.migrate_from_json()
        
        self.assertEqual(migrated, 2)
        self.assertFalse(json_path.exists())
        self.assertTrue(json_path.with_suffix('.json.backup').exists())
        
        # Verify data in database
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)
        conn.close()
    
    def test_cleanup_low_confidence(self):
        """Test removal of low-confidence patterns."""
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Insert test patterns
        patterns = [
            ('tool_usage', 'hash1', '{"tool": "test1"}', 0.2, 1, datetime.now().isoformat(), datetime.now().isoformat()),
            ('tool_usage', 'hash2', '{"tool": "test2"}', 0.5, 1, datetime.now().isoformat(), datetime.now().isoformat()),
            ('tool_usage', 'hash3', '{"tool": "test3"}', 0.8, 1, datetime.now().isoformat(), datetime.now().isoformat()),
        ]
        
        for p in patterns:
            cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_hash, pattern_data, confidence, occurrences, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', p)
        
        conn.commit()
        conn.close()
        
        # Clean up low confidence
        removed = self.optimizer.cleanup_low_confidence_patterns()
        
        self.assertEqual(removed, 1)  # Only pattern with 0.2 confidence should be removed
        
        # Verify
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)
        conn.close()
    
    def test_merge_similar_patterns(self):
        """Test merging of similar patterns."""
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Insert similar patterns
        patterns = [
            ('tool_usage', 'hash1', '{"tool": "execute-command", "action": "run"}', 0.8, 5, datetime.now().isoformat(), datetime.now().isoformat()),
            ('tool_usage', 'hash2', '{"tool": "execute-command", "action": "run"}', 0.7, 3, datetime.now().isoformat(), datetime.now().isoformat()),
            ('tool_usage', 'hash3', '{"tool": "create-file", "action": "write"}', 0.9, 2, datetime.now().isoformat(), datetime.now().isoformat()),
        ]
        
        for p in patterns:
            cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_hash, pattern_data, confidence, occurrences, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', p)
        
        conn.commit()
        conn.close()
        
        # Merge similar patterns
        merged = self.optimizer.merge_similar_patterns()
        
        self.assertGreaterEqual(merged, 1)  # At least one merge should happen
        
        # Verify
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns')
        count = cursor.fetchone()[0]
        self.assertLess(count, 3)  # Should have fewer patterns after merge
        conn.close()
    
    def test_archive_old_patterns(self):
        """Test archiving of old unused patterns."""
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Insert patterns with different last_used dates
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        recent_date = (datetime.now() - timedelta(days=10)).isoformat()
        
        patterns = [
            ('tool_usage', 'hash1', '{"tool": "test1"}', 0.8, 1, old_date, old_date, old_date),
            ('tool_usage', 'hash2', '{"tool": "test2"}', 0.8, 1, recent_date, recent_date, recent_date),
            ('tool_usage', 'hash3', '{"tool": "test3"}', 0.8, 1, old_date, old_date, None),
        ]
        
        for p in patterns:
            cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_hash, pattern_data, confidence, occurrences, first_seen, last_seen, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)
        
        conn.commit()
        conn.close()
        
        # Archive old patterns
        archived = self.optimizer.archive_old_patterns()
        
        self.assertEqual(archived, 2)  # Two old patterns should be archived
        
        # Verify
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns WHERE archived = 1')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)
        conn.close()
    
    def test_effectiveness_scoring(self):
        """Test effectiveness score calculation."""
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Insert patterns with usage data
        patterns = [
            ('tool_usage', 'hash1', '{"tool": "test1"}', 0.8, 10, datetime.now().isoformat(), datetime.now().isoformat(), 8, 2),
            ('tool_usage', 'hash2', '{"tool": "test2"}', 0.7, 10, datetime.now().isoformat(), datetime.now().isoformat(), 2, 8),
        ]
        
        for p in patterns:
            cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_hash, pattern_data, confidence, occurrences, first_seen, last_seen, success_count, failure_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)
        
        conn.commit()
        conn.close()
        
        # Update effectiveness scores
        self.optimizer.update_effectiveness_scores()
        
        # Verify scores
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT effectiveness_score FROM patterns ORDER BY pattern_hash')
        scores = [row[0] for row in cursor.fetchall()]
        
        self.assertGreater(scores[0], scores[1])  # First pattern should have higher score
        self.assertGreater(scores[0], 0.5)  # Good pattern should have > 0.5 score
        self.assertLess(scores[1], 0.5)  # Poor pattern should have < 0.5 score
        
        conn.close()
    
    def test_remove_ineffective_patterns(self):
        """Test removal of ineffective patterns."""
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Insert patterns with different effectiveness
        patterns = [
            ('tool_usage', 'hash1', '{"tool": "test1"}', 0.8, 10, datetime.now().isoformat(), datetime.now().isoformat(), 8, 2, 0.8),
            ('tool_usage', 'hash2', '{"tool": "test2"}', 0.7, 10, datetime.now().isoformat(), datetime.now().isoformat(), 1, 9, 0.1),
        ]
        
        for p in patterns:
            cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_hash, pattern_data, confidence, occurrences, first_seen, last_seen, success_count, failure_count, effectiveness_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)
        
        conn.commit()
        conn.close()
        
        # Remove ineffective patterns
        removed = self.optimizer.remove_ineffective_patterns()
        
        self.assertEqual(removed, 1)  # One ineffective pattern should be removed
        
        # Verify
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        conn.close()
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        conn = sqlite3.connect(self.optimizer.db_path)
        cursor = conn.cursor()
        
        # Insert test patterns
        patterns = [
            ('tool_usage', 'hash1', '{"tool": "test1"}', 0.8, 1, datetime.now().isoformat(), datetime.now().isoformat(), 0),
            ('successes', 'hash2', '{"result": "success"}', 0.9, 1, datetime.now().isoformat(), datetime.now().isoformat(), 0),
            ('failures', 'hash3', '{"error": "test"}', 0.7, 1, datetime.now().isoformat(), datetime.now().isoformat(), 1),
        ]
        
        for p in patterns:
            cursor.execute('''
                INSERT INTO patterns (pattern_type, pattern_hash, pattern_data, confidence, occurrences, first_seen, last_seen, archived)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)
        
        conn.commit()
        conn.close()
        
        # Get statistics
        stats = self.optimizer.get_statistics()
        
        self.assertEqual(stats['active_patterns'], 2)
        self.assertEqual(stats['archived_patterns'], 1)
        self.assertIn('tool_usage', stats['patterns_by_type'])
        self.assertIn('successes', stats['patterns_by_type'])
        self.assertGreater(stats['avg_confidence'], 0)
    
    def test_full_optimization(self):
        """Test complete optimization workflow."""
        # Create legacy JSON with patterns that won't be removed
        recent_date = datetime.now().isoformat()
        json_data = {
            'patterns': {
                'tool_usage': [
                    {
                        'pattern_type': 'tool_usage',
                        'pattern_data': {'tool': 'test'},
                        'confidence': 0.2,  # Low confidence - will be removed
                        'occurrences': 1,
                        'first_seen': '2024-01-01T00:00:00',
                        'last_seen': '2024-01-01T00:00:00'
                    },
                    {
                        'pattern_type': 'tool_usage',
                        'pattern_data': {'tool': 'good'},
                        'confidence': 0.8,  # Good confidence
                        'occurrences': 10,
                        'first_seen': recent_date,
                        'last_seen': recent_date
                    },
                    {
                        'pattern_type': 'successes',
                        'pattern_data': {'result': 'success'},
                        'confidence': 0.9,  # High confidence
                        'occurrences': 15,
                        'first_seen': recent_date,
                        'last_seen': recent_date
                    }
                ]
            }
        }
        
        json_path = self.project_dir / '.pipeline' / 'patterns.json'
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(json_data, f)
        
        # Run full optimization
        results = self.optimizer.run_full_optimization()
        
        self.assertEqual(results['migrated'], 3)
        self.assertIn('final_stats', results)
        # At least one good pattern should remain after optimization
        total_patterns = results['final_stats']['active_patterns'] + results['final_stats']['archived_patterns']
        self.assertGreater(total_patterns, 0)


if __name__ == '__main__':
    unittest.main()