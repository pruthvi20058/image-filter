import os
import io
import base64
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)

# Minimal mock WASTE_DATA (expand this with your real classes)
WASTE_DATA = {
    "plastic_bottle": {
        "name": "Plastic Bottle",
        "category": "Recyclable",
        "recycling_instructions": "Rinse and place in PET recycling.",
    },
    "battery": {
        "name": "Battery",
        "category": "Hazardous - E-Waste",
        "recycling_instructions": "Do not throw in general waste. Take to e-waste collection.",
    },
    "food_scraps": {
        "name": "Food Scraps",
        "category": "General Waste / Compostable",
        "recycling_instructions": "Compost where available.",
    },
    "glass_bottle": {
        "name": "Glass Bottle",
        "category": "Recyclable",
        "recycling_instructions": "Rinse and recycle glass.",
    },
}

ALL_MATERIALS = list(WASTE_DATA.keys())

# Confidence threshold: if best detection confidence < threshold, treat as "not a waste item".
# Default 0.70, but override with environment variable WASTE_CONFIDENCE_THRESHOLD (0.0 - 1.0).
try:
    WASTE_CONFIDENCE_THRESHOLD = float(os.environ.get("WASTE_CONFIDENCE_THRESHOLD", "0.70"))
except Exception:
    WASTE_CONFIDENCE_THRESHOLD = 0.70

def load_image_from_file(file_storage):
    """Load PIL Image from Flask file storage"""
    try:
        img = Image.open(file_storage.stream)
        img.verify()
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream).convert("RGB")
        return img
    except Exception:
        raise ValueError("Uploaded file is not a valid image")

def load_image_from_base64(b64_string):
    """Load PIL Image from base64 string (data URL or raw)"""
    try:
        if b64_string.startswith("data:"):
            b64_string = b64_string.split(",", 1)[1]
        decoded = base64.b64decode(b64_string)
        img = Image.open(io.BytesIO(decoded)).convert("RGB")
        return img
    except Exception:
        raise ValueError("Base64 string is not a valid image")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"success": True, "message": "OK"}), 200

@app.route('/classify_waste', methods=['POST'])
def classify_waste_api():
    """
    Accepts:
      - multipart/form-data with field 'image' (file)
      - or JSON { "image_base64": "<base64-data-or-data-url>" }
    Returns:
      - If no confident waste detection: {"success": False, "message": "No waste item detected."}
      - Otherwise returns detection details.
    """
    try:
        img = None
        if "image" in request.files:
            file = request.files["image"]
            img = load_image_from_file(file)
        else:
            data = request.get_json(silent=True) or {}
            b64 = data.get("image_base64") or request.form.get("image_base64")
            if b64:
                img = load_image_from_base64(b64)

        if img is None:
            return jsonify({"success": False, "message": "No image provided. Send 'image' file or JSON with 'image_base64'."}), 400

        # ----- MOCK DETECTION LOGIC -----
        # Simulate detection: produce 1-3 candidates with confidences
        num_candidates = random.randint(1, min(3, len(ALL_MATERIALS)))
        candidates = random.sample(ALL_MATERIALS, k=num_candidates)

        # Mock confidences (in real model, use actual confidences)
        materials = []
        for name in candidates:
            materials.append({
                "id": name,
                "display_name": WASTE_DATA.get(name, {}).get("name", name),
                "category": WASTE_DATA.get(name, {}).get("category", "Unknown"),
                "recycling_instructions": WASTE_DATA.get(name, {}).get("recycling_instructions", ""),
                "confidence": round(random.uniform(0.40, 0.99), 2)  # allow some low confidences to simulate non-waste
            })

        # Find the highest-confidence candidate
        best = max(materials, key=lambda m: m["confidence"])
        best_conf = best["confidence"]

        # If best confidence is below threshold => treat as non-waste (do NOT return materials details)
        if best_conf < WASTE_CONFIDENCE_THRESHOLD:
            # Respond in a way the client can easily detect "not a waste item"
            # We return success=False and a clear message. No material details are included.
            return jsonify({"success": False, "message": "No waste item detected."}), 200

        # Otherwise construct normal result including only candidates above a minimal filter (optional)
        # (Here we include all; you can filter by per-material min confidence if desired.)
        results = {
            "success": True,
            "detected_count": len(materials),
            "materials": materials,
            "summary": {"recyclable_items": 0, "hazardous_items": 0, "general_waste_items": 0},
        }

        for m in materials:
            cat = m.get("category", "")
            if "Recyclable" in cat:
                results["summary"]["recyclable_items"] += 1
            elif "Hazardous" in cat or "E-Waste" in cat:
                results["summary"]["hazardous_items"] += 1
            else:
                results["summary"]["general_waste_items"] += 1

        return jsonify(results), 200

    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
