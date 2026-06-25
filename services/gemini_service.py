import os
import requests
import json

class GeminiService:
    @classmethod
    def chat(cls, history, message, menu_context=None):
        """
        Send the conversation history and the new message to Google's Gemini API.
        Enforces a food-focused system prompt and handles language mapping.
        If menu_context is provided, enforces structured JSON output.
        """
        api_key = os.environ.get('GEMINI_API_KEY')
        print(f"DEBUG: Resolving GEMINI_API_KEY = {api_key[:8]}... (len={len(api_key)})" if api_key else "DEBUG: GEMINI_API_KEY is None/Empty")
        if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
            if menu_context:
                return {
                    "response": "I'm sorry, my AI connection is not configured at the moment (missing GEMINI_API_KEY). Please configure the API key in the .env file to enable chat.",
                    "recommended_items": []
                }
            return ("I'm sorry, my AI connection is not configured at the moment (missing GEMINI_API_KEY). "
                    "Please configure the API key in the .env file to enable chat.")

        model = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # Convert history format to Gemini contents format
        contents = []
        for turn in history:
            role = turn.get('role', 'user')
            if role in ('bot', 'assistant', 'model'):
                role = 'model'
            else:
                role = 'user'
            
            text = turn.get('text') or turn.get('content') or ""
            if text:
                contents.append({
                    "role": role,
                    "parts": [{"text": text}]
                })
        
        # Append the new message
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        # Gemini API requires the first turn to be from 'user' — drop any leading model turns
        while contents and contents[0].get('role') != 'user':
            contents.pop(0)

        if menu_context:
            system_instruction = (
                "You are HRD AI, a friendly, helpful, and expert food and restaurant AI Assistant for HRD Cafe. "
                "You specialize in food recommendations, menu suggestions, ingredients, recipes, cooking tips, "
                "beverages, nutrition, combos, and dining suggestions. "
                "We have a menu with the following items available in our cafe:\n"
                f"{menu_context}\n\n"
                "Your task is to respond to the user's message. "
                "If they are asking for recommendations, recommend the best matching items from our menu context above based on their mood, price, and preferences. "
                "You MUST support the following smart capabilities:\n"
                "1. Budget-based recommendations: If the user specifies a budget (e.g. 'under ₹250'), filter the menu items and recommend only those within the budget (e.g., Earl Grey Tea, Long Black, Tiramisu, Rum Cake, etc., where price <= 250).\n"
                "2. Mood-based recommendations: Recommend items that fit their state of mind (e.g., Stressed/Tired -> recommend warm teas, Matcha Latte, Kefir, or Espresso; Happy/Celebratory -> recommend rich desserts like Brownie Gelato, Cheesecakes; Focused -> recommend clean dark coffee like Long Black, House Blend).\n"
                "3. Group recommendations: Recommend a balanced selection of drinks, sharing snacks, and desserts if the user mentions multiple people, friends, or a party.\n"
                "4. Healthy recommendations: Recommend nutritious items like salads (Spinach, Arugula, Avocado), clean soups (Pumpkin, Cream of Potato), or organic kefir and herbal teas.\n"
                "5. Combo suggestions: Recommend official combos (like Espresso & Cheesecake Combo, Soup & Salad Combo) or suggest custom beverage & snack/dessert pairings.\n\n"
                "Always respond in JSON format with the exact same schema:\n"
                "{\n"
                "  \"response\": \"Your warm, welcoming, professional message explaining your suggestions or answering their question. Support Hindi/Hinglish if the user asks in Hindi/Hinglish. Format the text with proper paragraphs. Do not use markdown inside this JSON string other than normal line breaks.\",\n"
                "  \"recommended_items\": [\n"
                "    {\n"
                "      \"id\": 10,  // The item_id of the recommended menu item from the menu context\n"
                "      \"name\": \"Tiramisu\", // The exact name of the recommended menu item from the menu context\n"
                "      \"price\": 250 // The price of the recommended menu item from the menu context\n"
                "    }\n"
                "  ]\n"
                "}\n"
                "If the user is not asking for food/drink recommendations or if no items match their request, set \"recommended_items\" to an empty array [].\n"
                "If the user asks questions unrelated to food, drinks, café, recipes, cooking, nutrition, or kitchen topics, "
                "politely redirect them back to food (e.g., 'I am specialized in food and beverage recommendations. "
                "I'd love to help you with menu options, recipes, or pairing suggestions instead!') and keep \"recommended_items\" as []."
            )
        else:
            system_instruction = (
                "You are HRD AI, a friendly, helpful, and expert food and restaurant AI Assistant for HRD Cafe. "
                "You specialize in food recommendations, menu suggestions, ingredients, recipes, cooking tips, "
                "beverages, nutrition, combos, and dining suggestions. "
                "Automatically detect the user's language. If they ask in Hindi, respond in Hindi. "
                "If they ask in English, respond in English. If they use Hinglish (Hindi written in English alphabet), "
                "respond naturally in Hinglish. "
                "Keep your tone warm, welcoming, fast-paced, and professional. "
                "If the user asks questions unrelated to food, drinks, café, recipes, cooking, nutrition, or kitchen topics, "
                "politely redirect them back to food (e.g., 'I am specialized in food and beverage recommendations. "
                "I'd love to help you with menu options, recipes, or pairing suggestions instead!')."
            )

        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            }
        }

        if menu_context:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                res_data = response.json()
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        text_val = parts[0].get('text', "")
                        if menu_context:
                            try:
                                return json.loads(text_val)
                            except Exception as e:
                                print(f"Error parsing JSON from Gemini response: {e}. Raw response: {text_val}")
                                return {
                                    "response": text_val,
                                    "recommended_items": []
                                }
                        return text_val
                if menu_context:
                    return {
                        "response": "I received an empty response. Please try asking in a different way.",
                        "recommended_items": []
                    }
                return "I received an empty response. Please try asking in a different way."
            else:
                print(f"Gemini API error {response.status_code}: {response.text}")
                err_msg = "The AI Assistant is currently unavailable. Please try again in a few moments."
                if menu_context:
                    return {"response": err_msg, "recommended_items": []}
                return err_msg
        except requests.exceptions.Timeout:
            print("Gemini API request timed out.")
            err_msg = "The AI Assistant is currently unavailable. Please try again in a few moments."
            if menu_context:
                return {"response": err_msg, "recommended_items": []}
            return err_msg
        except Exception as e:
            print(f"Exception during Gemini API request: {e}")
            err_msg = "The AI Assistant is currently unavailable. Please try again in a few moments."
            if menu_context:
                return {"response": err_msg, "recommended_items": []}
            return err_msg
