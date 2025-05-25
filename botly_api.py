from flask import Flask, jsonify
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

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

    matching_rows = df[df["Room Number"].astype(str).str.upper().str.strip() == room_id]
    if matching_rows.empty:
        return jsonify({"error": "Room not found"}), 404

    # ניקח את השורה הראשונה לסוג חדר ותאריך
    first_row = matching_rows.iloc[0]
    room_type = first_row.get("Type of room", "").strip()
    documents_supplied = str(first_row.get("מסמכים סופקו", "")).strip() == "כן"

    # תאריך
    date_value = first_row.get("Commissioning Due Date", "")
    try:
        due_date = pd.to_datetime(date_value).date()
    except Exception:
        due_date = None

    # גופי תאורה
    fixtures = []
    for _, row in matching_rows.iterrows():
        fixtures.append({
            "family": row.get("Family", "").strip(),
            "type": row.get("Type", "").strip(),
            "quantity": int(row.get("Quantity", 0))
        })

    return jsonify({
        "room_id": room_id,
        "room_type": room_type,
        "documents_supplied": documents_supplied,
        "commissioning_due_date": due_date.isoformat() if due_date else None,
        "today": datetime.today().date().isoformat(),
        "fixtures": fixtures
    })

if __name__ == "__main__":
    app.run(debug=True, port=8080)
