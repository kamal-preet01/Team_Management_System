# initialize_db.py
import json
from auth_utils import hash_password
from config import USERS_DB, TASKS_DB, MESSAGES_DB


def initialize_database():
    # Default boss credentials
    default_boss = {
        "Shammi Kapoor": {
            "password": hash_password("admin123"),
            "role": "boss"
        }
    }

    # Initialize users database with default boss
    with open(USERS_DB, 'w') as f:
        json.dump(default_boss, f, indent=4)

    # Initialize empty tasks database
    with open(TASKS_DB, 'w') as f:
        json.dump({}, f, indent=4)

    # Initialize empty messages database
    with open(MESSAGES_DB, 'w') as f:
        json.dump({}, f, indent=4)

    print("Database initialized successfully!")
    print("Default boss credentials:")
    print("Username: Shammi Kapoor")
    print("Password: admin123")


if __name__ == "__main__":
    initialize_database()