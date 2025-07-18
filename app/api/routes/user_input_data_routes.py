from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from app.api.core.database import get_user_collection
from app.api.core.oauth import get_current_user
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

router = APIRouter(prefix="/api/user-input", tags=["User Input"])


@router.post("/submit")
async def submit_user_input(
    request: Request,
    text: str = Form(None),
    url: str = Form(None),
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    user_id: str = Depends(get_current_user),
    user_input_collection = Depends(get_user_collection)
):
    input_data = {}
    if text:
        input_data["text"] = text
    if url:
        input_data["url"] = url
    if image:
        filename = f"uploads/images/{datetime.utcnow().isoformat()}_{image.filename}"
        with open(filename, "wb") as f:
            f.write(await image.read())
        input_data["image_filename"] = filename
    if audio:
        filename = f"uploads/audio/{datetime.utcnow().isoformat()}_{audio.filename}"
        with open(filename, "wb") as f:
            f.write(await audio.read())
        input_data["audio_filename"] = filename

    if not input_data:
        raise HTTPException(status_code=422, detail="At least one input must be provided.")

    input_data["user_id"] = user_id
    input_data["created_at"] = datetime.utcnow()

    result = user_input_collection.insert_one(input_data)

    return api_response(
        message="User input submitted successfully",
        status=201,
        data={"input_id": str(result.inserted_id)}
    )

@router.get("/all")
async def get_all_user_inputs(
    user_id: str = Depends(get_current_user),
    user_input_collection = Depends(get_user_collection)
):
    inputs = list(user_input_collection.find({"user_id": user_id}))
    for item in inputs:
        item["_id"] = str(item["_id"])
    return api_response(
        message="User input list fetched successfully",
        status=200,
        data=inputs
    )