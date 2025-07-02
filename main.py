# FINAL BRAIN SCRIPT - FULLY CALIBRATED
from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract
from itertools import permutations
import re

# --- FINAL CALIBRATION VALUES ---
# FROM YOUR INPUT
WHEEL_CROP = [1004, 1456, 132, 584]  # y1, y2, x1, x2
GRID_CROP = [131, 930, 0, 711]      # y1, y2, x1, x2

app = Flask(__name__)

# LOAD DICTIONARY
with open('/usr/share/dict/words', 'r') as f:
    dictionary = set(word.strip().upper() for word in f)

@app.route('/')
def health_check():
    return "brain online", 200

def solve_puzzle(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 1. GET LETTERS FROM WHEEL
    y1, y2, x1, x2 = WHEEL_CROP
    wheel_img = img[y1:y2, x1:x2]
    ocr_data = pytesseract.image_to_data(wheel_img, config='--psm 6', output_type=pytesseract.Output.DICT)
    available_letters = []
    letter_coords = {}
    for i in range(len(ocr_data['text'])):
        letter = ocr_data['text'][i].upper()
        if re.match("^[A-Z]$", letter) and letter not in letter_coords:
            abs_x = x1 + ocr_data['left'][i] + ocr_data['width'][i] // 2
            abs_y = y1 + ocr_data['top'][i] + ocr_data['height'][i] // 2
            letter_coords[letter] = (abs_x, abs_y)
    available_letters = list(letter_coords.keys())

    # 2. GET EXISTING WORDS FROM GRID
    y1, y2, x1, x2 = GRID_CROP
    grid_img = img[y1:y2, x1:x2]
    found_words_text = pytesseract.image_to_string(grid_img)
    existing_words = set(re.findall(r'\b[A-Z]{3,}\b', found_words_text.upper()))

    # 3. FIND NEW WORDS
    all_possible_words = set()
    for i in range(3, len(available_letters) + 1):
        for p in permutations(available_letters, i):
            word = "".join(p)
            if word in dictionary:
                all_possible_words.add(word)
    new_words = list(all_possible_words - existing_words)
    new_words.sort(key=len, reverse=True) # SOLVE LONGEST WORDS FIRST

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
    swipe_paths = solve_puzzle(image_bytes)
    return jsonify({"swipes": swipe_paths})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
