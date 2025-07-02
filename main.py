# FINAL BRAIN SCRIPT v9.0 - THE ANNIHILATOR
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

def get_target_lengths(grid_img):
    gray = cv2.cvtColor(grid_img, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 30, 200)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        if 0.8 < aspect_ratio < 1.2 and 50 < w < 150:
             boxes.append((x, y))
    if not boxes: return []
    boxes.sort(key=lambda b: b[1])
    word_groups = []
    current_group = [boxes[0]]
    for i in range(1, len(boxes)):
        if abs(boxes[i][1] - current_group[-1][1]) < 20:
            current_group.append(boxes[i])
        else:
            word_groups.append(current_group)
            current_group = [boxes[i]]
    word_groups.append(current_group)
    return [len(group) for group in word_groups]

def solve_everything(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # ... [Same OCR logic for wheel] ...
    y1w, y2w, x1w, x2w = WHEEL_CROP
    wheel_img = img[y1w:y2w, x1w:x2w]
    ocr_data = pytesseract.image_to_data(wheel_img, config='--psm 10', output_type=pytesseract.Output.DICT)
    letter_coords = {}
    for i in range(len(ocr_data['text'])):
        letter = ocr_data['text'][i].upper()
        if re.match("^[A-Z]$", letter) and letter not in letter_coords:
            letter_coords[letter] = (x1w + ocr_data['left'][i] + ocr_data['width'][i] // 2, y1w + ocr_data['top'][i] + ocr_data['height'][i] // 2)
    
    y1g, y2g, x1g, x2g = GRID_CROP
    grid_img = img[y1g:y2g, x1g:x2g]
    existing_words_text = pytesseract.image_to_string(cv2.cvtColor(grid_img, cv2.COLOR_BGR2GRAY))
    existing_words = set(re.findall(r'\b[A-Z]{3,}\b', existing_words_text.upper()))
    
    target_lengths = get_target_lengths(grid_img)
    available_letters = list(letter_coords.keys())
    
    # --- MACHINE GUN LOGIC ---
    swipes = []
    found_this_cycle = set()
    
    for length in sorted(target_lengths):
        if len(available_letters) >= length:
            for p in permutations(available_letters, length):
                word = "".join(p)
                if word in dictionary and word not in existing_words and word not in found_this_cycle:
                    path = [letter_coords[l] for l in word]
                    swipes.append(path)
                    found_this_cycle.add(word) # MARK IT AS FOUND SO WE DON'T ADD IT AGAIN
    
    return swipes # RETURN EVERYTHING

@app.route('/solve', methods=['POST'])
def process_image():
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot file"}), 400
    image_file = request.files['screenshot']
    image_bytes = image_file.read()
    swipe_paths = solve_everything(image_bytes)
    return jsonify({"swipes": swipe_paths})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
