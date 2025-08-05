from dotenv import load_dotenv
from urllib.parse import quote
from transformers import pipeline
import os
from fastapi import requests,HTTPException
from ...utils.api_response import api_response
from ..config.config import CLAIMBUSTER_API_KEY , GOOGLE_FACT_CHECK_API_KEY
import requests
load_dotenv()

classifier = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    revision="714eb0f"  # Optional: version locking
)
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
    
    
def  check_authenticity(claim: str) -> dict:
    encoded_claim = quote(claim)  # Proper URL encoding
    endpoint = f"https://idir.uta.edu/claimbuster/api/v2/score/text/{encoded_claim}"
    headers = {"x-api-key": CLAIMBUSTER_API_KEY}

    try:
        response = requests.get(url=endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # print(data)
        score = data.get("results", [{}])[0].get("score",None)
        
        # Simple logic for verdict
        if score is not None:
            return {"score": round(score, 2), "limit_exceeded": False}
        else:
            return {"score": None, "error": "Score not found.", "limit_exceeded": False}

    except requests.exceptions.RequestException as e:
        print("ClaimBuster request failed:", str(e))
        return {"score": None, "error": "ClaimBuster is currently unavailable. Please try again later.", "limit_exceeded": False}
    
def google_fact_check(text: str) -> dict:
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": text,
        "key": GOOGLE_FACT_CHECK_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        # Return only the first claim if available
        if "claims" in result and len(result["claims"]) > 0:
            claim = result["claims"][0]
            text = claim.get("text", "No text available")
            claimant = claim.get("claimant") or "Not available"

            claim_reviews = claim.get("claimReview", [])
            if claim_reviews and isinstance(claim_reviews, list):
                review_obj = claim_reviews[0]
                review_rating = review_obj.get("reviewRating", {})
                review_text = review_rating.get("alternateName") or review_rating.get("ratingValue") or "Not available"
            else:
                review_text = "Not available"

            msg = f"🔍 Fact Check: {text}\nClaimed by: {claimant}\nReview: {review_text}"
            return {"message": msg, "limit_exceeded": False}
        else:
            return {"message": "🔍 Fact Check: No relevant claims found.", "limit_exceeded": False}

    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))