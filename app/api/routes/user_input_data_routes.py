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
    # generate_final_conclusion,
    validate_file_extension,
    calculate_bias_score,
    overall_score
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
from ..config.config import GOOGLE_FACT_CHECK_API_KEY
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
        return api_response("No input provided.",400)

    combined_text = " ".join(all_texts)
    # print(combined_text)
    # Analysis logic
    sentiment = analyze_sentiment(combined_text)
    authenticity = check_authenticity(combined_text)
    fact_check_result = google_fact_check(combined_text,GOOGLE_FACT_CHECK_API_KEY)
    bias = calculate_bias_score(combined_text)

    

    authenticity_score = authenticity["score"]
    authenticity_data = round(authenticity_score,4)*100
    sentiment_score = sentiment["score"]
    sentiment_data  = round(sentiment_score, 4)*100
    bias_score = bias["bias_score"]
    bias_data = round(bias_score, 4)*100
    overall_score_percentage = overall_score(bias_data, authenticity_data, sentiment_data)
    # conclusion = generate_final_conclusion(
    #     sentiment=sentiment,
    #     authenticity_score=authenticity_score,
    #     fact_check=fact_check_result,
    #     bias_score=bias_score
    # )
    weights = {'bias': 0.3, 'authenticity': 0.5, 'sentiment': 0.2}
    overall_weighted_score_percentage = overall_score(bias_data, authenticity_data, sentiment_data,weights)

    return {
        "message": "Analysis completed",
        "sentiment": sentiment,
        "authenticity": authenticity,
        "fact_check_result": fact_check_result,
        "bias_score": bias,
        "overall_score": overall_score_percentage,
        "overall_weighted_score": overall_weighted_score_percentage
        # "final_conclusion": conclusion
    }