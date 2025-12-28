"""
Pattern Database Optimizer

Optimizes pattern storage and management by:
- Cleaning up low-confidence patterns
- Merging similar patterns
- Archiving old unused patterns
- Tracking pattern effectiveness
- Migrating to SQLite for better performance
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import json
import sqlite3
import hashlib

from .logging_setup import get_logger
from .pattern_recognition import ExecutionPattern


class PatternOptimizer:
    """
    Optimizes pattern database for better performance and storage efficiency.
    
    Features:
    - Remove low-confidence patterns (< 0.3)
    - Merge similar patterns
    - Archive old patterns (> 90 days unused)
    - Track pattern effectiveness
    - SQLite storage for better performance
    """
    
    def __init__(self, project_dir: Path):
        """
        Initialize pattern optimizer.
        
        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.logger = get_logger()
        
        # Database paths
        self.db_path = project_dir / '.pipeline' / 'patterns.db'
        self.archive_path = project_dir / '.pipeline' / 'patterns_archive.db'
        self.legacy_json_path = project_dir / '.pipeline' / 'patterns.json'
        
        # Optimization thresholds
        self.min_confidence = 0.3
        self.archive_days = 90
        self.similarity_threshold = 0.85
        self.min_success_rate = 0.2
        
        # Statistics
        self.stats = {
            'patterns_removed': 0,
            'patterns_merged': 0,
            'patterns_archived': 0,
            'space_saved': 0
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_hash TEXT UNIQUE NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL NOT NULL,
                occurrences INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                last_used TIMESTAMP,
                effectiveness_score REAL DEFAULT 0.0,
                archived BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pattern_type ON patterns(pattern_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence ON patterns(confidence)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_used ON patterns(last_used)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_archived ON patterns(archived)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pattern_hash ON patterns(pattern_hash)')
        
        # Create effectiveness tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                success BOOLEAN NOT NULL,
                execution_time REAL,
                context TEXT,
                FOREIGN KEY (pattern_id) REFERENCES patterns(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_pattern ON pattern_usage(pattern_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON pattern_usage(timestamp)')
        
        conn.commit()
        conn.close()
        
        self.logger.info("📊 Pattern database initialized")
    
    def _pattern_hash(self, pattern_data: Dict) -> str:
        """Generate hash for pattern data."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(pattern_data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def migrate_from_json(self) -> int:
        """
        Migrate patterns from legacy JSON format to SQLite.
        
        Returns:
            Number of patterns migrated
        """
        if not self.legacy_json_path.exists():
            self.logger.info("No legacy JSON patterns to migrate")
            return 0
        
        try:
            with open(self.legacy_json_path, 'r') as f:
                data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            migrated = 0
            for pattern_type, patterns in data.get('patterns', {}).items():
                for pattern in patterns:
                    pattern_hash = self._pattern_hash(pattern['pattern_data'])
                    
                    try:
                        cursor.execute('''
                            INSERT INTO patterns (
                                pattern_type, pattern_hash, pattern_data,
                                confidence, occurrences, first_seen, last_seen
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            pattern_type,
                            pattern_hash,
                            json.dumps(pattern['pattern_data']),
                            pattern['confidence'],
                            pattern.get('occurrences', 1),
                            pattern['first_seen'],
                            pattern['last_seen']
                        ))
                        migrated += 1
                    except sqlite3.IntegrityError:
                        # Pattern already exists (duplicate hash)
                        pass
            
            conn.commit()
            conn.close()
            
            # Backup and remove JSON file
            backup_path = self.legacy_json_path.with_suffix('.json.backup')
            self.legacy_json_path.rename(backup_path)
            
            self.logger.info(f"✅ Migrated {migrated} patterns from JSON to SQLite")
            return migrated
            
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            return 0
    
    def cleanup_low_confidence_patterns(self) -> int:
        """
        Remove patterns with confidence below threshold.
        
        Returns:
            Number of patterns removed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count patterns to remove
        cursor.execute('''
            SELECT COUNT(*) FROM patterns 
            WHERE confidence < ? AND archived = 0
        ''', (self.min_confidence,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            return 0
        
        # Remove low-confidence patterns
        cursor.execute('''
            DELETE FROM patterns 
            WHERE confidence < ? AND archived = 0
        ''', (self.min_confidence,))
        
        conn.commit()
        conn.close()
        
        self.stats['patterns_removed'] += count
        self.logger.info(f"🧹 Removed {count} low-confidence patterns (< {self.min_confidence})")
        return count
    
    def merge_similar_patterns(self) -> int:
        """
        Merge patterns that are very similar.
        
        Returns:
            Number of patterns merged
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all patterns grouped by type
        cursor.execute('''
            SELECT id, pattern_type, pattern_data, confidence, occurrences
            FROM patterns WHERE archived = 0
            ORDER BY pattern_type, confidence DESC
        ''')
        
        patterns_by_type = defaultdict(list)
        for row in cursor.fetchall():
            pattern_id, ptype, pdata, conf, occ = row
            patterns_by_type[ptype].append({
                'id': pattern_id,
                'data': json.loads(pdata),
                'confidence': conf,
                'occurrences': occ
            })
        
        merged_count = 0
        
        for ptype, patterns in patterns_by_type.items():
            # Compare each pattern with others
            i = 0
            while i < len(patterns):
                j = i + 1
                while j < len(patterns):
                    similarity = self._calculate_similarity(
                        patterns[i]['data'],
                        patterns[j]['data']
                    )
                    
                    if similarity >= self.similarity_threshold:
                        # Merge j into i
                        self._merge_patterns(
                            cursor,
                            patterns[i]['id'],
                            patterns[j]['id']
                        )
                        patterns.pop(j)
                        merged_count += 1
                    else:
                        j += 1
                i += 1
        
        conn.commit()
        conn.close()
        
        self.stats['patterns_merged'] += merged_count
        if merged_count > 0:
            self.logger.info(f"🔗 Merged {merged_count} similar patterns")
        return merged_count
    
    def _calculate_similarity(self, data1: Dict, data2: Dict) -> float:
        """Calculate similarity between two pattern data dictionaries."""
        # Simple similarity based on common keys and values
        keys1 = set(data1.keys())
        keys2 = set(data2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        common_keys = keys1 & keys2
        if not common_keys:
            return 0.0
        
        # Calculate similarity based on common key-value pairs
        matching = sum(1 for k in common_keys if data1.get(k) == data2.get(k))
        total = len(keys1 | keys2)
        
        return matching / total if total > 0 else 0.0
    
    def _merge_patterns(self, cursor, keep_id: int, remove_id: int):
        """Merge two patterns, keeping the first and removing the second."""
        # Update occurrences and confidence
        cursor.execute('''
            UPDATE patterns
            SET occurrences = occurrences + (
                SELECT occurrences FROM patterns WHERE id = ?
            ),
            confidence = (confidence + (
                SELECT confidence FROM patterns WHERE id = ?
            )) / 2
            WHERE id = ?
        ''', (remove_id, remove_id, keep_id))
        
        # Transfer usage records
        cursor.execute('''
            UPDATE pattern_usage
            SET pattern_id = ?
            WHERE pattern_id = ?
        ''', (keep_id, remove_id))
        
        # Remove merged pattern
        cursor.execute('DELETE FROM patterns WHERE id = ?', (remove_id,))
    
    def archive_old_patterns(self) -> int:
        """
        Archive patterns that haven't been used in 90+ days.
        
        Returns:
            Number of patterns archived
        """
        cutoff_date = datetime.now() - timedelta(days=self.archive_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count patterns to archive
        cursor.execute('''
            SELECT COUNT(*) FROM patterns 
            WHERE (last_used IS NULL OR last_used < ?)
            AND archived = 0
        ''', (cutoff_date.isoformat(),))
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            return 0
        
        # Mark patterns as archived
        cursor.execute('''
            UPDATE patterns
            SET archived = 1
            WHERE (last_used IS NULL OR last_used < ?)
            AND archived = 0
        ''', (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
        
        self.stats['patterns_archived'] += count
        self.logger.info(f"📦 Archived {count} old patterns (> {self.archive_days} days unused)")
        return count
    
    def update_effectiveness_scores(self):
        """Update effectiveness scores for all patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate effectiveness for each pattern
        cursor.execute('''
            SELECT id, success_count, failure_count, occurrences
            FROM patterns WHERE archived = 0
        ''')
        
        for row in cursor.fetchall():
            pattern_id, success, failure, occurrences = row
            
            if occurrences == 0:
                effectiveness = 0.0
            else:
                # Effectiveness = (success rate * confidence boost)
                success_rate = success / (success + failure) if (success + failure) > 0 else 0.5
                usage_factor = min(1.0, occurrences / 10)  # Boost for frequently used patterns
                effectiveness = success_rate * (0.7 + 0.3 * usage_factor)
            
            cursor.execute('''
                UPDATE patterns
                SET effectiveness_score = ?
                WHERE id = ?
            ''', (effectiveness, pattern_id))
        
        conn.commit()
        conn.close()
        
        self.logger.info("📈 Updated effectiveness scores for all patterns")
    
    def remove_ineffective_patterns(self) -> int:
        """
        Remove patterns with low success rate.
        
        Returns:
            Number of patterns removed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count patterns to remove
        cursor.execute('''
            SELECT COUNT(*) FROM patterns 
            WHERE effectiveness_score < ? 
            AND (success_count + failure_count) >= 5
            AND archived = 0
        ''', (self.min_success_rate,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            return 0
        
        # Remove ineffective patterns
        cursor.execute('''
            DELETE FROM patterns 
            WHERE effectiveness_score < ? 
            AND (success_count + failure_count) >= 5
            AND archived = 0
        ''', (self.min_success_rate,))
        
        conn.commit()
        conn.close()
        
        self.stats['patterns_removed'] += count
        self.logger.info(f"🗑️  Removed {count} ineffective patterns (success rate < {self.min_success_rate})")
        return count
    
    def optimize_database(self):
        """Run SQLite optimization commands."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vacuum to reclaim space
        cursor.execute('VACUUM')
        
        # Analyze for query optimization
        cursor.execute('ANALYZE')
        
        conn.commit()
        conn.close()
        
        self.logger.info("⚡ Optimized database structure")
    
    def get_statistics(self) -> Dict:
        """Get pattern database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total patterns
        cursor.execute('SELECT COUNT(*) FROM patterns WHERE archived = 0')
        stats['active_patterns'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM patterns WHERE archived = 1')
        stats['archived_patterns'] = cursor.fetchone()[0]
        
        # Patterns by type
        cursor.execute('''
            SELECT pattern_type, COUNT(*) 
            FROM patterns WHERE archived = 0
            GROUP BY pattern_type
        ''')
        stats['patterns_by_type'] = dict(cursor.fetchall())
        
        # Average confidence
        cursor.execute('SELECT AVG(confidence) FROM patterns WHERE archived = 0')
        stats['avg_confidence'] = cursor.fetchone()[0] or 0.0
        
        # Average effectiveness
        cursor.execute('SELECT AVG(effectiveness_score) FROM patterns WHERE archived = 0')
        stats['avg_effectiveness'] = cursor.fetchone()[0] or 0.0
        
        # Database size
        stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
        
        conn.close()
        
        return stats
    
    def run_full_optimization(self) -> Dict:
        """
        Run complete optimization workflow.
        
        Returns:
            Dictionary with optimization results
        """
        self.logger.info("🚀 Starting full pattern database optimization")
        
        # Step 1: Migrate from JSON if needed
        migrated = self.migrate_from_json()
        
        # Step 2: Update effectiveness scores
        self.update_effectiveness_scores()
        
        # Step 3: Remove low-confidence patterns
        removed_low_conf = self.cleanup_low_confidence_patterns()
        
        # Step 4: Remove ineffective patterns
        removed_ineffective = self.remove_ineffective_patterns()
        
        # Step 5: Merge similar patterns
        merged = self.merge_similar_patterns()
        
        # Step 6: Archive old patterns
        archived = self.archive_old_patterns()
        
        # Step 7: Optimize database
        self.optimize_database()
        
        # Get final statistics
        stats = self.get_statistics()
        
        results = {
            'migrated': migrated,
            'removed_low_confidence': removed_low_conf,
            'removed_ineffective': removed_ineffective,
            'merged': merged,
            'archived': archived,
            'final_stats': stats
        }
        
        self.logger.info(f"✅ Optimization complete: {results}")
        return results