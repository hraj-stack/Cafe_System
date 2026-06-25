from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models.menu import Menu
from models.contact import Contact
from services.ai_recommender import AIRecommender
from models import db
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    items = Menu.query.all()
    return render_template('landing_page.html', items=items)

@main_bp.route('/home')
def home():
    return render_template('home.html')

@main_bp.route('/menu')
def menu():
    items = Menu.query.all()
    categories = {}
    for item in items:
        if item.category not in categories:
            categories[item.category] = []
        categories[item.category].append(item)
        
    def get_slug(name):
        return name.lower().replace(" & ", "_").replace(" ", "_").replace("'", "")
        
    return render_template('menu.html', categories=categories, get_slug=get_slug)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        new_contact = Contact(name=name, email=email, phone=phone, message=message)
        db.session.add(new_contact)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')

@main_bp.route('/ai-assistant', methods=['GET', 'POST'])
def ai_assistant():
    recommendations = None
    selected_mood = None
    if request.method == 'POST':
        selected_mood = request.form.get('mood')
        if selected_mood:
            recs_json = AIRecommender.get_recommendation(selected_mood)
            recommendations = json.loads(recs_json)
            # If user is logged in, save to Recommendation model (to be added)
    
    moods = ['Happy', 'Stressed', 'Tired', 'Energetic', 'Focused', 'Romantic', 'Casual']
    return render_template('ai_assistant.html', moods=moods, recommendations=recommendations, selected_mood=selected_mood)


@main_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'message': 'Message is required.'}), 400
        
        message = data['message'].strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({'success': False, 'message': 'Message cannot be empty.'}), 400
            
        from services.gemini_service import GeminiService
        
        # Retrieve all menu items to pass as context
        menu_items = Menu.query.all()
        menu_context = "\n".join([
            f"- ID: {item.item_id} | Name: {item.name} | Category: {item.category} | Price: ₹{int(item.price)} | Description: {item.description}" 
            for item in menu_items
        ])
        
        ai_res = GeminiService.chat(history, message, menu_context=menu_context)
        
        if isinstance(ai_res, dict):
            response_text = ai_res.get('response', '')
            recommended_items = ai_res.get('recommended_items', [])
            for item in recommended_items:
                try:
                    menu_item = Menu.query.get(int(item.get('id', 0)))
                    if menu_item:
                        item['description'] = menu_item.description or ""
                        slug = menu_item.name.lower().replace(" & ", "_").replace(" ", "_").replace("'", "")
                        item['image_url'] = f"/static/images/menu_previews/{slug}.jpg"
                except Exception as ex:
                    print(f"Error enriching item details: {ex}")
        else:
            response_text = ai_res
            recommended_items = []
        
        return jsonify({
            'success': True,
            'response': response_text,
            'recommended_items': recommended_items
        }), 200
    except Exception as e:
        print(f"Error in ai_chat endpoint: {e}")
        return jsonify({
            'success': False,
            'message': 'The AI Assistant is currently unavailable. Please try again in a few moments.'
        }), 500
