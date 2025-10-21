import sqlite3
import json

DATABASE_FILE = "subscribers.db"
JSON_FILE = "subscribers.json"  #


def initialize_database():
    """
    Creates a new SQLite database and migrates data from subscribers.json.
    """
    # Connect to (and create) the database file
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # --- Create the subscribers table ---
    # We add 'id' as a primary key for easy editing/deleting later
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region TEXT NOT NULL,
        account_number TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        monthly_fee REAL NOT NULL
    );
    """
    )
    print("Table 'subscribers' created successfully.")

    # --- Load data from JSON ---
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            all_subscribers = json.load(f)  #

        # --- Insert data into the database ---
        total_added = 0
        for region, accounts in all_subscribers.items():
            for acc_num, details in accounts.items():
                try:
                    cursor.execute(
                        "INSERT INTO subscribers (region, account_number, name, monthly_fee) VALUES (?, ?, ?, ?)",
                        (region, acc_num, details["name"], details["monthly_fee"]),
                    )
                    total_added += 1
                except sqlite3.IntegrityError:
                    # This will catch if you try to run it twice (UNIQUE constraint)
                    print(f"Skipping duplicate account: {acc_num}")
                except KeyError:
                    print(f"Skipping malformed entry for account: {acc_num}")

        conn.commit()
        print(f"Successfully added {total_added} subscribers to the database.")

    except FileNotFoundError:
        print(f"Error: {JSON_FILE} not found. Cannot populate database.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode {JSON_FILE}. Check for syntax errors.")

    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    initialize_database()
