#!/usr/bin/env python3
"""Purge old conversations from the database.

This script removes conversations that are older than a specified number of days,
or all conversations if --all flag is provided.

Usage:
    python scripts/purge_conversations.py              # Delete conversations older than 30 days
    python scripts/purge_conversations.py --days 7     # Delete conversations older than 7 days
    python scripts/purge_conversations.py --all        # Delete ALL conversations
    python scripts/purge_conversations.py --dry-run    # Show what would be deleted
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from neural_terminal.config import settings


def get_engine():
    """Create database engine."""
    return create_engine(settings.database_url)


def purge_conversations(days: int = 30, dry_run: bool = False, delete_all: bool = False) -> tuple[int, int]:
    """Purge old conversations from database.
    
    Args:
        days: Delete conversations older than this many days
        dry_run: If True, only show what would be deleted
        delete_all: If True, delete all conversations
        
    Returns:
        Tuple of (conversations_deleted, messages_deleted)
    """
    engine = get_engine()
    
    with engine.connect() as conn:
        if delete_all:
            # Get counts before deletion
            conv_count = conn.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
            msg_count = conn.execute(text("SELECT COUNT(*) FROM messages")).scalar()
            
            if dry_run:
                print(f"[DRY RUN] Would delete {conv_count} conversations and {msg_count} messages")
                return 0, 0
            
            # Delete all
            conn.execute(text("DELETE FROM messages"))
            conn.execute(text("DELETE FROM conversations"))
            conn.commit()
            print(f"Deleted {conv_count} conversations and {msg_count} messages")
            return conv_count, msg_count
        
        else:
            # Calculate cutoff date
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get IDs of conversations to delete
            result = conn.execute(
                text("SELECT id FROM conversations WHERE updated_at < :cutoff"),
                {"cutoff": cutoff}
            )
            conv_ids = [row[0] for row in result]
            
            if not conv_ids:
                print(f"No conversations older than {days} days found")
                return 0, 0
            
            conv_count = len(conv_ids)
            
            # Count messages to delete
            msg_count = conn.execute(
                text("SELECT COUNT(*) FROM messages WHERE conversation_id IN :conv_ids"),
                {"conv_ids": tuple(conv_ids)}
            ).scalar()
            
            if dry_run:
                print(f"[DRY RUN] Would delete {conv_count} conversations and {msg_count} messages")
                return 0, 0
            
            # Delete messages first (foreign key constraint)
            conn.execute(
                text("DELETE FROM messages WHERE conversation_id IN :conv_ids"),
                {"conv_ids": tuple(conv_ids)}
            )
            
            # Delete conversations
            conn.execute(
                text("DELETE FROM conversations WHERE id IN :conv_ids"),
                {"conv_ids": tuple(conv_ids)}
            )
            
            conn.commit()
            print(f"Deleted {conv_count} conversations and {msg_count} messages older than {days} days")
            return conv_count, msg_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Purge old conversations from the database"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Delete conversations older than this many days (default: 30)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Delete ALL conversations"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("=== DRY RUN MODE ===")
    
    try:
        purge_conversations(
            days=args.days,
            dry_run=args.dry_run,
            delete_all=args.all
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
