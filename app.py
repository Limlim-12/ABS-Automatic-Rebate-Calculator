from flask import Flask, render_template, request, redirect, url_for, flash
from rebate_calculator import calculate_rebate
from datetime import datetime
import csv
import os
import sqlite3

app = Flask(__name__)
# --- ADDED: A secret key is required for 'flash' messages
app.secret_key = "your_super_secret_key_change_this"

# --- Define database and history file settings
DATABASE_FILE = "subscribers.db"
HISTORY_FILE = "history.csv"
HISTORY_HEADERS = [
    "Timestamp",
    "Region",
    "Account Number",
    "Subscriber Name",
    "Monthly Fee",
    "Downtime Start",
    "Downtime End",
    "Total Rebate",
]


# --- Helper function to get a database connection
def get_db_conn():
    """Connects to the database and returns a connection object."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# --- Helper function to load subscribers for the form
def get_subscribers_for_form():
    """
    Fetches all subscribers from the DB and formats them
    into the nested dictionary that the JavaScript in index.html expects.
    """
    conn = get_db_conn()
    all_subs = conn.execute("SELECT * FROM subscribers ORDER BY name").fetchall()
    conn.close()

    subscribers_data = {}
    for sub in all_subs:
        region = sub["region"]
        if region not in subscribers_data:
            subscribers_data[region] = {}

        subscribers_data[region][sub["account_number"]] = {
            "name": sub["name"],
            "monthly_fee": sub["monthly_fee"],
        }
    return subscribers_data


def parse_datetime(value):
    """Safely parse both 'YYYY-MM-DDTHH:MM' and 'YYYY-MM-DD HH:MM' formats."""
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {value}")


def write_to_history(data):
    """Appends a new calculation to the history.csv file."""
    file_exists = os.path.isfile(HISTORY_FILE)

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


#
# --- ⭐️ MAIN CALCULATOR ROUTES ⭐️ ---
#
@app.route("/", methods=["GET", "POST"])
def index():
    """
    Home route - renders input form and results.
    """
    if request.method == "POST":
        try:
            # (Form processing logic...)
            region = request.form.get("region")
            account_number = request.form.get("account_number")
            monthly_fee_fallback = float(request.form["monthly_fee"])
            start_time_str = request.form["start_time"]
            end_time_str = request.form["end_time"]

            start_time = parse_datetime(start_time_str)
            end_time = parse_datetime(end_time_str)

            if end_time < start_time:
                return render_template(
                    "result.html",
                    result=None,
                    error="Error: 'Downtime End' cannot be earlier than 'Downtime Start'. Please go back and correct the times.",
                )

            # Lookup subscriber from database
            conn = get_db_conn()
            subscriber_info = conn.execute(
                "SELECT * FROM subscribers WHERE account_number = ?", (account_number,)
            ).fetchone()
            conn.close()

            if subscriber_info:
                subscriber_name = subscriber_info["name"]
                monthly_fee = float(subscriber_info["monthly_fee"])
            else:
                subscriber_name = "Unknown Subscriber"
                monthly_fee = monthly_fee_fallback

            result = calculate_rebate(monthly_fee, start_time, end_time)

            # Save successful calculation to history
            try:
                history_data = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Region": region,
                    "Account Number": account_number,
                    "Subscriber Name": subscriber_name,
                    "Monthly Fee": monthly_fee,
                    "Downtime Start": start_time_str,
                    "Downtime End": end_time_str,
                    "Total Rebate": result["total_rebate_rounded"],
                }
                write_to_history(history_data)
            except Exception as e:
                print(f"Warning: Failed to write to history file. Error: {e}")

            return render_template(
                "result.html",
                result=result,
                region=region,
                account_number=account_number,
                subscriber_name=subscriber_name,
                monthly_fee=monthly_fee,
                start_time=start_time_str,
                end_time=end_time_str,
                error=None,
            )

        except Exception as e:
            return render_template(
                "result.html",
                result=None,
                error=f"Error: {str(e)}",
            )

    # Default view now loads from database
    subscribers_for_js = get_subscribers_for_form()
    return render_template("index.html", subscribers=subscribers_for_js)


@app.route("/history")
def history():
    """Displays the calculation history."""
    history_records = []
    if os.path.isfile(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            history_records = list(reader)
            history_records.reverse()

    return render_template(
        "history.html", history=history_records, headers=HISTORY_HEADERS
    )


#
# --- ⭐️ NEW ADMIN PANEL ROUTES ⭐️ ---
#
@app.route("/admin")
def admin():
    """Display the admin panel with all subscribers."""
    conn = get_db_conn()
    all_subscribers = conn.execute(
        "SELECT * FROM subscribers ORDER BY region, name"
    ).fetchall()
    conn.close()
    return render_template("admin.html", subscribers=all_subscribers)


@app.route("/add", methods=["GET", "POST"])
def add_subscriber():
    """Handle adding a new subscriber."""
    if request.method == "POST":
        region = request.form.get("region")
        account_number = request.form.get("account_number")
        name = request.form.get("name")
        monthly_fee = request.form.get("monthly_fee")

        if not all([region, account_number, name, monthly_fee]):
            flash("All fields are required.", "error")
            return redirect(url_for("add_subscriber"))

        try:
            conn = get_db_conn()
            conn.execute(
                "INSERT INTO subscribers (region, account_number, name, monthly_fee) VALUES (?, ?, ?, ?)",
                (region, account_number, name, float(monthly_fee)),
            )
            conn.commit()
            conn.close()
            flash(f"Success! Subscriber '{name}' added.", "success")
            return redirect(url_for("admin"))

        except sqlite3.IntegrityError:
            flash(f"Error: Account number '{account_number}' already exists.", "error")
            conn.close()
        except ValueError:
            flash("Error: Monthly fee must be a valid number.", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")

        # If any error, stay on the page and show flashed message
        return redirect(url_for("add_subscriber"))

    # GET request just shows the form
    return render_template("subscriber_form.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_subscriber(id):
    """Handle editing an existing subscriber."""
    conn = get_db_conn()

    if request.method == "POST":
        region = request.form.get("region")
        account_number = request.form.get("account_number")
        name = request.form.get("name")
        monthly_fee = request.form.get("monthly_fee")

        if not all([region, account_number, name, monthly_fee]):
            flash("All fields are required.", "error")
            return redirect(url_for("edit_subscriber", id=id))

        try:
            conn.execute(
                """UPDATE subscribers 
                   SET region = ?, account_number = ?, name = ?, monthly_fee = ?
                   WHERE id = ?""",
                (region, account_number, name, float(monthly_fee), id),
            )
            conn.commit()
            flash(f"Success! Subscriber '{name}' updated.", "success")
            return redirect(url_for("admin"))

        except sqlite3.IntegrityError:
            flash(
                f"Error: Account number '{account_number}' already exists for another user.",
                "error",
            )
        except ValueError:
            flash("Error: Monthly fee must be a valid number.", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")

        # If any error, stay on the page
        return redirect(url_for("edit_subscriber", id=id))

    # GET request: fetch the user and show the form
    subscriber_to_edit = conn.execute(
        "SELECT * FROM subscribers WHERE id = ?", (id,)
    ).fetchone()
    conn.close()

    if subscriber_to_edit is None:
        flash("Subscriber not found.", "error")
        return redirect(url_for("admin"))

    return render_template("subscriber_form.html", subscriber=subscriber_to_edit)


@app.route("/delete/<int:id>", methods=["POST"])
def delete_subscriber(id):
    """Handle deleting a subscriber."""
    try:
        conn = get_db_conn()
        conn.execute("DELETE FROM subscribers WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash("Subscriber successfully deleted.", "success")
    except Exception as e:
        flash(f"An error occurred while deleting: {e}", "error")

    return redirect(url_for("admin"))


# --- END OF NEW ADMIN ROUTES ---

if __name__ == "__main__":
    app.run(debug=True)
