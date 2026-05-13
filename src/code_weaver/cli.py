import os
import sys
import subprocess
import asyncio
import secrets
import socket
import argparse
from pathlib import Path
import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Define the global configuration directory
GLOBAL_CONFIG_DIR = Path.home() / ".code_weaver"
DB_PATH = GLOBAL_CONFIG_DIR / "chainlit.db"

async def init_db():
    """Initialize the database schema in the global config directory."""
    db_url = f"sqlite+aiosqlite:///{DB_PATH}"
    
    print("🛠️  Initializing Code Weaver database...")
    
    schema_queries = [
        """CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            identifier TEXT NOT NULL UNIQUE,
            metadata TEXT NOT NULL,
            createdAt TEXT
        );""",
        """CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            createdAt TEXT,
            name TEXT,
            userId TEXT,
            userIdentifier TEXT,
            tags TEXT,
            metadata TEXT,
            FOREIGN KEY (userId) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS steps (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            threadId TEXT NOT NULL,
            parentId TEXT,
            streaming INTEGER NOT NULL,
            waitForAnswer INTEGER,
            isError INTEGER,
            metadata TEXT,
            tags TEXT,
            input TEXT,
            output TEXT,
            createdAt TEXT,
            start TEXT,
            end TEXT,
            generation TEXT,
            showStep INTEGER,
            indent INTEGER,
            defaultOpen INTEGER,
            autoCollapse INTEGER,
            showInput TEXT,
            language TEXT,
            FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS elements (
            id TEXT PRIMARY KEY,
            threadId TEXT,
            type TEXT,
            url TEXT,
            chainlitKey TEXT,
            name TEXT NOT NULL,
            display TEXT,
            objectKey TEXT,
            size TEXT,
            page INTEGER,
            language TEXT,
            forId TEXT,
            mime TEXT,
            props TEXT,
            FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS feedbacks (
            id TEXT PRIMARY KEY,
            forId TEXT NOT NULL,
            threadId TEXT NOT NULL,
            value INTEGER NOT NULL,
            comment TEXT,
            FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
        );""",
    ]

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        for query in schema_queries:
            await conn.execute(text(query))
    await engine.dispose()
    print("✅ Database initialized successfully.")

def find_free_port(start_port=8000):
    """Find the next available port starting from start_port."""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

def init():
    """Initialize the project by creating default config files and DB in the global config directory."""
    print(f"Initializing Code Weaver in {GLOBAL_CONFIG_DIR}...")
    
    # Create the global directory if it doesn't exist
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define default config
    default_config = {
        "openai": {
            "api_key": "your-api-key-here",
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "temperature": 0.0
        },
        "paths": {
            "system_prompt": "system_prompt.md",
            "allowed_commands": [
                "pytest", "pip", "uv", "git", "ls", "dir", "mkdir", "echo", "python", "node", "npm",
                "yarn", "pnpm", "pwd", "whoami", "date", "go", "cargo", "rustc", "make", "cmake",
                "gcc", "clang", "ruff", "flake8", "black", "eslint", "prettier", "chainlit"
            ],
            "allowed_paths": [],
            "blocked_paths": []
        }
    }
    
    # Create config.yaml
    config_path = GLOBAL_CONFIG_DIR / "config.yaml"
    if not config_path.exists():
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)
        print(f"Created {config_path}")
    else:
        print(f"{config_path} already exists. Skipping.")

    # Create .env file
    env_path = GLOBAL_CONFIG_DIR / ".env"
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(f'CHAINLIT_AUTH_SECRET="{secrets.token_hex(32)}"\n')
        print(f"Created {env_path}")
    else:
        print(f"{env_path} already exists. Skipping.")

    # Create a default system_prompt.md if it doesn't exist
    prompt_path = GLOBAL_CONFIG_DIR / "system_prompt.md"
    if not prompt_path.exists():
        with open(prompt_path, "w") as f:
            f.write("# Code Weaver System Prompt\n\nYou are an expert AI coding agent...")
        print(f"Created {prompt_path}")
    else:
        print(f"{prompt_path} already exists. Skipping.")

    # Initialize Database
    asyncio.run(init_db())

    print(f"\nInitialization complete!")
    print("-" * 50)
    print(f"Your configuration files and database have been created at: {GLOBAL_CONFIG_DIR}")
    print("\nNEXT STEPS:")
    print(f"1. Open the following files in a text editor:")
    print(f"   - {GLOBAL_CONFIG_DIR / 'config.yaml'}  <-- Set your model and temperature")
    print(f"   - {GLOBAL_CONFIG_DIR / '.env'}         <-- Enter your OPENAI_API_KEY")
    print(f"   - {GLOBAL_CONFIG_DIR / 'system_prompt.md'} <-- Customize the agent's behavior")
    print("\n2. Once configured, you can start the server from ANY project folder:")
    print("   cd /path/to/your/project")
    print("   code_weaver serve")
    print("-" * 50)

def serve(port=None, host=None):
    """Start the server after verifying global config files."""
    print("Starting Code Weaver server...")
    
    # Verify required files in the global directory
    required_files = ["config.yaml", ".env", "system_prompt.md", "chainlit.db"]
    missing_files = [f for f in required_files if not (GLOBAL_CONFIG_DIR / f).exists()]
    
    if missing_files:
        print(f"Error: Missing required files in {GLOBAL_CONFIG_DIR}: {', '.join(missing_files)}")
        print("Please run 'code_weaver init' first.")
        sys.exit(1)
    
    # To make .env work from anywhere, we need to tell the system where it is
    env = os.environ.copy()
    try:
        with open(GLOBAL_CONFIG_DIR / ".env") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env[key] = value
    except Exception as e:
        print(f"Error reading .env file: {e}")
        sys.exit(1)

    # Set the database path environment variable so Chainlit knows where to look
    # Set the database path environment variable so Chainlit knows where to look
    # Instead of symlinking, we set the CHAINLIT_DATABASE_URL environment variable
    # which Chainlit uses to locate the database.
    env["CHAINLIT_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    # Handle port selection
    if port:
        final_port = str(port)
    else:
        final_port = str(find_free_port())
    
    # Handle host selection
    final_host = host if host else "localhost"
    
    print(f"🚀 Launching server on {final_host}:{final_port}...")

    # Start chainlit
    try:
        script_path = Path(__file__).parent / "web_ui.py"
        cmd = ["chainlit", "run", str(script_path), "--port", final_port]
        if host:
            cmd.extend(["--host", final_host])
            
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'chainlit' command not found. Please ensure dependencies are installed.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Code Weaver CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    subparsers.add_parser("init", help="Initialize configuration and database")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the Code Weaver server")
    serve_parser.add_argument("--port", type=int, help="Port to run the server on")
    serve_parser.add_argument("--host", type=str, help="Host to run the server on (defaults to localhost)")

    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "serve":
        serve(port=args.port, host=args.host)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()