from fastapi import APIRouter, Request ,Depends,HTTPException
from fastapi.responses import JSONResponse
from ..core.database import get_ip_collection ,get_feedback_collection
from ..config.config import LOGIN_REDIRECT
from ...utils.api_response import api_response
from ..services.extension_services import analyze_sentiment , check_authenticity , google_fact_check
from ..schemas.extension_input_schema import AnalyzeRequest , FeedbackData
from datetime import datetime
router = APIRouter(
    prefix="/api/extension",
    tags=["extension"]
)

MAX_FREE_REQUESTS = 3

@router.get("/ip-check")
async def fact_check_limit_check(request: Request, query: str ,collection = Depends(get_ip_collection)):
    
    client_ip = request.client.host
    
    ip_data = collection.find_one({"ip": client_ip})

    if ip_data:
        if ip_data["count"] > MAX_FREE_REQUESTS - 1:
            
            return JSONResponse(
                status_code=403,
                content={
                    "limit_exceeded": True,
                    "message": "Free request limit reached. Please log in.",
                    "redirect_url": LOGIN_REDIRECT 
                },
            )
        else:
            collection.update_one(
                {"ip": client_ip},
                {"$inc": {"count": 1}}
            )
    else:
        collection.insert_one({
            "ip": client_ip,
            "count": 1
        })

    # If within limit, return a simple message
    return {
        "limit_exceeded": False,
        "remaining": MAX_FREE_REQUESTS - (ip_data["count"] + 1 if ip_data else 1),
        "message": "Allowed"
    }


@router.post("/analyze")
async def analyze_input(
    request:AnalyzeRequest
):
    combined_text = request.text
    if not combined_text:
        return api_response("No input provided.",400)

    sentiment = analyze_sentiment(combined_text)
    authenticity = check_authenticity(combined_text)
    fact_check_result = google_fact_check(combined_text)
    return {
        "message": "Analysis completed",
        "sentiment": sentiment,
        "authenticity": authenticity,
        "fact_check_result": fact_check_result,
    }

# @router.post("/feedback/submit")
# async def submit_feedback(
#     data: FeedbackData,
#     request: Request,
#     feedback_collection=Depends(get_feedback_collection)
# ):
#     try:
#         feedback = {
#             "reason": data.reason,
#             "details": data.details,
#             "timestamp": datetime.utcnow(),
#         }

#         result = feedback_collection.insert_one(feedback)
        
#         return api_response("Feedback submitted successfully", 200, {"feedback_id": str(result.inserted_id)})

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=api_response(f"Error submitting feedback: {str(e)}", 500))
    

@router.post("/feedback")
async def submit_feedback(
    data: FeedbackData,
    request: Request,
    feedback_collection=Depends(get_feedback_collection)
):
    feedback = {
        "reason": data.reason,
        "details": data.details,
        "submitted_at": datetime.utcnow(),
        "client_ip": request.client.host
    }

    try:
        result = feedback_collection.insert_one(feedback)
        return api_response("Feedback submitted successfully", 200)
    except Exception as e:
        return api_response(f"Error submitting feedback: {str(e)}", 500)