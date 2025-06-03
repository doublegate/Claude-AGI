#!/usr/bin/env python3
"""
Setup databases for Claude-AGI
==============================

This script helps set up PostgreSQL and Redis for development.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_command(cmd):
    """Check if a command is available"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_postgresql():
    """Setup PostgreSQL database"""
    print("\n=== Setting up PostgreSQL ===")
    
    if not check_command("psql"):
        print("PostgreSQL is not installed. Please install it first:")
        print("  Ubuntu/Debian: sudo apt install postgresql postgresql-contrib")
        print("  macOS: brew install postgresql")
        print("  Fedora: sudo dnf install postgresql postgresql-server")
        return False
    
    print("Creating database and user...")
    
    # SQL commands to set up database
    sql_commands = """
-- Create user if not exists
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'claude_agi') THEN
      CREATE ROLE claude_agi WITH LOGIN PASSWORD 'password';
   END IF;
END
$$;

-- Create databases
CREATE DATABASE IF NOT EXISTS claude_consciousness;
CREATE DATABASE IF NOT EXISTS claude_agi_dev;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE claude_consciousness TO claude_agi;
GRANT ALL PRIVILEGES ON DATABASE claude_agi_dev TO claude_agi;

-- Create pgvector extension (for Phase 2)
\c claude_consciousness
CREATE EXTENSION IF NOT EXISTS vector;

\c claude_agi_dev
CREATE EXTENSION IF NOT EXISTS vector;
"""
    
    try:
        # Write SQL to temp file
        sql_file = Path("/tmp/claude_agi_setup.sql")
        sql_file.write_text(sql_commands)
        
        # Execute SQL
        subprocess.run(
            ["sudo", "-u", "postgres", "psql", "-f", str(sql_file)],
            check=True
        )
        
        print("✓ PostgreSQL setup complete")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error setting up PostgreSQL: {e}")
        print("\nYou can manually run these commands as postgres user:")
        print(sql_commands)
        return False
    finally:
        if sql_file.exists():
            sql_file.unlink()

def setup_redis():
    """Setup Redis"""
    print("\n=== Setting up Redis ===")
    
    if not check_command("redis-cli"):
        print("Redis is not installed. Please install it first:")
        print("  Ubuntu/Debian: sudo apt install redis-server")
        print("  macOS: brew install redis")
        print("  Fedora: sudo dnf install redis")
        return False
    
    # Check if Redis is running
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip() == "PONG":
            print("✓ Redis is already running")
            return True
    except subprocess.CalledProcessError:
        pass
    
    # Try to start Redis
    print("Starting Redis service...")
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["brew", "services", "start", "redis"], check=True)
        else:  # Linux
            subprocess.run(["sudo", "systemctl", "start", "redis"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "redis"], check=True)
        
        print("✓ Redis started successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error starting Redis: {e}")
        print("\nPlease start Redis manually and ensure it's running on port 6379")
        return False

def setup_directories():
    """Create necessary directories"""
    print("\n=== Creating directories ===")
    
    project_root = Path(__file__).parent.parent.parent
    directories = [
        project_root / "data",
        project_root / "data" / "faiss",
        project_root / "logs",
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True, parents=True)
        print(f"✓ Created {directory}")

def update_env_file():
    """Update .env file with database configuration"""
    print("\n=== Updating .env file ===")
    
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    # Read existing .env or .env.example
    if env_file.exists():
        content = env_file.read_text()
    elif env_example.exists():
        content = env_example.read_text()
    else:
        content = ""
    
    # Add database configuration if not present
    db_config = """
# Database Configuration
POSTGRES_URL=postgresql+asyncpg://claude_agi:password@localhost:5432/claude_consciousness
REDIS_URL=redis://localhost:6379/0
FAISS_INDEX_PATH=./data/faiss/index.bin
FAISS_DIMENSION=384  # For all-MiniLM-L6-v2 model
"""
    
    if "POSTGRES_URL" not in content:
        content += db_config
        env_file.write_text(content)
        print("✓ Added database configuration to .env")
    else:
        print("✓ Database configuration already in .env")

def main():
    """Main setup function"""
    print("Claude-AGI Database Setup")
    print("=" * 50)
    
    # Check if running with appropriate permissions
    if os.geteuid() != 0 and sys.platform != "darwin":
        print("\nNote: This script may need sudo permissions for some operations.")
        print("You may be prompted for your password.\n")
    
    # Setup components
    postgres_ok = setup_postgresql()
    redis_ok = setup_redis()
    setup_directories()
    update_env_file()
    
    # Summary
    print("\n" + "=" * 50)
    print("Setup Summary:")
    print(f"  PostgreSQL: {'✓ Ready' if postgres_ok else '✗ Manual setup required'}")
    print(f"  Redis: {'✓ Ready' if redis_ok else '✗ Manual setup required'}")
    print(f"  Directories: ✓ Created")
    print(f"  Environment: ✓ Updated")
    
    if postgres_ok and redis_ok:
        print("\n✓ All databases are ready!")
        print("\nTo enable database integration:")
        print("1. Edit configs/development.yaml")
        print("2. Set database.enabled: true")
        print("3. Run the application")
    else:
        print("\n⚠ Some databases need manual setup.")
        print("Please install and configure them before enabling database integration.")

if __name__ == "__main__":
    main()