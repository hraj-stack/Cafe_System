import json

class AIRecommender:
    """
    Mock AI Recommender.
    In a real-world scenario, this would interface with an LLM via API 
    (e.g., OpenAI API) to generate contextual recommendations.
    """
    
    MOOD_RECOMMENDATIONS = {
        'Happy': ['Algorithm Affogato', 'Cheesecake', 'Cold Brew'],
        'Stressed': ['Chamomile Tea', 'Lavender Latte', 'Dark Chocolate Muffin'],
        'Tired': ['Espresso', 'Quantum Cold Brew', 'Energy Bar'],
        'Energetic': ['Fruit Smoothie', 'Avocado Toast', 'Nitro Cold Brew'],
        'Focused': ['Neural Latte', 'Protein Sandwich', 'Dark Chocolate Brownie'],
        'Romantic': ['Red Velvet Cake', 'Mocha', 'Macarons'],
        'Casual': ['Cappuccino', 'Croissant', 'Fries']
    }

    @classmethod
    def get_recommendation(cls, mood):
        # In the future, this would call `openai.ChatCompletion.create(...)`
        recs = cls.MOOD_RECOMMENDATIONS.get(mood, ['House Blend Coffee', 'Muffin'])
        return json.dumps(recs)
