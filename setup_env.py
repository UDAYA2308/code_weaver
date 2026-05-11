import os
import yaml
import secrets
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import sqlite3
import json

sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)


def setup_files():
    config_file = "config.yaml"
    env_file = ".env"
    if not os.path.exists(config_file):
        config_content = {
            "openai": {"api_key": "your_api_key_here", "model": "gpt-4o", "api_base_url": "https://api.openai.com/v1",
                       "temperature": 0.0},
            "paths": {"system_prompt": "system_prompt.md"},
            "agent": {"max_iterations": 10},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_content, f, default_flow_style=False)
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f'CHAINLIT_AUTH_SECRET="{secrets.token_hex(32)}"\n')


async def init_db():
    db_url = "sqlite+aiosqlite:///chainlit.db"

    print(f"🛠️  Checking Chainlit SQLAlchemy schema...")

    schema_queries = [
        """CREATE TABLE users (
            id TEXT PRIMARY KEY,
            identifier TEXT NOT NULL UNIQUE,
            metadata TEXT NOT NULL,
            createdAt TEXT
        );""",
        """CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            createdAt TEXT,
            name TEXT,
            userId TEXT,
            userIdentifier TEXT,
            tags TEXT,
            metadata TEXT,
            FOREIGN KEY (userId) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE steps (
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
        """CREATE TABLE elements (
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
        """CREATE TABLE feedbacks (
            id TEXT PRIMARY KEY,
            forId TEXT NOT NULL,
            threadId TEXT NOT NULL,
            value INTEGER NOT NULL,
            comment TEXT,
            FOREIGN KEY (threadId) REFERENCES threads(id) ON DELETE CASCADE
        );"""
    ]

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        for query in schema_queries:
            # Use IF NOT EXISTS to prevent errors on multiple runs
            if "CREATE TABLE" in query:
                query = query.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
            await conn.execute(text(query))
    await engine.dispose()
    print("✅ Database initialized successfully.")


if __name__ == "__main__":
    setup_files()
    asyncio.run(init_db())
