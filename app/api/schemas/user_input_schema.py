from typing import Literal , Optional, List
from pydantic import BaseModel, HttpUrl ,Field ,root_validator
from datetime import datetime

class InputMetaData(BaseModel):
    input_type: Literal["text", "url", "image", "audio"]
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str  # Link user ID to metadata

class TextInputData(BaseModel):
    text: str
    metadata: InputMetaData

class URLInputData(BaseModel):
    url: HttpUrl
    metadata: InputMetaData

class FileInputData(BaseModel):
    filename: str
    content_type: str
    metadata: InputMetaData

class AnalysisResult(BaseModel):
    input_id: str
    user_id: str
    result_label: Literal["fake", "real"]
    confidence: float
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

class UserInputData(BaseModel):
    text: Optional[str] = None
    url: Optional[HttpUrl] = None
    image_filename: Optional[str] = None  # store image filename/path
    audio_filename: Optional[str] = None  # store audio filename/path
    user_id: str  # Link user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @root_validator
    def at_least_one_field_must_be_present(cls, values):
        text, url, image_filename, audio_filename = (
            values.get("text"),
            values.get("url"),
            values.get("image_filename"),
            values.get("audio_filename"),
        )
        if not any([text, url, image_filename, audio_filename]):
            raise ValueError("At least one of text, url, image_filename, or audio_filename must be provided.")
        return values

class UserInputWithResult(BaseModel):
    input_data: UserInputData
    analysis_result: AnalysisResult

class UserHistoryResponse(BaseModel):
    user_id: str
    history: List[UserInputWithResult]
