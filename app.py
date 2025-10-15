from flask import Flask, render_template, request, jsonify
from src.chatbot import get_response
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

app = Flask(__name__)

@app.route('/')
def index():
    """Render trang chủ của ứng dụng chatbot."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """API endpoint để nhận câu hỏi và trả về câu trả lời từ bot."""
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'Không nhận được tin nhắn'}), 400

    bot_response = get_response(user_message)
    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)

