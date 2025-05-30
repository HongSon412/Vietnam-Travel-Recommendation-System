import openai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def extract_travel_preferences(self, user_message):
        """Extract travel preferences from user message using OpenAI"""
        
        system_prompt = """
        Bạn là một AI chuyên phân tích yêu cầu du lịch của người dùng. 
        Hãy phân tích tin nhắn của người dùng và trích xuất các thông tin sau dưới dạng JSON:
        
        {
            "month": số tháng (1-12) hoặc null,
            "temperature_preference": "mát" | "ôn hòa" | "nóng" | null,
            "rain_tolerance": "ít" | "vừa" | "nhiều" | null,
            "terrain_preference": "miền núi" | "ven biển" | "đồng bằng" | null,
            "activity_type": "nghỉ dưỡng" | "khám phá" | "thể thao" | "văn hóa" | null,
            "keywords": ["từ khóa quan trọng từ tin nhắn"]
        }
        
        Chỉ trả về JSON, không có text khác.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                preferences = json.loads(json_match.group())
                return preferences
            else:
                return self._parse_fallback(user_message)
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._parse_fallback(user_message)
    
    def _parse_fallback(self, user_message):
        """Fallback parsing method if OpenAI fails"""
        preferences = {
            "month": None,
            "temperature_preference": None,
            "rain_tolerance": None,
            "terrain_preference": None,
            "activity_type": None,
            "keywords": []
        }
        
        message_lower = user_message.lower()
        
        # Extract month
        months = {
            "tháng 1": 1, "tháng 2": 2, "tháng 3": 3, "tháng 4": 4,
            "tháng 5": 5, "tháng 6": 6, "tháng 7": 7, "tháng 8": 8,
            "tháng 9": 9, "tháng 10": 10, "tháng 11": 11, "tháng 12": 12,
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "xuân": 3, "hè": 6, "thu": 9, "đông": 12 
        }
        
        for month_str, month_num in months.items():
            if month_str in message_lower:
                preferences["month"] = month_num
                break
        
        # Extract temperature preference
        if any(word in message_lower for word in ["mát", "lạnh", "cool", "cold"]):
            preferences["temperature_preference"] = "mát"
        elif any(word in message_lower for word in ["nóng", "hot", "warm"]):
            preferences["temperature_preference"] = "nóng"
        elif any(word in message_lower for word in ["ôn hòa", "dễ chịu", "mild"]):
            preferences["temperature_preference"] = "ôn hòa"
        
        # Extract rain tolerance
        if any(word in message_lower for word in ["ít mưa", "khô", "dry"]):
            preferences["rain_tolerance"] = "ít"
        elif any(word in message_lower for word in ["nhiều mưa", "mưa", "rain"]):
            preferences["rain_tolerance"] = "nhiều"
        
        # Extract terrain preference
        if any(word in message_lower for word in ["núi", "mountain", "hill"]):
            preferences["terrain_preference"] = "miền núi"
        elif any(word in message_lower for word in ["biển", "beach", "coast", "ven biển"]):
            preferences["terrain_preference"] = "ven biển"
        elif any(word in message_lower for word in ["đồng bằng", "plain", "delta"]):
            preferences["terrain_preference"] = "đồng bằng"
        
        return preferences
    
    def generate_response(self, user_message, recommendations, preferences):
        """Generate a natural response with recommendations"""
        
        system_prompt = """
        Bạn là một chatbot tư vấn du lịch thông minh cho Việt Nam. 
        Hãy trả lời một cách tự nhiên, thân thiện và hữu ích.
        Sử dụng thông tin khuyến nghị để đưa ra lời khuyên cụ thể về địa điểm du lịch.
        Giải thích tại sao những địa điểm này phù hợp với yêu cầu của người dùng.
        Trả lời bằng tiếng Việt.
        """
        
        # Prepare recommendation text
        rec_text = "Dựa trên yêu cầu của bạn, tôi khuyến nghị các địa điểm sau:\n\n"
        for i, rec in enumerate(recommendations[:5], 1):
            rec_text += f"{i}. {rec['location.name']} ({rec['location.region']})\n"
            rec_text += f"   - Địa hình: {rec['location.terrain']}\n"
            if 'score' in rec:
                rec_text += f"   - Độ phù hợp: {rec['score']:.1f}/10\n"
            rec_text += "\n"
        
        user_prompt = f"""
        Tin nhắn người dùng: "{user_message}"
        
        Sở thích đã phân tích: {json.dumps(preferences, ensure_ascii=False)}
        
        Khuyến nghị địa điểm:
        {rec_text}
        
        Hãy trả lời một cách tự nhiên và hữu ích.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(recommendations)
    
    def _generate_fallback_response(self, recommendations):
        """Fallback response if OpenAI fails"""
        if not recommendations:
            return "Xin lỗi, tôi không tìm thấy địa điểm phù hợp với yêu cầu của bạn. Bạn có thể thử mô tả chi tiết hơn không?"
        
        response = "Dựa trên yêu cầu của bạn, tôi khuyến nghị các địa điểm sau:\n\n"
        for i, rec in enumerate(recommendations[:3], 1):
            response += f"{i}. {rec['location.name']} - {rec['location.region']}\n"
            response += f"   Địa hình: {rec['location.terrain']}\n\n"
        
        response += "Những địa điểm này có điều kiện thời tiết phù hợp với sở thích của bạn!"
        return response
