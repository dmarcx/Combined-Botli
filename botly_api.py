from flask import Flask, jsonify
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load the Excel files once
above = pd.read_excel("Lighting_AboveGround.xlsx")
below = pd.read_excel("Lighting_BelowGround.xlsx")


def get_room_dataframe(room_id):
    if room_id.upper().startswith("L"):
        return above
    elif room_id.upper().startswith("P"):
        return below
    return None


def clean_room_id(room_id):
    return room_id.strip().upper()


@app.route("/api/room/<room_id>", methods=["GET"])
def get_room_data(room_id):
    room_id = clean_room_id(room_id)
    df = get_room_dataframe(room_id)
    if df is None:
        return jsonify({"error": "Invalid room prefix"}), 400

    row = df[df["Room Number"].astype(str).str.upper().str.strip() == room_id]
    if row.empty:
        return jsonify({"error": "Room not found"}), 404

    row = row.iloc[0]
    room_type = row.get("Type of Room", "").strip()
    documents_supplied = row.get("Documents Supplied", "").strip() == "כן"

    date_str = row.get("Commissioning Due Date", "").strip()
    try:
        due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        due_date = None

    return jsonify({
        "room_id": room_id,
        "room_type": room_type,
        "documents_supplied": documents_supplied,
        "commissioning_due_date": due_date.isoformat() if due_date else None,
        "today": datetime.today().date().isoformat()
    })


if __name__ == "__main__":
    app.run(debug=True, port=8080)
