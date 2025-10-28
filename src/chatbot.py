import os
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
import re

# --- Khởi tạo & Tải các mô hình ---
load_dotenv()

# --- Các hằng số ---
DB_PATH = "data"
COLLECTION_NAME = "ptit_chatbot_rag"
EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

print("Đang khởi tạo bộ não của Chatbot...")

# Cấu hình Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Tải mô hình embedding (chỉ một lần)
print(f"Đang tải mô hình embedding: {EMBEDDING_MODEL}...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# Khởi tạo ChromaDB client (chỉ một lần)
print(f"Đang kết nối tới cơ sở dữ liệu vector tại: {DB_PATH}...")
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection(name=COLLECTION_NAME)

print("✅ Chatbot đã sẵn sàng!")

# --- Bộ nhớ hội thoại (conversation memory) ---
conversation_history = []  # Lưu danh sách [{role, content}, ...]

# --- Hàm xử lý chính của Chatbot ---
def get_rag_response(question: str) -> str:
    """
    Hàm chính thực hiện chu trình RAG để trả lời câu hỏi.
    """
    print(f"\nĐang tìm kiếm thông tin cho câu hỏi: '{question}'")

    # Tạo vector cho câu hỏi và truy vấn ChromaDB để lấy ngữ cảnh
    results = collection.query(
        query_texts=[question],
        n_results=3
    )

    context_documents = results['documents'][0]
    if not context_documents:
        print("Không tìm thấy thông tin liên quan trong cơ sở dữ liệu.")
        return "Xin lỗi, tôi không có thông tin về vấn đề này. Bạn có thể hỏi câu khác không?"

    context = "\n\n".join(context_documents)
    print(f"Ngữ cảnh tìm được:\n---\n{context}\n---")

    # Gộp hội thoại trước vào prompt
    conversation_text = ""
    for turn in conversation_history[-3:]:  # chỉ lấy 3 lượt gần nhất
        conversation_text += f"{turn['role'].capitalize()}: {turn['content']}\n"

    # Thiết kế Prompt cho Gemini
    prompt_template = f"""
    Bạn là một trợ lý ảo tư vấn tuyển sinh chuyên nghiệp và thân thiện của Học viện Công nghệ Bưu chính Viễn thông (PTIT).

    **QUY TẮC BẮT BUỘC:**
    1. Dựa **CHÍNH XÁC** và **DUY NHẤT** vào phần [NGỮ CẢNH] để trả lời câu hỏi.
    2. Không được bịa đặt, suy diễn hay thêm thông tin ngoài [NGỮ CẢNH].
    3. Người dùng có thể **hỏi tiếp về cùng chủ đề** ở câu trước, hãy **dựa vào lịch sử hội thoại** để hiểu câu hỏi của người dùng.
    4. Trả lời tự nhiên, lịch sự bằng tiếng Việt.
    5. Câu trả lời cuối cùng của bạn **PHẢI** được định dạng bằng HTML.
    6. Nếu [NGỮ CẢNH] có dạng liệt kê hãy chuyển chúng thành danh sách HTML hãy dùng thẻ <ul> và <li>.
    7. Nếu không đủ thông tin, trả lời: "Xin lỗi, tôi không có thông tin chi tiết về vấn đề này."

    **[HỘI THOẠI TRƯỚC]**
    {conversation_text}

    **[NGỮ CẢNH]**
    {context}

    **[CÂU HỎI MỚI CỦA NGƯỜI DÙNG]**
    {question}

    **[CÂU TRẢ LỜI CỦA BẠN]**
    """

    # --- Gọi Gemini API để sinh câu trả lời ---
    print("Đang gửi yêu cầu đến Gemini để tạo câu trả lời...")
    try:
        response = gemini_model.generate_content(prompt_template)
        print("Đã nhận phản hồi từ Gemini.")
        # 1. Lấy văn bản thô từ Gemini
        raw_text = response.text.strip()
        # 2. Dọn dẹp các dấu ```html và ``` ở đầu và cuối chuỗi
        cleaned_text = re.sub(r"^```html\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text[7:]   # Bỏ 7 ký tự '```html'
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]  ## Bỏ 3 ký tự '```'
        
        # 3. Trả về văn bản đã được làm sạch
        cleaned_text.strip()

        # Lưu câu hỏi và câu trả lời vào bộ nhớ hội thoại
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": cleaned_text})

        # Trả kết quả
        return cleaned_text
    
    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        return "Xin lỗi, đã có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau."

# --- Dành cho việc test nhanh ---
if __name__ == '__main__':
    while True:
        user_question = input("\nBạn hỏi: ")
        if user_question.lower() in ['exit', 'quit']:
            break
        bot_answer = get_rag_response(user_question)
        print(f"Chatbot: {bot_answer}")