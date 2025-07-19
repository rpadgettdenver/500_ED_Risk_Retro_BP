#!/usr/bin/env python3
"""
🔄 Rollback Cleanup Script
Restores project to state before automated cleanup.

Usage: python scripts/rollback_cleanup.py
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def find_latest_backup():
    """Find the most recent backup directory"""
    project_root = Path(__file__).resolve().parent.parent
    backup_dir = project_root / "backup_before_cleanup"
    
    if not backup_dir.exists():
        print("❌ No backup directory found!")
        return None
    
    return backup_dir

def find_cleanup_log():
    """Find the most recent cleanup log"""
    project_root = Path(__file__).resolve().parent.parent
    log_files = list(project_root.glob("cleanup_log_*.json"))
    
    if not log_files:
        print("⚠️  No cleanup log found - proceeding with basic restore")
        return None
    
    # Get most recent log
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    return latest_log

def restore_from_backup():
    """Restore files from backup"""
    backup_dir = find_latest_backup()
    if not backup_dir:
        return False
    
    project_root = backup_dir.parent
    
    print(f"🔄 Restoring from backup: {backup_dir}")
    
    # Restore each backed up item
    for item in backup_dir.iterdir():
        if item.name.startswith('.'):
            continue
            
        src_path = item
        dst_path = project_root / item.name
        
        try:
            if dst_path.exists():
                if dst_path.is_dir():
                    shutil.rmtree(dst_path)
                else:
                    dst_path.unlink()
            
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            print(f"✓ Restored: {item.name}")
            
        except Exception as e:
            print(f"❌ Failed to restore {item.name}: {e}")
    
    return True

def main():
    """Main rollback function"""
    print("🔄 Project Cleanup Rollback")
    print("=" * 30)
    
    # Confirm with user
    response = input("⚠️  This will restore your project to pre-cleanup state. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Rollback cancelled.")
        return
    
    # Find and display cleanup log
    log_file = find_cleanup_log()
    if log_file:
        print(f"📋 Found cleanup log: {log_file.name}")
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        print(f"📊 Original cleanup performed {len(log_data)} actions")
    
    # Restore from backup
    if restore_from_backup():
        print("\n✅ Rollback completed successfully!")
        print("🗑️  You can now delete the backup_before_cleanup directory if desired")
    else:
        print("\n❌ Rollback failed!")

if __name__ == "__main__":
    main()
