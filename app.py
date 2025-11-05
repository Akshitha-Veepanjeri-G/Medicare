from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from rapidfuzz import process, fuzz
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import base64

# ---------------- Firebase setup ----------------
cred = credentials.Certificate("medicare-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------------- Flask setup ----------------
app = Flask(__name__)
CORS(app)

# ---------------- Helper ----------------
def medicine_dict(doc):
    data = doc.to_dict()
    return {
        "name": data.get("name", ""),
        "medicineName": data.get("medicineName", ""),
        "quantity": data.get("quantity", ""),
        "expiryDate": data.get("expiryDate", ""),
        "contactInfo": data.get("contactInfo", ""),
        "imageBase64": data.get("imageBase64", "")
    }

# ---------------- Routes ----------------
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    email = request.form['email']
    return redirect(url_for('role', username=username, email=email))

@app.route('/role')
def role():
    username = request.args.get('username')
    email = request.args.get('email')
    return render_template('role.html', username=username, email=email)

@app.route('/donor')
def donor():
    return render_template('donor.html')

@app.route('/receiver')
def receiver():
    return render_template('receiver.html')

@app.route("/add_medicine", methods=["POST"])
def add_medicine():
    data = request.form
    image_file = request.files["image"]

    # Convert image to Base64
    image_bytes = image_file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    med_data = {
        "name": data["name"],
        "medicineName": data["medicineName"],
        "quantity": data["quantity"],
        "expiryDate": data["expiryDate"],
        "contactInfo": data["contactInfo"],
        "imageBase64": image_base64
    }

    db.collection("medicines").add(med_data)
    return jsonify({"message": "Medicine added successfully!"})

@app.route("/search_medicine", methods=["GET"])
def search_medicine():
    query = request.args.get("query", "")
    meds = db.collection("medicines").stream()
    all_meds = [medicine_dict(doc) for doc in meds]

    if not all_meds:
        return jsonify({"error": "No medicines available"}), 404

    names = [m["medicineName"] for m in all_meds]
    match, score, idx = process.extractOne(query, names, scorer=fuzz.token_sort_ratio)

    if score >= 60:
        return jsonify(all_meds[idx])
    else:
        return jsonify({"error": "No matching medicine found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
