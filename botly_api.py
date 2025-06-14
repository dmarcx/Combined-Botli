from flask import Flask, jsonify
import pandas as pd
from datetime import datetime

app = Flask(__name__)

@app.route("/health")
def health():
    # תשובה קצרה ומהירה • אין גישה לקבצים / DB כאן
    return "OK", 200

# Load Excel files once
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

def get_column_name(df, target_name):
    """Find actual column name in DataFrame by case-insensitive match."""
    for col in df.columns:
        if col.strip().lower() == target_name.strip().lower():
            return col
    return None

@app.route("/api/room/<room_id>", methods=["GET"])
def get_room_data(room_id):
    room_id = clean_room_id(room_id)
    df = get_room_dataframe(room_id)
    if df is None:
        return jsonify({"error": "Invalid room prefix"}), 400

    room_col = get_column_name(df, "Room Number")
    if room_col is None:
        return jsonify({"error": "Room Number column not found"}), 500

    matching_rows = df[df[room_col].astype(str).str.upper().str.strip() == room_id]
    if matching_rows.empty:
        return jsonify({"error": "Room not found"}), 404

    # Column names
    type_col = get_column_name(df, "Type of room")
    doc_col = get_column_name(df, "מסמכים סופקו")
    date_col = get_column_name(df, "Commissioning Due Date")
    fam_col = get_column_name(df, "Family")
    typ_col = get_column_name(df, "Type")
    qty_col = get_column_name(df, "Quantity")

    first_row = matching_rows.iloc[0]
    room_type = first_row.get(type_col, "").strip() if type_col else ""
    documents_supplied = str(first_row.get(doc_col, "")).strip() == "כן"

    # Parse date
    date_value = first_row.get(date_col, "") if date_col else ""
    try:
        due_date = pd.to_datetime(date_value).date()
    except Exception:
        due_date = None

    # Gather fixtures
    fixtures = []
    for _, row in matching_rows.iterrows():
        family = row.get(fam_col, "").strip() if fam_col else ""
        fixture_type = row.get(typ_col, "").strip() if typ_col else ""
        try:
            quantity = int(row.get(qty_col, 0)) if qty_col else 0
        except ValueError:
            quantity = 0
        fixtures.append({
            "family": family,
            "type": fixture_type,
            "quantity": quantity
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
