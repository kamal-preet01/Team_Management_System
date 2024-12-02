# config.py
import os
import sqlite3
from pathlib import Path

# Ensure data directory exists
BASE_DIR = Path("data")
BASE_DIR.mkdir(exist_ok=True)

# SQLite database path
DATABASE_PATH = BASE_DIR / "team_task_manager.db"