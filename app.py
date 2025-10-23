from flask import Flask, render_template, request, jsonify
from src.chatbot import get_rag_response
import os

# --- Thiết lập Flask App ---
# Chỉ định thư mục templates và static một cách tường minh
app = Flask(__name__, static_folder='static', template_folder='templates')

# --- Các đường dẫn của Web---
@app.route('/')
def index():
    return render_template('index.html')

# Decorator này xử lý các yêu cầu POST gửi đến URL '/chat'
@app.route('/chat', methods=['POST'])
def chat():
    # Lấy tin nhắn người dùng gửi lên từ file script.js
    user_message = request.json.get('message')

    # Kiểm tra xem tin nhắn có rỗng không
    if not user_message:
        return jsonify({'error': 'Không nhận được tin nhắn'}), 400

    # Gọi hàm xử lý RAG từ chatbot.py để lấy câu trả lời
    bot_response = get_rag_response(user_message)

    # Trả về câu trả lời dưới dạng JSON để script.js có thể đọc được
    return jsonify({'response': bot_response})


# --- Chạy ứng dụng ---
if __name__ == '__main__':
    # Host='0.0.0.0' cho phép truy cập từ các thiết bị khác trong cùng mạng
    app.run(host='0.0.0.0', port=5000, debug=True)