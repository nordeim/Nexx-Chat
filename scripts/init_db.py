#!/usr/bin/env python3
"""
Production Database Initialization Script for Neural Terminal.

This script ensures the database is properly configured for production use:
- Validates database integrity
- Optimizes SQLite settings
- Creates necessary indexes
- Sets up WAL mode for concurrent access
- Validates schema against ORM models
"""

import os
import sys
import sqlite3
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from neural_terminal.config import settings
from neural_terminal.infrastructure.database import (
    init_db,
    engine,
    Base,
    ConversationORM,
    MessageORM,
)
from sqlalchemy import inspect, text


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Production database initialization manager."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path.
        
        Args:
            db_path: Path to SQLite database file. Uses settings if not provided.
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = settings.db_path
        
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """Connect to database with optimized settings.
        
        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # Wait up to 30s for locks
            isolation_level=None,  # Autocommit mode for PRAGMAs
        )
        conn.row_factory = sqlite3.Row
        return conn
    
    def validate_integrity(self) -> bool:
        """Validate database integrity.
        
        Returns:
            True if database is valid
        
        Raises:
            RuntimeError: If corruption detected
        """
        logger.info("Validating database integrity...")
        
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            
            if result[0] != "ok":
                raise RuntimeError(f"Database corruption detected: {result[0]}")
            
            # Check foreign key constraints
            cursor.execute("PRAGMA foreign_key_check;")
            fk_violations = cursor.fetchall()
            
            if fk_violations:
                violations_str = "\n".join(str(v) for v in fk_violations)
                raise RuntimeError(f"Foreign key violations found:\n{violations_str}")
            
            logger.info("✅ Database integrity validated")
            return True
            
        finally:
            conn.close()
    
    def optimize_production_settings(self) -> None:
        """Optimize SQLite for production use."""
        logger.info("Applying production optimizations...")
        
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL;")
            result = cursor.fetchone()
            if result[0] != "wal":
                raise RuntimeError(f"Failed to enable WAL mode: {result[0]}")
            
            # Set synchronous mode to NORMAL for balance of safety/performance
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
            # Increase cache size (negative = KB, -64000 = ~64MB)
            cursor.execute("PRAGMA cache_size=-64000;")
            
            # Enable memory-mapped I/O for reads (256MB)
            cursor.execute("PRAGMA mmap_size=268435456;")
            
            # Set temp store to memory for better performance
            cursor.execute("PRAGMA temp_store=memory;")
            
            # Increase page size for better I/O (4096 bytes)
            cursor.execute("PRAGMA page_size=4096;")
            
            logger.info("✅ Production optimizations applied")
            
        finally:
            conn.close()
    
    def create_indexes(self) -> None:
        """Create performance indexes."""
        logger.info("Creating indexes...")
        
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Index on conversation_id for messages (already exists from FK, but verify)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON messages(conversation_id);
            """)
            
            # Index on created_at for message ordering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created_at 
                ON messages(created_at);
            """)
            
            # Index on updated_at for conversation sorting
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_updated_at 
                ON conversations(updated_at DESC);
            """)
            
            # Index on status for active conversation queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_status 
                ON conversations(status);
            """)
            
            # Index on model_id for filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_model_id 
                ON conversations(model_id);
            """)
            
            logger.info("✅ Indexes created")
            
        finally:
            conn.close()
    
    def verify_schema(self) -> bool:
        """Verify database schema matches ORM models.
        
        Returns:
            True if schema is valid
        """
        logger.info("Verifying database schema...")
        
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(f"sqlite:///{self.db_path}")
        
        try:
            inspector = inspect(engine)
            
            # Get actual tables
            actual_tables = set(inspector.get_table_names())
            expected_tables = {"conversations", "messages"}
            
            if actual_tables != expected_tables:
                missing = expected_tables - actual_tables
                extra = actual_tables - expected_tables
                logger.error(f"Schema mismatch! Missing: {missing}, Extra: {extra}")
                return False
            
            # Verify columns in conversations table
            conv_columns = {col["name"] for col in inspector.get_columns("conversations")}
            expected_conv_columns = {
                "id", "title", "model_id", "status", "created_at",
                "updated_at", "total_cost", "total_tokens",
                "parent_conversation_id", "tags"
            }
            
            if conv_columns != expected_conv_columns:
                missing = expected_conv_columns - conv_columns
                extra = conv_columns - expected_conv_columns
                logger.error(f"Conversations table mismatch! Missing: {missing}, Extra: {extra}")
                return False
            
            # Verify columns in messages table
            msg_columns = {col["name"] for col in inspector.get_columns("messages")}
            expected_msg_columns = {
                "id", "conversation_id", "role", "content", "prompt_tokens",
                "completion_tokens", "total_tokens", "cost", "latency_ms",
                "model_id", "created_at", "metadata"
            }
            
            if msg_columns != expected_msg_columns:
                missing = expected_msg_columns - msg_columns
                extra = msg_columns - expected_msg_columns
                logger.error(f"Messages table mismatch! Missing: {missing}, Extra: {extra}")
                return False
            
            logger.info("✅ Schema verification passed")
            return True
            
        finally:
            engine.dispose()
    
    def get_stats(self) -> dict:
        """Get database statistics.
        
        Returns:
            Dictionary of statistics
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM conversations;")
            conversation_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages;")
            message_count = cursor.fetchone()[0]
            
            # Get database file size
            file_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Get WAL file size
            wal_path = Path(str(self.db_path) + "-wal")
            wal_size = wal_path.stat().st_size if wal_path.exists() else 0
            
            # Get settings
            cursor.execute("PRAGMA journal_mode;")
            journal_mode = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA synchronous;")
            synchronous = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA cache_size;")
            cache_size = cursor.fetchone()[0]
            
            return {
                "conversations": conversation_count,
                "messages": message_count,
                "file_size_bytes": file_size,
                "wal_size_bytes": wal_size,
                "journal_mode": journal_mode,
                "synchronous": synchronous,
                "cache_size": cache_size,
                "path": str(self.db_path),
            }
            
        finally:
            conn.close()
    
    def backup(self, backup_dir: Optional[Path] = None) -> Path:
        """Create database backup.
        
        Args:
            backup_dir: Directory for backup. Uses ./backups if not specified.
            
        Returns:
            Path to backup file
        """
        if backup_dir is None:
            backup_dir = Path(__file__).parent.parent / "backups"
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"neural_terminal_backup_{timestamp}.db"
        
        logger.info(f"Creating backup at {backup_path}...")
        
        # Use SQLite backup API for online backup
        source = sqlite3.connect(str(self.db_path))
        try:
            backup = sqlite3.connect(str(backup_path))
            try:
                source.backup(backup)
                logger.info(f"✅ Backup created: {backup_path}")
                return backup_path
            finally:
                backup.close()
        finally:
            source.close()
    
    def vacuum(self) -> None:
        """Compact database file."""
        logger.info("Vacuuming database...")
        
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("VACUUM;")
            logger.info("✅ Database vacuumed")
        finally:
            conn.close()
    
    def init_production(self) -> bool:
        """Complete production initialization.
        
        Returns:
            True if successful
        """
        try:
            logger.info("=" * 60)
            logger.info("Neural Terminal Database Initialization")
            logger.info("=" * 60)
            
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create/update schema
            logger.info("Creating/updating schema...")
            init_db()
            
            # Validate integrity
            self.validate_integrity()
            
            # Apply optimizations
            self.optimize_production_settings()
            
            # Create indexes
            self.create_indexes()
            
            # Verify schema
            if not self.verify_schema():
                raise RuntimeError("Schema verification failed")
            
            # Get stats
            stats = self.get_stats()
            
            logger.info("-" * 60)
            logger.info("Database Initialization Complete")
            logger.info("-" * 60)
            logger.info(f"Path: {stats['path']}")
            logger.info(f"Conversations: {stats['conversations']}")
            logger.info(f"Messages: {stats['messages']}")
            logger.info(f"File Size: {stats['file_size_bytes']:,} bytes")
            logger.info(f"Journal Mode: {stats['journal_mode'].upper()}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize Neural Terminal database for production"
    )
    parser.add_argument(
        "--db-path",
        help="Path to database file (default: from settings)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before initialization",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Vacuum database after initialization",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only",
    )
    
    args = parser.parse_args()
    
    initializer = DatabaseInitializer(args.db_path)
    
    if args.stats:
        stats = initializer.get_stats()
        print("\nDatabase Statistics:")
        print("-" * 40)
        for key, value in stats.items():
            print(f"{key}: {value}")
        return
    
    # Create backup if requested
    if args.backup:
        initializer.backup()
    
    # Initialize
    success = initializer.init_production()
    
    # Vacuum if requested
    if success and args.vacuum:
        initializer.vacuum()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
