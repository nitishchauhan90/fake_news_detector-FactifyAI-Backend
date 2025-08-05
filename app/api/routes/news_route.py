import os
import httpx
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from app.utils.api_response import api_response  # adjust path if needed

load_dotenv()

router = APIRouter(prefix="/api/news", tags=["News"])

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

@router.get("/latest")
async def get_latest_news():
    params = {
        "apiKey": NEWS_API_KEY,
        "country": "us",
        "category": "business",
        "pageSize": 50
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(NEWS_API_URL, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch news")

    data = response.json()
    if data.get("status") != "ok":
        raise HTTPException(status_code=502, detail="Invalid response from NewsAPI")

    # Extract and simplify articles
    articles = [
        {
            "title": article.get("title"),
            "description": article.get("description"),
            "url": article.get("url"),
            "image": article.get("urlToImage"),
            "published_at": article.get("publishedAt"),
            "source": article.get("source", {}).get("name"),
        }
        # for article in data.get("articles", [])[:12]  # Ensures only 12 are returned
        for article in data.get("articles", [])
        if article.get("description") and article.get("urlToImage")
    ]
    top_12_articles = articles[:12]
    return api_response("Top 12 business news fetched successfully", 200, {
        "totalResults": len(top_12_articles),
        "articles": top_12_articles
    })