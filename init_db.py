import sqlite3
import json

DATABASE_FILE = "subscribers.db"
JSON_FILE = "subscribers.json"  #


def initialize_database():
    """
    Creates/updates the SQLite database structure and migrates initial data.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # --- Create the subscribers table ---
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
    print("Table 'subscribers' checked/created successfully.")

    # --- Create the users table ---
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    );
    """
    )
    print("Table 'users' checked/created successfully.")

    conn.commit()  # Commit changes after creating tables

    # --- Load data from JSON (Only run if subscribers table is empty) ---
    cursor.execute("SELECT COUNT(*) FROM subscribers")
    subscriber_count = cursor.fetchone()[0]

    if subscriber_count == 0:
        print("Subscribers table is empty. Attempting data migration from JSON...")
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                all_subscribers = json.load(f)  #

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
                        print(f"Skipping duplicate account: {acc_num}")
                    except KeyError:
                        print(f"Skipping malformed entry for account: {acc_num}")

            conn.commit()  # Commit after inserting all subscribers
            print(f"Successfully added {total_added} subscribers to the database.")

        except FileNotFoundError:
            print(f"Warning: {JSON_FILE} not found. Cannot populate subscribers table.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode {JSON_FILE}. Check for syntax errors.")
    else:
        print("Subscribers table already populated. Skipping data migration.")

    conn.close()
    print("Database connection closed.")


# --- This block should only appear once ---
if __name__ == "__main__":
    initialize_database()
