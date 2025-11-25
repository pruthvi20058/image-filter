import os
import io
import base64
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

# --- CONFIGURATION ---
app = Flask(__name__)
# Allow access from your frontend running on localhost (or Vercel/Netlify)
CORS(app) 

# --- MOCK CLASSIFICATION DATA ---
# This dictionary contains comprehensive data for all waste types.
# The keys correspond to possible detected materials from an actual ML model.
WASTE_DATA = {
    "Plastic Bottle (PET)": {
        "category": "Recyclable",
        "bin_color": "Blue",
        "color": "blue",
        "instructions": "Rinse thoroughly, remove the cap, and flatten the bottle before placing in the recycling bin. Caps are often recycled separately.",
    },
    "Aluminum Can": {
        "category": "Recyclable",
        "bin_color": "Blue",
        "color": "blue",
        "instructions": "Rinse out all food residue. Do not crush the can entirely, as automatic sorters may mistake crushed cans for general waste.",
    },
    "Cardboard Box": {
        "category": "Recyclable",
        "bin_color": "Brown",
        "color": "yellow",
        "instructions": "Flatten the box completely. Remove all tape and shipping labels. If greasy (like a pizza box), tear off clean parts and put the greasy part in general waste.",
    },
    "Newspaper/Magazine": {
        "category": "Recyclable",
        "bin_color": "Blue",
        "color": "blue",
        "instructions": "Keep dry. Place loose in the recycling bin. Do not tie with string or put in plastic bags.",
    },
    "Banana Peel/Fruit Scraps": {
        "category": "Organic/Compostable",
        "bin_color": "Green",
        "color": "green",
        "instructions": "Place directly into the compost bin or dedicated green waste bin. Do not include any packaging.",
    },
    "Used Batteries (AA/AAA)": {
        "category": "Hazardous/E-Waste",
        "bin_color": "Special Collection",
        "color": "red",
        "instructions": "Tape the terminals to prevent short circuits. Take to a specialized collection point (e.g., library, municipality center, or retail store drop-off).",
    },
    "Light Bulb (Incandescent)": {
        "category": "General Waste",
        "bin_color": "Black/Gray",
        "color": "gray",
        "instructions": "Wrap in paper or a plastic bag to prevent injury from broken glass and place carefully in the general waste bin.",
    },
    "Plastic Film/Bags": {
        "category": "General Waste",
        "bin_color": "Black/Gray",
        "color": "gray",
        "instructions": "Plastic films and bags jam recycling machinery. Dispose of in general waste, or check for specific local drop-off points.",
    },
}

# --- CORE ANALYSIS FUNCTION (MOCK IMPLEMENTATION) ---

def classify_image_mock(image_bytes):
    """
    Mocks the object detection and classification result.
    This function returns the *exact* JSON structure required by the frontend.
    """
    try:
        # Simulate successful image opening (a basic sanity check)
        Image.open(io.BytesIO(image_bytes))
        
        # 1. Simulate Detected Items (2 to 4 unique items)
        all_materials = list(WASTE_DATA.keys())
        # Randomly select between 2 and 4 unique items
        num_detections = random.randint(2, 4)
        detected_materials = random.sample(all_materials, k=num_detections)

        # 2. Build the final structured result
        materials_output = []
        summary = {"recyclable_items": 0, "hazardous_items": 0, "general_waste_items": 0}
        
        for material_name in detected_materials:
            data = WASTE_DATA[material_name]
            
            # Update summary counts
            if data['category'] == 'Recyclable':
                summary['recyclable_items'] += 1
            elif 'Hazardous' in data['category'] or 'E-Waste' in data['category']:
                summary['hazardous_items'] += 1
            else: # Includes General Waste/Organic
                summary['general_waste_items'] += 1

            materials_output.append({
                "detected_material": material_name,
                "confidence": random.uniform(0.75, 0.99), # Mock confidence
                "classification": {
                    "category": data['category'],
                    "bin_color": data['bin_color'],
                    "color": data['color'],
                    "instructions": data['instructions'],
                }
            })

        final_result = {
            "success": True,
            "message": "Classification successful.",
            "total_materials_detected": len(materials_output),
            "summary": summary,
            "materials": materials_output
        }
        
        # Simulate ML processing delay for realism
        import time
        time.sleep(1.0) 
        
        return final_result

    except Exception as e:
        print(f"Server-side error during mock classification: {e}")
        return {
            "success": False,
            "message": f"Server processing failed (Error: {e}). Ensure the input file is a valid image.",
            "total_materials_detected": 0,
            "summary": {"recyclable_items": 0, "hazardous_items": 0, "general_waste_items": 0},
            "materials": []
        }

# --- API ROUTE ---

@app.route('/classify_waste', methods=['POST'])
def classify_waste_api():
    """ Handles file upload and calls the classification function. """
    # 1. Check for file presence
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400

    if file:
        try:
            # Read image data directly from the file stream
            image_bytes = file.read()
            
            # Call the mock classifier
            results = classify_image_mock(image_bytes)
            
            # Return JSON results
            if results['success']:
                return jsonify(results), 200
            else:
                return jsonify(results), 500

        except Exception as e:
            return jsonify({"success": False, "message": f"Internal Server Error during file reading: {e}"}), 500


# --- RUN SERVER ---

if __name__ == '__main__':
    # Flask will run on http://0.0.0.0:5000 by default (for local testing)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)