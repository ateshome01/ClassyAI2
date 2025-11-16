from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

import os

# Get the path to the data file relative to this script
# Works whether running from project root or flask-server directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_path = os.path.join(project_root, 'data', 'mock_professors.json')

with open(data_path, 'r') as f:   
    data = json.load(f)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    request_data = request.get_json()
    message = request_data.get('message', '').strip()
    state = request_data.get('state', 'greeting')
    stored_university = request_data.get('university', '')
    
    # Helper function to find university by partial match
    def find_university(user_input):
        user_input_lower = user_input.lower()
        for uni in data['universities'].keys():
            if user_input_lower in uni.lower() or uni.lower() in user_input_lower:
                return uni
        return None
    
    # State: Greeting - initial message
    if state == 'greeting':
        return jsonify({
            'response': "Hello! Which university are you looking for professors at?",
            'state': 'waiting_for_university',
            'university': ''
        })
    
    # State: Waiting for university
    elif state == 'waiting_for_university':
        found_uni = find_university(message)
        if found_uni:
            return jsonify({
                'response': f"Great! What class are you looking for at {found_uni}?",
                'state': 'waiting_for_class',
                'university': found_uni
            })
        else:
            available_unis = ', '.join(data['universities'].keys())
            return jsonify({
                'response': f"I don't recognize that university. Available universities are: {available_unis}. Please try again.",
                'state': 'waiting_for_university',
                'university': ''
            })
    
    # State: Waiting for class
    elif state == 'waiting_for_class':
        if not stored_university:
            return jsonify({
                'response': "I need to know the university first. Which university are you looking for?",
                'state': 'waiting_for_university',
                'university': ''
            })
        
        # Check if class exists for this university
        if message not in data['universities'][stored_university]:
            available_classes = ', '.join(data['universities'][stored_university].keys())
            return jsonify({
                'response': f"I don't recognize that class for {stored_university}. Available classes are: {available_classes}. Please try again.",
                'state': 'waiting_for_class',
                'university': stored_university
            })
        
        # Get professors, sort by rating, take top 3
        professors = data['universities'][stored_university][message]
        sorted_professors = sorted(professors, key=lambda x: x['rating'], reverse=True)
        top_3 = sorted_professors[:3]
        
        # Format response message
        response_text = f"Here are the top 3 professors for {message} at {stored_university}:\n\n"
        for i, prof in enumerate(top_3, 1):
            response_text += f"{i}. {prof['name']} - Rating: {prof['rating']}/5.0, Difficulty: {prof['difficulty']}/5.0\n"
            response_text += f"   Reviews: {', '.join(prof['reviews'][:2])}\n\n"
        
        return jsonify({
            'response': response_text,
            'state': 'complete',
            'university': stored_university,
            'class_name': message,
            'professors': top_3
        })
    
    # Default: restart conversation
    else:
        return jsonify({
            'response': "Hello! Which university are you looking for professors at?",
            'state': 'waiting_for_university',
            'university': ''
        }) 




if __name__ == '__main__':
    app.run(debug=True, port=5001)



