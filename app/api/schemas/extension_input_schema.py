from pydantic import BaseModel 


class AnalyzeRequest(BaseModel):
    text: str

class FeedbackData(BaseModel):
    reason: str
    details: str = ""


