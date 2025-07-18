from fastapi import APIRouter, HTTPException, status ,Depends
from ..schemas.contact_schema import ContactFormSchema
from ..core.database import get_contact_collection
from pymongo.collection import Collection
import datetime
router = APIRouter(
    prefix="/api/misc",
    tags=["Misc"]
)

@router.post("/contact",response_model=dict)
async def receive_contact_form(
    data: ContactFormSchema,
    contact_collection = Depends(get_contact_collection)
):
    contact_doc = data.dict()
    contact_doc["created_at"] = datetime.datetime.utcnow()
    result = contact_collection.insert_one(contact_doc)
    
    # Ensure Mongo ObjectId is converted to string in the response
    response_data = contact_doc.copy()
    response_data["_id"] = str(result.inserted_id)

    return {
        "message": "Contact form received successfully.",
        "status": 200,
        "success": True,
        "data": response_data
    }
