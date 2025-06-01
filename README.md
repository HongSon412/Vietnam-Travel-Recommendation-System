# Vietnam Travel Recommendation System

An intelligent recommendation chatbot system using AI and LLM to recommend travel destinations in Vietnam based on weather data and user preferences.

## 🌟 Key Features

- **AI Chatbot**: Utilizes OpenAI for natural language understanding
- **Smart Clustering**: Weighted KMeans to group destinations by weather conditions
- **Interactive Map**: Displays recommendations on a Leaflet map
- **User-Friendly Interface**: Simple and easy-to-use web interface
- **Conversation History Storage**: SQLite database for storing conversations
## 🏗️ System Architecture

```
├── main.py                 # Main FastAPI backend
├── data/                   # Contains data and models
├── models/
│   ├── clustering.py       # Weighted KMeans model
│   └── database.py         # SQLite database models
├── services/
│   ├── openai_service.py   # OpenAI integration
│   └── recommendation_service.py # Recommendation logic
├── templates/
│   └── index.html          # Main frontend
├── static/
│   ├── style.css          # CSS styling
│   └── script.js          # JavaScript logic
├── df_weather.csv         # Weather data
├── requirements.txt       # Dependencies
└── .env                   # Environment variables
```

## 🚀 Installation Guide

### 1. Clone Repository

```bash
git clone <repository-url>
cd Vietnam-Travel-Recommendation-System
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Edit the `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./chatbot.db
DEBUG=True
```

### 5. Start the Application

```bash
python main.py
```

### 6. Access the Application

Open a browser and visit: `http://localhost:8000`

## 🎯 How to Use

### 1. Chat with the Chatbot

Enter queries such as:
- "Tôi muốn đi du lịch tháng 11, thích khí hậu mát và ít mưa"
- "Địa điểm ven biển, thời tiết nóng, tháng 6"
- "Miền núi, ít mưa, khí hậu ôn hòa"

### 2. View Recommendations

- The chatbot will analyze the request and provide recommendations
- Destinations are displayed on the map
- Click on a destination to view detailed information

### 3. Explore the Map

- Zoom in/out for details
- Click on markers to view information
- Use the "Reset View" button to center the map

## 🔧 API Endpoints

### POST /chat
Gửi tin nhắn đến chatbot

**Request:**
```json
{
    "message": "Tôi muốn đi du lịch tháng 12",
    "user_id": "anonymous"
}
```

**Response:**
```json
{
    "response": "Dựa trên yêu cầu của bạn...",
    "recommendations": [...],
    "preferences": {...},
    "timestamp": "2025-01-06T00:00:00"
}
```

### GET /location/{location_name}
Retrieve detailed information about a location

### GET /clusters
Retrieve clustering information

### GET /history
Retrieve conversation history

### GET /health
Check system status

## 🧠 Weighted KMeans Algorithm

The system uses a weighted KMeans algorithm to cluster destinations:

### Features Used:
- `day.avgtemp_c`: Average temperature
- `day.maxwind_kph`: Maximum wind speed
- `day.totalprecip_mm`: Total precipitation
- `day.avgvis_km`: Average visibility
- `day.avghumidity`: Average humidity
- `day.uv`: UV index

### Weight Adjustment:
- The chatbot automatically adjusts weights based on user preferences
- Example: If the user cares about temperature → increase weight for `avgtemp_c`

## 📊 Data  

Click on the [dataset](https://www.kaggle.com/datasets/hoantainson/dataset-weather-vit-nam-trong-1-nm-li) for more details.

## 🤝 Contributing

1. Fork repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request
