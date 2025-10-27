import os
import glob
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

print("Bắt đầu quá trình xây dựng cơ sở dữ liệu vector từ các file TXT trong thư mục data/topics/...")

# --- Cấu hình ---
DATA_FOLDER = os.path.join('data', 'topics')   #  thư mục chứa nhiều file TXT
DB_PATH = "data"                               # nơi lưu cơ sở dữ liệu vector (chroma.sqlite3)
COLLECTION_NAME = "ptit_chatbot_rag"
EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"


def build_database():
    # --- Khởi tạo mô hình embedding ---
    print(f"Đang tải mô hình embedding: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Thiết lập cơ sở dữ liệu ChromaDB tại: {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # --- Xóa collection cũ nếu tồn tại ---
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        print(f"Collection '{COLLECTION_NAME}' đã tồn tại. Đang xóa để xây dựng lại...")
        client.delete_collection(name=COLLECTION_NAME)

    # --- Tạo collection mới ---
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )

    # --- Đọc toàn bộ file TXT ---
    print(f"Đang đọc dữ liệu từ thư mục: {DATA_FOLDER}...")
    txt_files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    if not txt_files:
        print(" Không tìm thấy file .txt nào trong thư mục topics. Hãy kiểm tra lại!")
        return

    documents, metadatas, ids = [], [], []
    total_chunks = 0

    for file_index, file_path in enumerate(txt_files, start=1):
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()

        # --- Chia nội dung file thành các đoạn nhỏ (chunk) ---
        chunks = [text[i:i+800] for i in range(0, len(text), 800)]  # mỗi 800 ký tự là 1 đoạn

        for i, chunk in enumerate(chunks, start=1):
            documents.append(chunk)
            metadatas.append({'file': file_name, 'segment': f'phần_{i}'})
            ids.append(f'{file_name}_chunk_{i}')
            total_chunks += 1

        print(f"    Đã đọc {len(chunks)} đoạn từ file: {file_name}")

    # --- Nạp dữ liệu vào collection ---
    print(f"\nĐang nạp tổng cộng {total_chunks} đoạn văn từ {len(txt_files)} file TXT vào collection '{COLLECTION_NAME}'...")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    print("\n Hoàn tất! Cơ sở dữ liệu vector đã được xây dựng từ các file TXT.")
    print(f" Tổng số đoạn văn trong collection: {collection.count()}")


if __name__ == "__main__":
    build_database()
