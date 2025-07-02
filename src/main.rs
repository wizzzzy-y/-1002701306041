// IMPORT THE ARSENAL
use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use actix_multipart::Multipart;
use futures_util::stream::StreamExt;
use opencv::{
    prelude::*,
    core,
    imgcodecs,
    imgproc,
};
use serde_json::json;
use itertools::Itertools;
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::Read;
use tesseract::Tesseract;

// --- YOUR CALIBRATION ---
const WHEEL_CROP: [i32; 4] = [1004, 1456, 132, 584];
const GRID_CROP: [i32; 4] = [131, 930, 0, 711];

// COMPILE-TIME DICTIONARY LOAD
lazy_static::lazy_static! {
    static ref DICTIONARY: HashSet<String> = {
        let mut f = File::open("/usr/share/dict/words").expect("Dictionary not found");
        let mut contents = String::new();
        f.read_to_string(&mut contents).expect("Can't read dictionary");
        contents.lines().map(|s| s.trim().to_uppercase()).collect()
    };
}

// THIS IS THE NEW, HIGH-PERFORMANCE LOGIC
fn get_letters_and_coords(wheel_img: &Mat, tesseract_api: &mut Tesseract) -> HashMap<char, (i32, i32)> {
    let mut gray = Mat::default();
    imgproc::cvt_color(&wheel_img, &mut gray, imgproc::COLOR_BGR2GRAY, 0).unwrap();
    let mut thresh = Mat::default();
    imgproc::threshold(&gray, &mut thresh, 0.0, 255.0, imgproc::THRESH_BINARY_INV + imgproc::THRESH_OTSU).unwrap();

    let mut contours = opencv::types::VectorOfVectorOfPoint::new();
    imgproc::find_contours(&thresh, &mut contours, imgproc::RETR_EXTERNAL, imgproc::CHAIN_APPROX_SIMPLE, core::Point::new(0, 0)).unwrap();

    let mut letter_coords = HashMap::new();
    for contour in contours.iter() {
        let rect = imgproc::bounding_rect(&contour).unwrap();
        // FILTER OUT NOISE (TOO SMALL) OR THE WHOLE CIRCLE (TOO BIG)
        if rect.width > 20 && rect.width < 200 {
            let letter_roi = Mat::roi(&thresh, rect).unwrap();
            let text = tesseract_api.set_image_from_mat(&letter_roi)
                .set_variable("tessedit_char_whitelist", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                .set_variable("tessedit_pageseg_mode", "10") // Treat image as single char
                .recognize().unwrap().get_text().unwrap();
            
            if let Some(letter) = text.trim().chars().next() {
                if !letter_coords.contains_key(&letter) {
                    let center_x = WHEEL_CROP[2] + rect.x + rect.width / 2;
                    let center_y = WHEEL_CROP[0] + rect.y + rect.height / 2;
                    letter_coords.insert(letter, (center_x, center_y));
                }
            }
        }
    }
    letter_coords
}

// THE CORE SOLVER
async fn solve(mut payload: Multipart) -> impl Responder {
    let mut image_data = Vec::new();
    while let Some(item) = payload.next().await {
        let mut field = item.unwrap();
        if field.name() == "screenshot" {
            while let Some(chunk) = field.next().await { image_data.extend_from_slice(&chunk.unwrap()); }
        }
    }

    let img = imgcodecs::imdecode(&core::Mat::from_slice(&image_data).unwrap(), imgcodecs::IMREAD_COLOR).unwrap();
    let mut tesseract_api = Tesseract::new(None, Some("eng")).unwrap();

    // 1. GET LETTERS WITH REAL COORDS
    let wheel_rect = core::Rect::new(WHEEL_CROP[2], WHEEL_CROP[0], WHEEL_CROP[3] - WHEEL_CROP[2], WHEEL_CROP[1] - WHEEL_CROP[0]);
    let wheel_img = Mat::roi(&img, wheel_rect).unwrap();
    let letter_coords = get_letters_and_coords(&wheel_img, &mut tesseract_api);

    // 2. GET EXISTING WORDS
    let grid_rect = core::Rect::new(GRID_CROP[2], GRID_CROP[0], GRID_CROP[3] - GRID_CROP[2], GRID_CROP[1] - GRID_CROP[0]);
    let grid_img = Mat::roi(&img, grid_rect).unwrap();
    let mut gray_grid = Mat::default();
    imgproc::cvt_color(&grid_img, &mut gray_grid, imgproc::COLOR_BGR2GRAY, 0).unwrap();
    let existing_words_text = tesseract_api.set_image_from_mat(&gray_grid).recognize().unwrap().get_text().unwrap();
    let existing_words: HashSet<String> = existing_words_text.split_whitespace().map(|s| s.to_uppercase()).collect();

    // 3. FIND WORDS AND CREATE SWIPES
    let mut found_words = Vec::new();
    let available_letters: Vec<char> = letter_coords.keys().cloned().collect();
    for i in 3..=available_letters.len() {
        for p in available_letters.iter().permutations(i) {
            let word: String = p.into_iter().collect();
            if DICTIONARY.contains(&word) && !existing_words.contains(&word) {
                found_words.push(word);
            }
        }
    }
    
    let swipes: Vec<Vec<(i32, i32)>> = found_words.iter().map(|word| {
        word.chars().map(|c| letter_coords[&c]).collect()
    }).collect();

    HttpResponse::Ok().json(json!({ "swipes": swipes }))
}

// START SERVER
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| { App::new().route("/solve", web::post().to(solve)) })
    .bind(("0.0.0.0", 8080))?
    .run()
    .await
}
