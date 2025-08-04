#!/usr/bin/env python3
"""
Script to validate database index migrations and provide deployment guidance.
"""

import os
import sys
import re
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def validate_migration_file(file_path):
    """Validate a migration file for proper index creation syntax."""
    issues = []
    positives = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for CONCURRENT index creation
    if "CREATE INDEX" in content and "CONCURRENTLY" not in content:
        issues.append("❌ Non-concurrent index creation found - may cause table locks")
    
    # Check for IF NOT EXISTS
    if "CREATE INDEX" in content and "IF NOT EXISTS" not in content:
        issues.append("⚠️  Missing IF NOT EXISTS - may fail on re-run")
    
    # Check for proper DROP statements in reverse_sql
    create_count = content.count("CREATE INDEX")
    drop_count = content.count("DROP INDEX")
    if create_count != drop_count:
        issues.append(f"❌ Mismatch: {create_count} CREATE vs {drop_count} DROP statements")
    
    # Check for positive indicators
    partial_indexes = content.count("WHERE")
    if partial_indexes > 0:
        positives.append(f"✅ {partial_indexes} partial indexes found (good for performance)")
    
    if "CONCURRENTLY" in content:
        positives.append("✅ Uses CONCURRENT index creation (production-safe)")
    
    if "IF NOT EXISTS" in content:
        positives.append("✅ Uses IF NOT EXISTS (re-runnable)")
    
    return issues, positives

def main():
    """Main validation function."""
    print("🔍 Validating Database Index Migrations")
    print("=" * 50)
    
    # Define migration files to check
    migration_files = [
        "apps/forum_integration/migrations/0006_add_performance_indexes.py",
        "apps/learning/migrations/0005_add_performance_indexes.py", 
        "apps/users/migrations/0002_add_performance_indexes.py"
    ]
    
    all_issues = []
    
    for migration_file in migration_files:
        file_path = project_root / migration_file
        if not file_path.exists():
            print(f"❌ Missing: {migration_file}")
            all_issues.append(f"Missing migration file: {migration_file}")
            continue
            
        print(f"\n📄 Checking: {migration_file}")
        issues, positives = validate_migration_file(file_path)
        
        for positive in positives:
            print(f"   {positive}")
        
        if not issues:
            print("   ✅ All checks passed")
        else:
            for issue in issues:
                print(f"   {issue}")
                all_issues.append(f"{migration_file}: {issue}")
    
    # Check management command
    command_file = project_root / "apps/forum_integration/management/commands/add_machina_indexes.py"
    if command_file.exists():
        print(f"\n📄 Checking: add_machina_indexes.py")
        print("   ✅ Management command found")
    else:
        print("   ❌ Management command missing")
        all_issues.append("Missing add_machina_indexes management command")
    
    # Summary
    print("\n" + "=" * 50)
    if not all_issues:
        print("🎉 All validations passed!")
        print("\n📋 Deployment Instructions:")
        print("1. python manage.py migrate forum_integration 0006")
        print("2. python manage.py migrate learning 0005")
        print("3. python manage.py migrate users 0002") 
        print("4. python manage.py add_machina_indexes")
        print("5. Run VACUUM ANALYZE; after all indexes are created")
    else:
        print(f"❌ Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"   - {issue}")
        sys.exit(1)
    
    print("\n🔍 Monitor Performance:")
    print("- Use EXPLAIN ANALYZE on critical queries")
    print("- Check pg_stat_user_indexes for usage statistics")
    print("- Monitor query execution times before/after")

if __name__ == "__main__":
    main()