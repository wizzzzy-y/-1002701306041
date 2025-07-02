# FINAL BRAIN SCRIPT v2.0 - WITH PRE-PROCESSING
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
    return "brain online v2.0", 200

def preprocess_for_ocr(image):
    # CONVERT TO GRAYSCALE AND APPLY A THRESHOLD TO MAKE IT PURE B&W
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def solve_puzzle(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 1. GET LETTERS FROM WHEEL
    y1, y2, x1, x2 = WHEEL_CROP
    wheel_img = img[y1:y2, x1:x2]
    # NEW PRE-PROCESSING FOR WHEEL
    processed_wheel = preprocess_for_ocr(wheel_img)
    # NEW TESSERACT CONFIG - Hunt for single characters
    ocr_data = pytesseract.image_to_data(processed_wheel, config='--psm 10', output_type=pytesseract.Output.DICT)
    
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
    # NEW PRE-PROCESSING FOR GRID
    processed_grid = cv2.cvtColor(grid_img, cv2.COLOR_BGR2GRAY) # Simple grayscale is enough for the grid
    found_words_text = pytesseract.image_to_string(processed_grid)
    existing_words = set(re.findall(r'\b[A-Z]{3,}\b', found_words_text.upper()))

    # 3. FIND NEW WORDS
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
    swipe_paths = solve_puzzle(image_bytes)
    return jsonify({"swipes": swipe_paths})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
