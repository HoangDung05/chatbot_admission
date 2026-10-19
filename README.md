# Chatbot tư vấn tuyển sinh PTIT

Ứng dụng Flask trả lời câu hỏi tuyển sinh từ các tài liệu `.txt` trong `data/topics/`. Ứng dụng tìm đoạn liên quan bằng mô hình embedding tiếng Việt và ChromaDB, sau đó gửi ngữ cảnh tới Gemini để tạo câu trả lời.

## Yêu cầu

- Python 3.12 (phiên bản đã kiểm tra) và kết nối Internet khi cài thư viện, tải mô hình embedding lần đầu và gọi Gemini API.
- Gemini API key có quyền dùng mô hình đã cấu hình. Có thể tạo khóa trong [Google AI Studio](https://aistudio.google.com/apikey).

## Chạy trên Windows bằng PowerShell

Mở PowerShell trong thư mục chứa `app.py`, rồi chạy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
notepad .env.local
```

Trong `.env.local`, điền `GEMINI_API_KEY`, `ADMIN_EMAIL`, `FLASK_SECRET_KEY` và `ADMIN_PASSWORD_HASH` của riêng bạn. Không dùng lại tài khoản quản trị hoặc khóa phiên từng có trong Git; không commit file này. Tạo một khóa phiên và hash mật khẩu mới bằng các lệnh sau, rồi sao chép kết quả vào `.env.local`:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python.exe -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('New admin password: ')))"
```

`APP_ENV=development` mặc định cho phép cookie trên HTTP localhost; chế độ này vẫn tắt debug và chỉ lắng nghe `127.0.0.1`. Chỉ bật debug cục bộ khi cần bằng `FLASK_DEBUG=1`. Khi triển khai sau này, đặt `APP_ENV=production` để bật cookie `Secure`, dùng HTTPS và máy chủ WSGI phù hợp. `GEMINI_MODEL` có thể đổi sang mô hình mà dự án Gemini của bạn hỗ trợ.

Ở lần chạy đầu trên bản sao mới, tạo cơ sở dữ liệu vector từ các file trong `data/topics/`:

```powershell
.\.venv\Scripts\python.exe src\build_database.py
```

Lệnh này **xóa collection cũ và xây dựng lại** từ các file `.txt`, vì vậy chỉ chạy khi cần tạo mới hoặc cập nhật toàn bộ dữ liệu. Nếu máy bạn đã có `data/chroma.sqlite3` với collection `ptit_chatbot_rag`, có thể bỏ qua bước này.

Khởi động ứng dụng:

```powershell
.\.venv\Scripts\python.exe app.py
```

Mở <http://127.0.0.1:5000> để chat. Trang quản lý tài liệu ở <http://127.0.0.1:5000/admin/login>. Nhấn `Ctrl+C` trong terminal để dừng server.

## Cấu trúc chính

| Đường dẫn | Công dụng |
| --- | --- |
| `app.py` | Web server Flask và các route chat, quản lý tài liệu |
| `src/chatbot.py` | Tìm kiếm ChromaDB và gọi Gemini API |
| `src/build_database.py` | Xây dựng lại ChromaDB từ tài liệu nguồn |
| `data/topics/` | Tài liệu tuyển sinh dạng `.txt` |
| `templates/`, `static/` | Giao diện web |

## Khi gặp lỗi

- Thiếu cấu hình bảo mật hoặc `GEMINI_API_KEY`: kiểm tra `.env.local` nằm cạnh `app.py` và tất cả giá trị bắt buộc đã được điền.
- Gemini báo `404` hoặc không có quyền truy cập mô hình: đổi `GEMINI_MODEL` trong `.env.local` sang mô hình mà dự án của bạn được phép sử dụng, rồi khởi động lại server.
- Không tìm thấy collection ChromaDB: chạy `src/build_database.py` như hướng dẫn ở trên.
- Console trình duyệt báo `Unchecked runtime.lastError`: thường là lỗi nhắn tin của tiện ích Chrome. Kiểm tra yêu cầu `/chat` trong tab Network và thử tắt tiện ích liên quan; lỗi của ứng dụng sẽ xuất hiện trong terminal chạy Flask.

Không đưa server phát triển Flask lên Internet. Trang quản trị dùng CSRF token và cần đăng nhập bằng cấu hình riêng trong `.env.local`.
