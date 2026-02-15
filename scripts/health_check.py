#!/usr/bin/env python3
"""
Database Health Check Script for Neural Terminal.

Monitors database health and reports issues. Can be used for:
- Monitoring dashboards
- Health check endpoints
- Alerting systems
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from neural_terminal.config import settings


@dataclass
class HealthStatus:
    """Health check result."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    database: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]


class DatabaseHealthChecker:
    """Database health monitoring."""
    
    # Thresholds
    MAX_SIZE_MB = 1024  # Warn if database > 1GB
    MAX_WAL_SIZE_MB = 100  # Warn if WAL > 100MB
    MAX_CONVERSATIONS = 10000  # Warn if too many conversations
    MAX_MESSAGES_PER_CONV = 1000  # Warn if conversation too long
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize health checker.
        
        Args:
            db_path: Path to database file
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = settings.db_path
    
    def connect(self) -> sqlite3.Connection:
        """Connect to database."""
        return sqlite3.connect(str(self.db_path), timeout=5.0)
    
    def check_integrity(self) -> tuple[bool, List[str]]:
        """Check database integrity.
        
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Integrity check
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            if result[0] != "ok":
                issues.append(f"Database corruption: {result[0]}")
            
            # Foreign key check
            cursor.execute("PRAGMA foreign_key_check;")
            fk_issues = cursor.fetchall()
            if fk_issues:
                issues.append(f"Foreign key violations: {len(fk_issues)}")
            
            conn.close()
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Integrity check failed: {e}"]
    
    def check_size(self) -> tuple[bool, List[str], Dict[str, Any]]:
        """Check database file sizes.
        
        Returns:
            Tuple of (is_ok, issues, stats)
        """
        issues = []
        stats = {}
        
        # Main database
        if self.db_path.exists():
            size_mb = self.db_path.stat().st_size / (1024 * 1024)
            stats["size_mb"] = round(size_mb, 2)
            
            if size_mb > self.MAX_SIZE_MB:
                issues.append(f"Database size ({size_mb:.1f}MB) exceeds threshold ({self.MAX_SIZE_MB}MB)")
        else:
            issues.append("Database file not found")
            stats["size_mb"] = 0
        
        # WAL file
        wal_path = Path(str(self.db_path) + "-wal")
        if wal_path.exists():
            wal_size_mb = wal_path.stat().st_size / (1024 * 1024)
            stats["wal_size_mb"] = round(wal_size_mb, 2)
            
            if wal_size_mb > self.MAX_WAL_SIZE_MB:
                issues.append(f"WAL size ({wal_size_mb:.1f}MB) exceeds threshold ({self.MAX_WAL_SIZE_MB}MB)")
        else:
            stats["wal_size_mb"] = 0
        
        # SHM file
        shm_path = Path(str(self.db_path) + "-shm")
        if shm_path.exists():
            stats["shm_size_mb"] = round(shm_path.stat().st_size / (1024 * 1024), 2)
        else:
            stats["shm_size_mb"] = 0
        
        return len(issues) == 0, issues, stats
    
    def check_performance(self) -> tuple[bool, List[str], Dict[str, Any]]:
        """Check database performance metrics.
        
        Returns:
            Tuple of (is_ok, issues, stats)
        """
        issues = []
        stats = {}
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM conversations;")
            stats["conversations"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages;")
            stats["messages"] = cursor.fetchone()[0]
            
            # Check for very long conversations
            cursor.execute("""
                SELECT conversation_id, COUNT(*) as msg_count
                FROM messages
                GROUP BY conversation_id
                HAVING msg_count > ?
            """, (self.MAX_MESSAGES_PER_CONV,))
            long_convs = cursor.fetchall()
            if long_convs:
                issues.append(f"{len(long_convs)} conversations exceed {self.MAX_MESSAGES_PER_CONV} messages")
            
            # Check for conversations without messages
            cursor.execute("""
                SELECT COUNT(*) FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE m.id IS NULL
            """)
            empty_convs = cursor.fetchone()[0]
            if empty_convs > 10:  # Allow some empty for new conversations
                issues.append(f"{empty_convs} conversations have no messages (consider cleanup)")
            
            # Calculate average messages per conversation
            if stats["conversations"] > 0:
                stats["avg_messages_per_conv"] = round(
                    stats["messages"] / stats["conversations"], 2
                )
            else:
                stats["avg_messages_per_conv"] = 0
            
            conn.close()
            
            if stats["conversations"] > self.MAX_CONVERSATIONS:
                issues.append(f"Too many conversations ({stats['conversations']}, consider archiving)")
            
            return len(issues) == 0, issues, stats
            
        except Exception as e:
            return False, [f"Performance check failed: {e}"], {}
    
    def check_configuration(self) -> tuple[bool, List[str], Dict[str, Any]]:
        """Check database configuration.
        
        Returns:
            Tuple of (is_ok, issues, config)
        """
        issues = []
        config = {}
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Get settings
            cursor.execute("PRAGMA journal_mode;")
            config["journal_mode"] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA synchronous;")
            config["synchronous"] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA cache_size;")
            config["cache_size"] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA mmap_size;")
            config["mmap_size"] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size;")
            config["page_size"] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA foreign_keys;")
            config["foreign_keys"] = cursor.fetchone()[0]
            
            conn.close()
            
            # Validate settings
            if config["journal_mode"] != "wal":
                issues.append(f"WAL mode not enabled (current: {config['journal_mode']})")
            
            if config["foreign_keys"] != 1:
                issues.append("Foreign key constraints not enabled")
            
            return len(issues) == 0, issues, config
            
        except Exception as e:
            return False, [f"Configuration check failed: {e}"], {}
    
    def run_health_check(self) -> HealthStatus:
        """Run complete health check.
        
        Returns:
            HealthStatus object
        """
        all_issues = []
        all_recommendations = []
        database_stats = {}
        
        # Check integrity
        integrity_ok, integrity_issues = self.check_integrity()
        all_issues.extend(integrity_issues)
        
        # Check size
        size_ok, size_issues, size_stats = self.check_size()
        all_issues.extend(size_issues)
        database_stats.update(size_stats)
        
        # Check performance
        perf_ok, perf_issues, perf_stats = self.check_performance()
        all_issues.extend(perf_issues)
        database_stats.update(perf_stats)
        
        # Check configuration
        config_ok, config_issues, config_stats = self.check_configuration()
        all_issues.extend(config_issues)
        database_stats.update(config_stats)
        
        # Generate recommendations
        if database_stats.get("size_mb", 0) > 500:
            all_recommendations.append("Consider vacuuming database to reclaim space")
        
        if database_stats.get("wal_size_mb", 0) > 50:
            all_recommendations.append("WAL file is large - checkpoint may be needed")
        
        if perf_stats.get("conversations", 0) > 5000:
            all_recommendations.append("Consider archiving old conversations")
        
        # Determine status
        if not integrity_ok:
            status = "unhealthy"
        elif len(all_issues) > 2:
            status = "degraded"
        elif all_issues:
            status = "degraded"
        else:
            status = "healthy"
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            database=database_stats,
            issues=all_issues,
            recommendations=all_recommendations,
        )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check Neural Terminal database health"
    )
    parser.add_argument(
        "--db-path",
        help="Path to database file (default: from settings)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with non-zero code if unhealthy",
    )
    
    args = parser.parse_args()
    
    checker = DatabaseHealthChecker(args.db_path)
    result = checker.run_health_check()
    
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"Database Health Check: {result.status.upper()}")
        print("=" * 60)
        print(f"Timestamp: {result.timestamp}")
        print(f"\nDatabase Stats:")
        print("-" * 40)
        for key, value in result.database.items():
            print(f"  {key}: {value}")
        
        if result.issues:
            print(f"\n⚠️  Issues Found ({len(result.issues)}):")
            print("-" * 40)
            for issue in result.issues:
                print(f"  • {issue}")
        else:
            print("\n✅ No issues found")
        
        if result.recommendations:
            print(f"\n💡 Recommendations:")
            print("-" * 40)
            for rec in result.recommendations:
                print(f"  • {rec}")
        
        print("=" * 60 + "\n")
    
    if args.exit_code and result.status == "unhealthy":
        sys.exit(1)
    elif args.exit_code and result.status == "degraded":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
