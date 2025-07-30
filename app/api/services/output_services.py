from fastapi import UploadFile, HTTPException
import os
import newspaper
from transformers import pipeline
import requests
from urllib.parse import quote
import torch
from transformers import pipeline
from ..config.config import CLAIMBUSTER_API_KEY
from ...utils.api_response import api_response
from textblob import TextBlob
import pytesseract
from PIL import Image
import io
import requests
from bs4 import BeautifulSoup
import whisper
import tempfile
from fastapi.responses import JSONResponse
model = whisper.load_model("base")  # Load Whisper model only once

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
MAX_FILE_SIZE_MB = 3 # Limit audio file size to 3 MB


classifier = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    revision="714eb0f"  # Optional: locks a stable version
)




def extract_text_from_url(url: str) -> str:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    MAX_INPUT_WORDS = 800   # Limit text to avoid very long inputs
    SUMMARY_MIN = 50        # Min length of summary
    SUMMARY_MAX = 300       # Max length of summary

    # Fetch page HTML
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract text from all <p> tags
    paragraphs = [p.get_text() for p in soup.find_all("p")]
    full_text = " ".join(paragraphs).strip()

    # Limit to first N words for summarization
    words = full_text.split()
    short_text = " ".join(words[:MAX_INPUT_WORDS])

    # Summarize
    summary = summarizer(
        short_text,
        max_length=SUMMARY_MAX,
        min_length=SUMMARY_MIN,
        do_sample=False
    )[0]['summary_text']

    return summary


def extract_text_from_image(image_bytes: bytes) -> str:
    # Open image from bytes
    image = Image.open(io.BytesIO(image_bytes))
    # Extract raw text using Tesseract
    raw_text = pytesseract.image_to_string(image)
    # Clean the text: remove newlines, tabs, and extra spaces
    cleaned_text = " ".join(raw_text.split())

    return cleaned_text.strip()

async def extract_text_from_audio(file: UploadFile) -> dict:
    filename = file.filename
    extension = os.path.splitext(filename)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    # Check file size (limit to 5MB)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_audio:
            temp_audio.write(contents)
            temp_audio.flush()
            result = model.transcribe(temp_audio.name)
            return result["text"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# def extract_text_from_audio(audio_bytes: bytes) -> str:
#     import speech_recognition as sr
#     import io
#     recognizer = sr.Recognizer()
#     with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
#         audio = recognizer.record(source)
#     return recognizer.recognize_google(audio)

def analyze_sentiment(text: str) -> str:
    res = classifier(text)[0]  # returns {'label': 'NEGATIVE', 'score': 0.9987}
    label = res['label']
    score = res['score']
    
   
    if score < 0.6:
        return "NEUTRAL"
    
    data = {
        "label_data":label,
        "score" : score
    }
    
    # return f"{label} (confidence: {round(score, 4)})"
    return data

def overall_score(bias_score, authenticity_score, sentiment_score, weights=None):
    if not weights:
        # Simple average
        overall = (bias_score + authenticity_score + sentiment_score) / 3
    else:
        # Weighted average
        total_weight = sum(weights.values())
        overall = (
            (bias_score * weights.get('bias', 1)) +
            (authenticity_score * weights.get('authenticity', 1)) +
            (sentiment_score * weights.get('sentiment', 1))
        ) / total_weight
    
    return round(overall, 2)


def calculate_bias_score(text: str) -> dict:
    blob = TextBlob(text)
    
    
    subjectivity = blob.sentiment.subjectivity  
    
    
    polarity = abs(blob.sentiment.polarity)
    
    score = round((subjectivity * 0.7) + (polarity * 0.3), 2)
    
    
    if score < 0.3:
        level = "Low (Mostly Neutral)"
    elif score < 0.6:
        level = "Moderate Bias"
    else:
        level = "High (Strongly Biased)"
    
    return {
        "bias_score": score,
        "bias_level": level
    }

def  check_authenticity(claim: str) -> dict:
    encoded_claim = quote(claim)  # Proper URL encoding
    endpoint = f"https://idir.uta.edu/claimbuster/api/v2/score/text/{encoded_claim}"
    headers = {"x-api-key": CLAIMBUSTER_API_KEY}

    try:
        response = requests.get(url=endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # print(data)
        score = data.get("results", [{}])[0].get("score")
        if score is None:
            return api_response("Score not found in ClaimBuster response.",502)

        score = round(score, 2)

        # Simple logic for verdict
        if score > 0.75:
            verdict = "Highly Check-Worthy"
        elif score > 0.4:
            verdict = "Possibly Check-Worthy"
        else:
            verdict = "Unlikely to be Check-Worthy"

        return {
            "claim": claim,
            "score": score,
            "verdict": verdict,
            "source": "ClaimBuster API"
        }

    except requests.RequestException as e:
        return api_response(f"ClaimBuster API error: {str(e)}",502)

def google_fact_check(text: str, api_key: str) -> dict:
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": text,
        "key": api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Return only the first claim if available
        if "claims" in data and data["claims"]:
            item = data["claims"][0]
            review = item.get("claimReview", [])[0] if item.get("claimReview") else {}

            return {
                "input_query": text,
                "claim_text": item.get("text", "N/A"),
                "rating": review.get("textualRating", "N/A"),
                "title": review.get("title", "N/A"),
                "url": review.get("url", "N/A"),
                "publisher": review.get("publisher", {}).get("name", "N/A")
            }
        else:
            # return api_response("No fact-checked claims found for the provided text.",404)
            return {
                "rating":"No rating found",
                "input_query": text,
                "fact_checked_claims": [],
                "message": "Google Fact Check API returned no results for the provided text."
            }
    except requests.exceptions.RequestException as e:
        return api_response(f"External API error: {str(e)}",502)

    
def generate_final_conclusion(sentiment: str, authenticity_score: float, fact_check: str, bias_score: float) -> str:
    if authenticity_score >= 80 and sentiment != "negative" and "true" in fact_check.lower() and bias_score < 40:
        return "This content appears to be mostly REAL"
    elif authenticity_score < 50 or "false" in fact_check.lower() or bias_score >= 70:
        return "This content is likely FAKE"
    elif 50 <= authenticity_score < 80 or (40 <= bias_score < 70):
        return "This content might be PARTIALLY TRUE or BIASED"
    else:
        return "Unable to determine content authenticity accurately"
    
def validate_file_extension(file: UploadFile, allowed_exts: set, file_type: str):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        return api_response(
            f"Invalid {file_type} file type. Allowed: {', '.join(allowed_exts)}",
            400
        )