# from fastapi import UploadFile, HTTPException
# import os

# def extract_text_from_url(url: str) -> str:
#     import requests
#     from bs4 import BeautifulSoup
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, "html.parser")
#     return soup.get_text()

# def extract_text_from_image(image_bytes: bytes) -> str:
#     import pytesseract
#     from PIL import Image
#     import io
#     image = Image.open(io.BytesIO(image_bytes))
#     return pytesseract.image_to_string(image)

# def extract_text_from_audio(audio_bytes: bytes) -> str:
#     import speech_recognition as sr
#     import io
#     recognizer = sr.Recognizer()
#     with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
#         audio = recognizer.record(source)
#     return recognizer.recognize_google(audio)

# def analyze_sentiment(text: str) -> str:
#     # Dummy: return 'positive', 'neutral', 'negative'
#     return "neutral"

# def check_authenticity(text: str) -> float:
#     # Placeholder for ML model or heuristic
#     return 76.3  # percentage

# def google_fact_check(text: str) -> str:
#     # Placeholder - you can use Fact Check Tools API or external sources
#     return "Partially true"

# def generate_final_conclusion(sentiment: str, authenticity_score: float, fact_check: str) -> str:
#     if authenticity_score >= 80 and sentiment != "negative" and "true" in fact_check.lower():
#         return "This content appears to be mostly REAL"
#     elif authenticity_score < 50:
#         return "This content is likely FAKE"
#     else:
#         return "This content might be PARTIALLY TRUE"
    
# def validate_file_extension(file: UploadFile, allowed_exts: set, file_type: str):
#     ext = os.path.splitext(file.filename)[1].lower()
#     if ext not in allowed_exts:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid {file_type} file type. Allowed: {', '.join(allowed_exts)}"
        