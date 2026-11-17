from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from datetime import datetime, timezone
import json
import os
import re

load_dotenv(dotenv_path=".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-later")

client = MongoClient(
    host=os.getenv("MONGO_HOST"),
    port=int(os.getenv("MONGO_PORT")),
    username=os.getenv("MONGO_USER"),
    password=os.getenv("MONGO_PASSWORD"),
    authSource="admin",
    serverSelectionTimeoutMS=5000
)

db = client[os.getenv("MONGO_DATABASE")]
submissions = db["submissions"]


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        if not name or not email:
            return render_template(
                "index.html",
                error="Please fill in all fields.",
                name=name,
                email=email
            )

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return render_template(
                "index.html",
                error="Please enter a valid email address.",
                name=name,
                email=email
            )

        try:
            client.admin.command("ping")

            submissions.insert_one({
                "name": name,
                "email": email,
                "created_at": datetime.now(timezone.utc)
            })

            flash(name, "success")
            return redirect(url_for("success"))

        except PyMongoError:
            return render_template(
                "index.html",
                error="Database connection failed. Please try again.",
                name=name,
                email=email
            )

    return render_template("index.html")


@app.route("/success")
def success():
    messages = flash_messages = None
    from flask import get_flashed_messages
    messages = get_flashed_messages(category_filter=["success"])

    if not messages:
        return redirect(url_for("home"))

    return render_template("success.html", name=messages[0])


@app.route("/api", methods=["GET"])
def get_users():
    try:
        data_file = os.path.join(app.root_path, "data", "users.json")

        with open(data_file, "r") as file:
            users = json.load(file)

        return jsonify(users), 200

    except FileNotFoundError:
        return jsonify({"error": "Data file not found"}), 404

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON data"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
