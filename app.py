from flask import Flask, render_template, request, jsonify
from src.chatbot import get_rag_response  # <-- THAY ĐỔI QUAN TRỌNG Ở ĐÂY
import os

# --- Thiết lập Flask App ---
# Chỉ định thư mục templates và static một cách tường minh
# Điều này giúp Flask tìm đúng file HTML, CSS, JS
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')


# --- Các Route (đường dẫn) của ứng dụng ---

@app.route('/')
def index():
    """
    Render trang chủ (giao diện chat) của ứng dụng.
    Flask sẽ tự động tìm file 'index.html' trong thư mục 'templates'.
    """
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """
    API endpoint để nhận câu hỏi từ JavaScript và trả về câu trả lời từ bot.
    """
    # Lấy tin nhắn người dùng gửi lên từ file script.js
    user_message = request.json.get('message')

    # Kiểm tra xem tin nhắn có rỗng không
    if not user_message:
        return jsonify({'error': 'Không nhận được tin nhắn'}), 400

    # Gọi hàm xử lý RAG từ chatbot.py để lấy câu trả lời
    # Đây là nơi chúng ta kết nối với "bộ não" mới
    bot_response = get_rag_response(user_message)

    # Trả về câu trả lời dưới dạng JSON để script.js có thể đọc được
    return jsonify({'response': bot_response})


# --- Chạy ứng dụng ---
if __name__ == '__main__':
    # Chạy Flask app ở chế độ debug để dễ dàng theo dõi lỗi
    # Host='0.0.0.0' cho phép truy cập từ các thiết bị khác trong cùng mạng
    app.run(host='0.0.0.0', port=5000, debug=True)