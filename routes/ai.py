"""
AI routes blueprint for HRD Café.
Handles AI-powered menu recommendations based on mood.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from models import db
from models.recommendation import Recommendation
from services.ai_recommender import AIRecommender

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai/recommend', methods=['GET'])
def recommend_page():
    """Render the AI recommendation page."""
    return render_template('ai_recommend.html')


@ai_bp.route('/ai/recommend', methods=['POST'])
def get_recommendations():
    """Get AI-powered recommendations based on mood (JSON endpoint)."""
    try:
        data = request.get_json()

        if not data or 'mood' not in data:
            return jsonify({
                'success': False,
                'message': 'Please provide a mood to get recommendations.'
            }), 400

        mood = data['mood'].strip()

        if not mood:
            return jsonify({
                'success': False,
                'message': 'Mood cannot be empty.'
            }), 400

        # Get recommendations from AI service
        recommender = AIRecommender()
        recommendations = recommender.get_recommendations(mood)

        # Save recommendation record to database
        try:
            user_id = current_user.id if current_user.is_authenticated else None
            rec_record = Recommendation(
                user_id=user_id,
                mood=mood,
                recommended_items=str(recommendations)
            )
            db.session.add(rec_record)
            db.session.commit()
        except Exception:
            # Don't fail the request if saving the record fails
            db.session.rollback()

        return jsonify({
            'success': True,
            'mood': mood,
            'recommendations': recommendations
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'An error occurred while generating recommendations: {str(e)}'
        }), 500
