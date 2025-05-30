import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import pickle
import os

class WeightedKMeans:
    def __init__(self, n_clusters=8, random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        self.feature_weights = {
            'day.avgtemp_c': 1.0,
            'day.maxwind_kph': 1.0,
            'day.totalprecip_mm': 1.0,
            'day.avgvis_km': 1.0,
            'day.avghumidity': 1.0,
            'day.uv': 1.0
        }
        self.cluster_labels_ = None
        self.cluster_centers_ = None
        
    def set_weights(self, weights_dict):
        """Update feature weights based on user preferences"""
        for feature, weight in weights_dict.items():
            if feature in self.feature_weights:
                self.feature_weights[feature] = weight
                
    def prepare_data(self, df):
        """Prepare and aggregate weather data by location"""
        # Group by location and calculate averages
        location_features = df.groupby(['location.name', 'location.region', 'location.terrain', 'location.lat', 'location.lon']).agg({
            'day.avgtemp_c': 'mean',
            'day.maxwind_kph': 'mean', 
            'day.totalprecip_mm': 'mean',
            'day.avgvis_km': 'mean',
            'day.avghumidity': 'mean',
            'day.uv': 'mean'
        }).reset_index()
        
        return location_features
    
    def apply_weights(self, X):
        """Apply weights to features"""
        weighted_X = X.copy()
        for i, feature in enumerate(self.feature_weights.keys()):
            weighted_X[:, i] = weighted_X[:, i] * self.feature_weights[feature]
        return weighted_X
    
    def fit(self, df):
        """Fit the weighted KMeans model"""
        # Prepare data
        self.location_data = self.prepare_data(df)
        
        # Extract features for clustering
        feature_columns = list(self.feature_weights.keys())
        X = self.location_data[feature_columns].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Apply weights
        X_weighted = self.apply_weights(X_scaled)
        
        # Fit KMeans
        self.kmeans.fit(X_weighted)
        self.cluster_labels_ = self.kmeans.labels_
        self.cluster_centers_ = self.kmeans.cluster_centers_
        
        # Add cluster labels to location data
        self.location_data['cluster'] = self.cluster_labels_
        
        return self
    
    def predict(self, df):
        """Predict clusters for new data"""
        location_features = self.prepare_data(df)
        feature_columns = list(self.feature_weights.keys())
        X = location_features[feature_columns].values
        X = np.nan_to_num(X, nan=0.0)
        X_scaled = self.scaler.transform(X)
        X_weighted = self.apply_weights(X_scaled)
        return self.kmeans.predict(X_weighted)
    
    def get_cluster_characteristics(self):
        """Get characteristics of each cluster"""
        if self.location_data is None:
            return None
            
        cluster_chars = []
        feature_columns = list(self.feature_weights.keys())
        
        for cluster_id in range(self.n_clusters):
            cluster_data = self.location_data[self.location_data['cluster'] == cluster_id]
            if len(cluster_data) == 0:
                continue
                
            characteristics = {
                'cluster_id': cluster_id,
                'locations': cluster_data['location.name'].tolist(),
                'count': len(cluster_data),
                'avg_features': {}
            }
            
            for feature in feature_columns:
                characteristics['avg_features'][feature] = cluster_data[feature].mean()
                
            # Add descriptive labels
            avg_temp = characteristics['avg_features']['day.avgtemp_c']
            avg_precip = characteristics['avg_features']['day.totalprecip_mm']
            avg_humidity = characteristics['avg_features']['day.avghumidity']
            
            if avg_temp < 20:
                temp_label = "mát mẻ"
            elif avg_temp < 28:
                temp_label = "ôn hòa"
            else:
                temp_label = "nóng"
                
            if avg_precip < 2:
                rain_label = "ít mưa"
            elif avg_precip < 10:
                rain_label = "mưa vừa"
            else:
                rain_label = "nhiều mưa"
                
            characteristics['description'] = f"Khí hậu {temp_label}, {rain_label}"
            cluster_chars.append(characteristics)
            
        return cluster_chars
    
    def save_model(self, filepath):
        """Save the trained model"""
        model_data = {
            'scaler': self.scaler,
            'kmeans': self.kmeans,
            'feature_weights': self.feature_weights,
            'location_data': self.location_data,
            'cluster_labels_': self.cluster_labels_,
            'cluster_centers_': self.cluster_centers_
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath):
        """Load a trained model"""
        if not os.path.exists(filepath):
            return False
            
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            
        self.scaler = model_data['scaler']
        self.kmeans = model_data['kmeans']
        self.feature_weights = model_data['feature_weights']
        self.location_data = model_data['location_data']
        self.cluster_labels_ = model_data['cluster_labels_']
        self.cluster_centers_ = model_data['cluster_centers_']
        
        return True
    
    def find_similar_locations(self, preferences, top_k=5):
        """Find locations similar to user preferences"""
        if self.location_data is None:
            return []
            
        # Calculate similarity scores based on preferences
        scores = []
        for idx, row in self.location_data.iterrows():
            score = 0
            
            # Temperature preference
            if 'temperature' in preferences:
                temp_pref = preferences['temperature']
                temp_diff = abs(row['day.avgtemp_c'] - temp_pref)
                score += max(0, 10 - temp_diff)  # Higher score for closer temperature
            
            # Rain preference  
            if 'rain_tolerance' in preferences:
                rain_tolerance = preferences['rain_tolerance']
                if rain_tolerance == 'low' and row['day.totalprecip_mm'] < 2:
                    score += 5
                elif rain_tolerance == 'medium' and 2 <= row['day.totalprecip_mm'] < 10:
                    score += 5
                elif rain_tolerance == 'high' and row['day.totalprecip_mm'] >= 10:
                    score += 5
            
            # Terrain preference
            if 'terrain' in preferences:
                if preferences['terrain'] in row['location.terrain']:
                    score += 3
                    
            scores.append(score)
        
        # Get top recommendations
        self.location_data['score'] = scores
        recommendations = self.location_data.nlargest(top_k, 'score')
        
        return recommendations[['location.name', 'location.region', 'location.terrain', 
                              'location.lat', 'location.lon', 'cluster', 'score']].to_dict('records')
