from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import json
import os
from datetime import datetime

from models.database import get_db, create_tables, ChatHistory
from services.recommendation_service import RecommendationService

# Initialize recommendation service
recommendation_service = RecommendationService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    print("Initializing recommendation system...")
    if recommendation_service.load_and_prepare_data():
        recommendation_service.train_clustering_model()
        print("Recommendation system ready!")
    else:
        print("Warning: Could not initialize recommendation system")
    yield
    # Shutdown
    print("Shutting down...")

# Initialize FastAPI app
app = FastAPI(title="Vietnam Travel Chatbot", version="1.0.0", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    response: str
    recommendations: List[dict]
    preferences: dict
    timestamp: datetime



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage, db: Session = Depends(get_db)):
    """Main chat endpoint"""
    try:
        # Get recommendations from the service
        result = recommendation_service.get_recommendations(chat_message.message)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Save chat history to database
        chat_history = ChatHistory(
            user_message=chat_message.message,
            bot_response=result["response"],
            recommended_locations=json.dumps(result["recommendations"], ensure_ascii=False),
            user_id=chat_message.user_id
        )
        db.add(chat_history)
        db.commit()

        return ChatResponse(
            response=result["response"],
            recommendations=result["recommendations"],
            preferences=result["preferences"],
            timestamp=datetime.now()
        )

    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/location/{location_name}")
async def get_location_details(location_name: str):
    """Get detailed information about a specific location"""
    try:
        details = recommendation_service.get_location_details(location_name)
        if details is None:
            raise HTTPException(status_code=404, detail="Location not found")
        return details
    except Exception as e:
        print(f"Location details error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/clusters")
async def get_cluster_analysis():
    """Get cluster analysis information"""
    try:
        clusters = recommendation_service.get_cluster_analysis()
        if clusters is None:
            raise HTTPException(status_code=500, detail="Clustering model not ready")
        return {"clusters": clusters}
    except Exception as e:
        print(f"Cluster analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/history")
async def get_chat_history(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent chat history"""
    try:
        history = db.query(ChatHistory).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": h.id,
                "user_message": h.user_message,
                "bot_response": h.bot_response,
                "timestamp": h.timestamp,
                "recommendations": json.loads(h.recommended_locations) if h.recommended_locations else []
            }
            for h in history
        ]
    except Exception as e:
        print(f"History error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_trained": recommendation_service.model_trained,
        "data_loaded": recommendation_service.df is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
