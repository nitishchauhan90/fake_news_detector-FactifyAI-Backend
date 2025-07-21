from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request ,status
from app.api.core.database import get_user_collection
from app.api.core.oauth import get_current_user
from typing import Optional
from ..services.output_services import (
    extract_text_from_audio,
    extract_text_from_image,
    extract_text_from_url,
    analyze_sentiment,
    check_authenticity,
    google_fact_check,
    generate_final_conclusion,
    validate_file_extension
)
from app.api.schemas.user_input_schema import (
    URLInputData,
    TextInputData,
    InputMetaData,
    FileInputData,
    AnalysisResult,
    UserHistoryResponse,
    UserInputData,
    UserInputWithResult
)
from app.utils.api_response import api_response
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["User Input"])


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}

@router.post("/analyze")
async def analyze_input(
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user),
):
    all_texts = []

    if text:
        all_texts.append(text)

    if url:
        url_text = extract_text_from_url(url)
        all_texts.append(url_text)

    if image:
        validate_file_extension(image, ALLOWED_IMAGE_EXTENSIONS, "image")
        image_bytes = await image.read()
        image_text = extract_text_from_image(image_bytes)
        all_texts.append(image_text)

    if audio:
        validate_file_extension(audio, ALLOWED_AUDIO_EXTENSIONS, "audio")
        audio_bytes = await audio.read()
        audio_text = extract_text_from_audio(audio_bytes)
        all_texts.append(audio_text)

    if not all_texts:
        raise HTTPException(status_code=400, detail="No input provided.")

    combined_text = " ".join(all_texts)

    # Analysis logic
    sentiment = analyze_sentiment(combined_text)
    authenticity_score = check_authenticity(combined_text)
    fact_check_result = google_fact_check(combined_text)

    conclusion = generate_final_conclusion(
        sentiment=sentiment,
        authenticity_score=authenticity_score,
        fact_check=fact_check_result
    )

    return {
        "message": "Analysis completed",
        "sentiment": sentiment,
        "authenticity_score": authenticity_score,
        "fact_check_result": fact_check_result,
        "final_conclusion": conclusion
    }