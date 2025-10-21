from flask import Flask, render_template, request
from rebate_calculator import calculate_rebate
from datetime import datetime
import json

app = Flask(__name__)


# Load your existing subscribers.json file
with open("subscribers.json", "r", encoding="utf-8") as f:
    subscribers = json.load(f)


def parse_datetime(value):
    """Safely parse both 'YYYY-MM-DDTHH:MM' and 'YYYY-MM-DD HH:MM' formats."""
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {value}")


import json
from flask import Flask, render_template, request
from datetime import datetime
from rebate_calculator import calculate_rebate, parse_datetime


app = Flask(__name__)

# ✅ Load subscriber list from JSON
with open("subscribers.json", "r", encoding="utf-8") as f:
    subscribers = json.load(f)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Home route - renders input form and results.
    """
    if request.method == "POST":
        try:
            # ✅ Collect form inputs
            region = request.form.get("region")
            account_number = request.form.get("account_number")
            monthly_fee = float(request.form["monthly_fee"])
            start_time_str = request.form["start_time"]
            end_time_str = request.form["end_time"]

            # ✅ Convert to datetime safely
            start_time = parse_datetime(start_time_str)
            end_time = parse_datetime(end_time_str)

            # ✅ Lookup subscriber name
            subscriber_info = subscribers.get(region, {}).get(account_number, {})
            subscriber_name = subscriber_info.get("name", "Unknown Subscriber")
            monthly_fee = float(subscriber_info.get("monthly_fee", request.form["monthly_fee"]))

            

            # ✅ Compute rebate using your existing logic
            result = calculate_rebate(monthly_fee, start_time, end_time)

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
            # Render error message cleanly
            return render_template(
                "result.html",
                result=None,
                error=f"Error: {str(e)}",
            )

    # Default view with subscriber data for dropdowns
    return render_template("index.html", subscribers=subscribers)


if __name__ == "__main__":
    app.run(debug=True)
