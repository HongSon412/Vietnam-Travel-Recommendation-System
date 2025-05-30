import pandas as pd
import numpy as np
from models.clustering import WeightedKMeans
from services.openai_service import OpenAIService
import json

class RecommendationService:
    def __init__(self, weather_data_path=r"data\df_weather.csv"):
        self.weather_data_path = weather_data_path
        self.clustering_model = WeightedKMeans(n_clusters=8)
        self.openai_service = OpenAIService()
        self.df = None
        self.model_trained = False
        
    def load_and_prepare_data(self):
        """Load and prepare weather data"""
        try:
            self.df = pd.read_csv(self.weather_data_path)
            
            # Convert date column
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df['month'] = self.df['date'].dt.month
            
            print(f"Loaded {len(self.df)} weather records for {self.df['location.name'].nunique()} locations")
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def train_clustering_model(self, force_retrain=False):
        """Train or load the clustering model"""
        model_path = r"data\weather_clusters.pkl"
        
        if not force_retrain and self.clustering_model.load_model(model_path):
            print("Loaded existing clustering model")
            self.model_trained = True
            return True
        
        if self.df is None:
            if not self.load_and_prepare_data():
                return False
        
        print("Training clustering model...")
        try:
            self.clustering_model.fit(self.df)
            self.clustering_model.save_model(model_path)
            self.model_trained = True
            print("Clustering model trained and saved successfully")
            return True
            
        except Exception as e:
            print(f"Error training clustering model: {e}")
            return False
    
    def update_weights_from_preferences(self, preferences):
        """Update clustering weights based on user preferences"""
        weights = {
            'day.avgtemp_c': 1.0,
            'day.maxwind_kph': 1.0,
            'day.totalprecip_mm': 1.0,
            'day.avgvis_km': 1.0,
            'day.avghumidity': 1.0,
            'day.uv': 1.0
        }
        
        # Adjust weights based on preferences
        if preferences.get('temperature_preference'):
            weights['day.avgtemp_c'] = 2.0  # Increase temperature importance
        
        if preferences.get('rain_tolerance'):
            weights['day.totalprecip_mm'] = 2.0  # Increase precipitation importance
        
        if preferences.get('activity_type') == 'thể thao':
            weights['day.maxwind_kph'] = 1.5  # Wind matters for sports
            weights['day.uv'] = 1.5  # UV matters for outdoor activities
        
        self.clustering_model.set_weights(weights)
    
    def filter_by_month(self, month):
        """Filter data by specific month"""
        if month and self.df is not None:
            return self.df[self.df['month'] == month]
        return self.df
    
    def get_recommendations(self, user_message):
        """Get travel recommendations based on user message"""
        if not self.model_trained:
            if not self.train_clustering_model():
                return {
                    "error": "Could not initialize recommendation system",
                    "recommendations": [],
                    "response": "Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau."
                }
        
        try:
            # Extract preferences using OpenAI
            preferences = self.openai_service.extract_travel_preferences(user_message)
            print(f"Extracted preferences: {preferences}")
            
            # Update clustering weights based on preferences
            self.update_weights_from_preferences(preferences)
            
            # Filter data by month if specified
            filtered_df = self.filter_by_month(preferences.get('month'))
            
            # Convert preferences to numerical values for similarity calculation
            numerical_preferences = self._convert_preferences_to_numerical(preferences)
            
            # Get recommendations using clustering model
            recommendations = self.clustering_model.find_similar_locations(
                numerical_preferences, top_k=8
            )
            
            # Apply additional filtering based on preferences
            recommendations = self._apply_preference_filters(recommendations, preferences)
            
            # Generate natural language response
            response = self.openai_service.generate_response(
                user_message, recommendations, preferences
            )
            
            return {
                "preferences": preferences,
                "recommendations": recommendations[:5],  # Top 5 recommendations
                "response": response,
                "cluster_info": self.clustering_model.get_cluster_characteristics()
            }
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {
                "error": str(e),
                "recommendations": [],
                "response": "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."
            }
    
    def _convert_preferences_to_numerical(self, preferences):
        """Convert text preferences to numerical values"""
        numerical = {}
        
        # Temperature mapping
        temp_map = {"mát": 22, "ôn hòa": 26, "nóng": 32}
        if preferences.get('temperature_preference'):
            numerical['temperature'] = temp_map.get(preferences['temperature_preference'], 26)
        
        # Rain tolerance mapping
        rain_map = {"ít": "low", "vừa": "medium", "nhiều": "high"}
        if preferences.get('rain_tolerance'):
            numerical['rain_tolerance'] = rain_map.get(preferences['rain_tolerance'], "medium")
        
        # Terrain preference
        if preferences.get('terrain_preference'):
            numerical['terrain'] = preferences['terrain_preference']
        
        return numerical
    
    def _apply_preference_filters(self, recommendations, preferences):
        """Apply additional filtering based on preferences"""
        if not recommendations:
            return recommendations
        
        filtered = []
        for rec in recommendations:
            include = True
            
            # Filter by terrain if specified
            if preferences.get('terrain_preference'):
                if preferences['terrain_preference'] not in rec.get('location.terrain', ''):
                    include = False
            
            if include:
                filtered.append(rec)
        
        return filtered if filtered else recommendations  # Return original if no matches
    
    def get_cluster_analysis(self):
        """Get detailed cluster analysis"""
        if not self.model_trained:
            return None
        
        return self.clustering_model.get_cluster_characteristics()
    
    def get_location_details(self, location_name):
        """Get detailed weather information for a specific location"""
        if self.df is None:
            return None
        
        location_data = self.df[self.df['location.name'] == location_name]
        if location_data.empty:
            return None
        
        # Calculate monthly averages
        monthly_stats = location_data.groupby('month').agg({
            'day.avgtemp_c': 'mean',
            'day.totalprecip_mm': 'mean',
            'day.avghumidity': 'mean',
            'day.maxwind_kph': 'mean',
            'day.uv': 'mean'
        }).round(2)
        
        return {
            'location_info': {
                'name': location_name,
                'region': location_data['location.region'].iloc[0],
                'terrain': location_data['location.terrain'].iloc[0],
                'latitude': location_data['location.lat'].iloc[0],
                'longitude': location_data['location.lon'].iloc[0]
            },
            'monthly_averages': monthly_stats.to_dict('index'),
            'overall_averages': {
                'temperature': location_data['day.avgtemp_c'].mean(),
                'precipitation': location_data['day.totalprecip_mm'].mean(),
                'humidity': location_data['day.avghumidity'].mean(),
                'wind_speed': location_data['day.maxwind_kph'].mean(),
                'uv_index': location_data['day.uv'].mean()
            }
        }
