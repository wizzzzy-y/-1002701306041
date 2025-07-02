# F1N4L BR41N SCR1PT v4.0 - 4SYNC M4ST3RP13C3
from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract
from itertools import permutations
import re
import uuid
import threading

WHEEL_CROP = [1004, 1456, 132, 584]
GRID_CROP = [131, 930, 0, 711]

app = Flask(__name__)
with open('/usr/share/dict/words', 'r') as f:
    dictionary = set(word.strip().upper() for word in f)

jobs = {}

def preprocess_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def solve_and_store(job_id, image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            jobs[job_id] = {"status": "failed", "result": "Invalid image"}
            return
        
        y1w, y2w, x1w, x2w = WHEEL_CROP
        wheel_img = img[y1w:y2w, x1w:x2w]
        processed_wheel = preprocess_for_ocr(wheel_img)
        ocr_data = pytesseract.image_to_data(processed_wheel, config='--psm 10', output_type=pytesseract.Output.DICT)
        letter_coords = {}
        for i in range(len(ocr_data['text'])):
            letter = ocr_data['text'][i].upper()
            if re.match("^[A-Z]$", letter) and letter not in letter_coords:
                letter_coords[letter] = (x1w + ocr_data['left'][i] + ocr_data['width'][i] // 2, y1w + ocr_data['top'][i] + ocr_data['height'][i] // 2)
        
        y1g, y2g, x1g, x2g = GRID_CROP
        grid_img = img[y1g:y2g, x1g:x2g]
        processed_grid = cv2.cvtColor(grid_img, cv2.COLOR_BGR2GRAY)
        existing_words = set(re.findall(r'\b[A-Z]{3,}\b', pytesseract.image_to_string(processed_grid).upper()))
        
        all_possible_words = set("".join(p) for i in range(3, len(letter_coords) + 1) for p in permutations(letter_coords.keys(), i) if "".join(p) in dictionary)
        new_words = sorted(list(all_possible_words - existing_words), key=len, reverse=True)
        
        swipes = [[letter_coords[l] for l in word] for word in new_words]
        jobs[job_id] = {"status": "complete", "result": swipes}

    except Exception as e:
        jobs[job_id] = {"status": "failed", "result": str(e)}

@app.route('/submit', methods=['POST'])
def submit_job():
    if 'screenshot' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    job_id = str(uuid.uuid4())
    image_bytes = request.files['screenshot'].read()
    jobs[job_id] = {"status": "pending", "result": None}
    
    thread = threading.Thread(target=solve_and_store, args=(job_id, image_bytes))
    thread.start()
    
    return jsonify({"job_id": job_id})

@app.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"status": "not_found"}), 404
    
    if job["status"] in ["complete", "failed"]:
        jobs.pop(job_id, None) # Use .pop() for safer deletion
    
    return jsonify(job)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
