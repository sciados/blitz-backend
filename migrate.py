# migrate.py
"""
Database migration management script
Run migrations easily without needing pgAdmin
"""
import subprocess
import sys

def run_command(command):
    """Run a shell command and print output."""
    print(f"\n🚀 Running: {command}\n")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode

def main():
    if len(sys.argv) < 2:
        print("""
Blitz Database Migration Tool

Usage:
    python migrate.py init          # Initialize Alembic (first time only)
    python migrate.py migrate       # Create a new migration
    python migrate.py upgrade       # Apply all pending migrations
    python migrate.py downgrade     # Rollback last migration
    python migrate.py current       # Show current migration version
    python migrate.py history       # Show migration history
    python migrate.py reset         # Reset database (DANGER!)
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        print("🔧 Initializing Alembic...")
        run_command("alembic init alembic")
        print("✅ Alembic initialized! Now configure alembic/env.py")
    
    elif command == "migrate":
        message = input("Enter migration message: ")
        run_command(f'alembic revision --autogenerate -m "{message}"')
        print("✅ Migration created!")
    
    elif command == "upgrade":
        run_command("alembic upgrade head")
        print("✅ Database upgraded to latest version!")
    
    elif command == "downgrade":
        run_command("alembic downgrade -1")
        print("✅ Rolled back one migration!")
    
    elif command == "current":
        run_command("alembic current")
    
    elif command == "history":
        run_command("alembic history --verbose")
    
    elif command == "reset":
        confirm = input("⚠️  This will DROP ALL TABLES! Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            run_command("alembic downgrade base")
            print("✅ Database reset complete!")
        else:
            print("❌ Reset cancelled")
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()