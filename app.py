# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from src.chatbot import get_rag_response, add_document_to_database, delete_document_from_database
from werkzeug.utils import secure_filename
import os
import sys

# Thiết lập encoding UTF-8 cho Windows terminal
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- Thiết lập Flask App ---
# Chỉ định thư mục templates và static một cách tường minh
# Điều này giúp Flask tìm đúng file HTML, CSS, JS
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Thiết lập secret key cho session
app.secret_key = 'your-secret-key-change-this-in-production'

# Cấu hình upload file
UPLOAD_FOLDER = os.path.join('data', 'topics')
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Giới hạn 16MB

# Thông tin đăng nhập admin (cứng)
ADMIN_EMAIL = 'admin@ptit.edu.vn'
ADMIN_PASSWORD = 'admin123'

def allowed_file(filename):
    """Kiểm tra file có đúng định dạng không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator để yêu cầu đăng nhập"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


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


# --- Admin Routes ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Trang đăng nhập admin"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_email'] = email
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'error')
    
    return render_template('login.html')


@app.route('/admin/logout')
def admin_logout():
    """Đăng xuất admin"""
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    """Trang quản lý admin - upload file txt"""
    if request.method == 'POST':
        # Kiểm tra xem có file được upload không
        if 'file' not in request.files:
            flash('Không có file được chọn!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Nếu người dùng không chọn file
        if file.filename == '':
            flash('Không có file được chọn!', 'error')
            return redirect(request.url)
        
        # Kiểm tra file hợp lệ
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Đảm bảo thư mục upload tồn tại
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Lưu file
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            try:
                # Thêm file vào database
                result = add_document_to_database(filepath, filename)
                if result['success']:
                    flash(f'Đã thêm file "{filename}" vào database thành công! ({result["chunks"]} đoạn văn)', 'success')
                else:
                    flash(f'Lỗi khi thêm file vào database: {result["error"]}', 'error')
            except Exception as e:
                flash(f'Lỗi: {str(e)}', 'error')
        else:
            flash('File không hợp lệ! Chỉ chấp nhận file .txt', 'error')
    
    # Lấy danh sách file đã upload
    uploaded_files = []
    if os.path.exists(UPLOAD_FOLDER):
        uploaded_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.txt')]
    
    return render_template('admin.html', files=uploaded_files)


@app.route('/admin/delete/<filename>', methods=['POST'])
@login_required
def admin_delete_file(filename):
    """Xóa file txt và dữ liệu liên quan trong database"""
    try:
        # Kiểm tra file có tồn tại không
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            flash(f'File "{filename}" không tồn tại!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Xóa dữ liệu từ ChromaDB
        result = delete_document_from_database(filename)
        
        # Xóa file từ hệ thống
        try:
            os.remove(filepath)
            if result['success']:
                flash(f'Đã xóa file "{filename}" và {result["deleted_chunks"]} đoạn văn từ database thành công!', 'success')
            else:
                flash(f'Đã xóa file "{filename}" nhưng có lỗi khi xóa dữ liệu trong database: {result.get("error", "Unknown error")}', 'error')
        except Exception as e:
            flash(f'Lỗi khi xóa file: {str(e)}', 'error')
            
    except Exception as e:
        flash(f'Lỗi: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))


# --- Chạy ứng dụng ---
if __name__ == '__main__':
    # Chạy Flask app ở chế độ debug để dễ dàng theo dõi lỗi
    # Host='0.0.0.0' cho phép truy cập từ các thiết bị khác trong cùng mạng
    app.run(host='0.0.0.0', port=5000, debug=True)