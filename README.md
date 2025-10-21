# ABS Automatic Rebate Calculator

This is a simple Flask application to automatically calculate customer rebates based on service downtime.

## Features
-   Calculates rebates based on monthly fee, start time, and end time.
-   Loads a subscriber list from a `subscribers.json` file.
-   Searchable dropdown menu to find subscribers by name or account number.

## How to Run Locally
1.  Install requirements: `pip install -r requirements.txt`
2.  Run the app: `python app.py`
3.  Open `http://127.0.0.1:5000` in your browser.