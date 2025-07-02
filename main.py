# FINAL BRAIN SCRIPT v3.0 - ROBUST EDITION
from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract
from itertools import permutations
import re

# --- FINAL CALIBRATION VALUES ---
WHEEL_CROP = [1004, 1456, 132, 584]  # y1, y2, x1, x2
GRID_CROP = [131, 930, 0, 711]      # y1, y2, x1, x2

app = Flask(__name__)

with open('/usr/share/dict/words', 'r') as f:
    dictionary = set(word.strip().upper() for word in f)

@app.route('/')
def health_check():
    return "brain online v3.0 robust", 200

def preprocess_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def solve_puzzle(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # --- SANITY CHECK FOR IMAGE SIZE ---
    if img is None:
        return "err: Invalid image data"

    # --- DEFENSIVE CROPPING ---
    y1, y2, x1, x2 = WHEEL_CROP
    if y2 > img.shape[0] or x2 > img.shape[1]:
        return f"err: WHEEL_CROP [{y1},{y2},{x1},{x2}] is outside image bounds [{img.shape[0]},{img.shape[1]}]"
    wheel_img = img[y1:y2, x1:x2]

    # THE ERROR HAPPENED HERE, NOW IT'S PROTECTED
    processed_wheel = preprocess_for_ocr(wheel_img)
    ocr_data = pytesseract.image_to_data(processed_wheel, config='--psm 10', output_type=pytesseract.Output.DICT)
    
    letter_coords = {}
    for i in range(len(ocr_data['text'])):
        letter = ocr_data['text'][i].upper()
        if re.match("^[A-Z]$", letter) and letter not in letter_coords:
            abs_x = x1 + ocr_data['left'][i] + ocr_data['width'][i] // 2
            abs_y = y1 + ocr_data['top'][i] + ocr_data['height'][i] // 2
            letter_coords[letter] = (abs_x, abs_y)
    available_letters = list(letter_coords.keys())

    # --- SAME DEFENSE FOR GRID ---
    y1_g, y2_g, x1_g, x2_g = GRID_CROP
    if y2_g > img.shape[0] or x2_g > img.shape[1]:
        return f"err: GRID_CROP is outside image bounds"
    grid_img = img[y1_g:y2_g, x1_g:x2_g]
    
    processed_grid = cv2.cvtColor(grid_img, cv2.COLOR_BGR2GRAY)
    found_words_text = pytesseract.image_to_string(processed_grid)
    existing_words = set(re.findall(r'\b[A-Z]{3,}\b', found_words_text.upper()))

    all_possible_words = set()
    for i in range(3, len(available_letters) + 1):
        for p in permutations(available_letters, i):
            word = "".join(p)
            if word in dictionary:
                all_possible_words.add(word)
    new_words = list(all_possible_words - existing_words)
    new_words.sort(key=len, reverse=True)

    swipes = []
    for word in new_words:
        path = []
        for letter in word:
            if letter in letter_coords:
                path.append(letter_coords[letter])
        if len(path) == len(word):
            swipes.append(path)

    return swipes

@app.route('/solve', methods=['POST'])
def process_image():
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot file"}), 400
    image_file = request.files['screenshot']
    image_bytes = image_file.read()
    
    result = solve_puzzle(image_bytes)
    
    # RETURN AN ERROR INSTEAD OF CRASHING
    if isinstance(result, str) and result.startswith("err:"):
        return jsonify({"error": result}), 500

    return jsonify({"swipes": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
