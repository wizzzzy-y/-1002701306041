# F1N4L BR41N SCR1PT v5.0 - SN1P3R L0G1C
from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract
from itertools import permutations
import re

WHEEL_CROP = [1004, 1456, 132, 584]
GRID_CROP = [131, 930, 0, 711]

app = Flask(__name__)
with open('/usr/share/dict/words', 'r') as f:
    dictionary = set(word.strip().upper() for word in f)

def preprocess_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def solve_for_one_best_word(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # ... [Same OCR logic as before to get letter_coords and existing_words] ...
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

    # --- SN1P3R L0G1C H3R3 ---
    # F1ND TH3 L0NG3ST P0SS1BL3 N3W W0RD 4ND 3X1T
    available_letters = list(letter_coords.keys())
    for length in range(len(available_letters), 2, -1):
        for p in permutations(available_letters, length):
            word = "".join(p)
            if word in dictionary and word not in existing_words:
                # F0UND 0N3. G3T TH3 P4TH 4ND R3TURN 1MM3D14T3LY.
                path = [letter_coords[l] for l in word]
                return [path] # Return as a list containing one path

    return [] # F0und n0th1ng n3w

@app.route('/solve', methods=['POST'])
def process_image():
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot file"}), 400
    image_file = request.files['screenshot']
    image_bytes = image_file.read()
    swipe_paths = solve_for_one_best_word(image_bytes)
    return jsonify({"swipes": swipe_paths})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
