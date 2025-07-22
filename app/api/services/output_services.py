from fastapi import UploadFile, HTTPException
import os
import newspaper
from transformers import pipeline
import requests
from urllib.parse import quote
import torch
from transformers import pipeline

CLAIMBUSTER_API_KEY = "8a3450501f4d4eaaa386ce6d08ca7ba3"

classifier = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    revision="714eb0f"  # Optional: locks a stable version
)


def extract_text_from_url(url: str) -> str:
    list_of_urls = url
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    MAX_INPUT_WORDS = 800   # Take a bit more input text
    SUMMARY_MIN = 50        # slightly higher min length
    SUMMARY_MAX = 300       # allow longer summary

    for url in list_of_urls:
        # Download & parse
        article = newspaper.Article(url, language='en')
        article.download()
        article.parse()
        
        # Get the full text
        full_text = article.text.strip()
        words = full_text.split()
        
        # Only take first N words (to keep it short & fast)
        short_text = " ".join(words[:MAX_INPUT_WORDS])
        
        # print(f" Original text length: {len(words)} words")
        # print(f" Using only: {len(short_text.split())} words for summarization")
        
        # Summarize with longer output
        summary = summarizer(
            short_text,
            max_length=SUMMARY_MAX,   # slightly longer summary
            min_length=SUMMARY_MIN,   # ensures it's not too short
            do_sample=False
        )[0]['summary_text']

    return summary


def extract_text_from_image(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)

def extract_text_from_audio(audio_bytes: bytes) -> str:
    import speech_recognition as sr
    import io
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio)

def analyze_sentiment(text: str) -> str:
    res = classifier(text)[0]  # returns {'label': 'NEGATIVE', 'score': 0.9987}
    label = res['label']
    score = res['score']
    
    # ✅ Neutral fallback if confidence is low (< 0.6)
    if score < 0.6:
        return "NEUTRAL"
    
    # ✅ Otherwise return POSITIVE/NEGATIVE
    return f"{label} (confidence: {round(score, 4)})"

# def check_authenticity(text: str) -> float:
#     # Placeholder for ML model or heuristic
#     return 76.3  # percentage

def  check_authenticity(claim: str) -> dict:
    encoded_claim = quote(claim)  # ✅ Proper URL encoding
    endpoint = f"https://idir.uta.edu/claimbuster/api/v2/score/text/{encoded_claim}"
    headers = {"x-api-key": CLAIMBUSTER_API_KEY}

    try:
        response = requests.get(url=endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # print(data)
        score = data.get("results", [{}])[0].get("score")
        if score is None:
            raise HTTPException(status_code=502, detail="Score not found in ClaimBuster response.")

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
        raise HTTPException(status_code=502, detail=f"ClaimBuster API error: {str(e)}")


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
        print(data)
        # ✅ Return only the first claim if available
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
            return {
                "input_query": text,
                "fact_checked_claims": [],
                "message": "Google Fact Check API returned no results for the provided text."
            }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")

def generate_final_conclusion(sentiment: str, authenticity_score: float, fact_check: str) -> str:
    if authenticity_score >= 80 and sentiment != "negative" and "true" in fact_check.lower():
        return "This content appears to be mostly REAL"
    elif authenticity_score < 50:
        return "This content is likely FAKE"
    else:
        return "This content might be PARTIALLY TRUE"
    
def validate_file_extension(file: UploadFile, allowed_exts: set, file_type: str):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {file_type} file type. Allowed: {', '.join(allowed_exts)}"
        )