from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatbot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    recommended_locations = Column(Text)  # JSON string of recommended locations
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, default="anonymous")  # For future user management
    
class WeatherCluster(Base):
    __tablename__ = "weather_clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String, nullable=False)
    location_region = Column(String, nullable=False)
    location_terrain = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    cluster_id = Column(Integer, nullable=False)
    avg_temp = Column(Float)
    avg_humidity = Column(Float)
    avg_precipitation = Column(Float)
    avg_wind_speed = Column(Float)
    avg_visibility = Column(Float)
    avg_uv = Column(Float)
    
def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
