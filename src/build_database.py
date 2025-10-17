import json
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

print("Bắt đầu quá trình xây dựng cơ sở dữ liệu vector...")

# --- Phần 1: Thiết lập các Hằng số ---
DATA_FILE_PATH = os.path.join('data', 'intents.json')  # Tên file JSON của bạn
DB_PATH = "db"
COLLECTION_NAME = "ptit_chatbot_rag"
EMBEDDING_MODEL = "bkai-foundation-models/vietnamese-bi-encoder"


def build_database():
    """
    Đọc dữ liệu từ file JSON có cấu trúc từ điển lồng nhau và lưu vào ChromaDB.
    """
    # --- Phần 2: Khởi tạo các thành phần ---
    print(f"Đang tải mô hình embedding: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Thiết lập cơ sở dữ liệu ChromaDB tại: {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)

    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # Xóa collection cũ nếu tồn tại để đảm bảo dữ liệu luôn mới
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        print(f"Collection '{COLLECTION_NAME}' đã tồn tại. Đang xóa để xây dựng lại...")
        client.delete_collection(name=COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )

    # --- Phần 3: Đọc và xử lý dữ liệu ---
    print(f"Đang đọc và xử lý dữ liệu từ: {DATA_FILE_PATH}...")
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    metadatas = []
    ids = []
    id_counter = 1

    # Lặp qua các ngành trong "knowledge_base"
    for major_key, major_data in data['knowledge_base'].items():
        full_name = major_data['full_name']
        print(f"Đang xử lý ngành: {full_name}")

        # Lặp qua các chủ đề kiến thức trong "knowledge" của từng ngành
        for topic_key, topic_content in major_data['knowledge'].items():

            # KIỂM TRA XEM NỘI DUNG LÀ CHUNG HAY RIÊNG THEO CƠ SỞ
            if isinstance(topic_content, str):
                # Trường hợp thông tin chung cho cả 2 cơ sở
                doc_content = f"Chủ đề: {full_name} - {topic_key}. Nội dung: {topic_content}"
                documents.append(doc_content)
                metadatas.append({'major': major_key, 'topic': topic_key})
                ids.append(f"doc_{id_counter}")
                id_counter += 1

            elif isinstance(topic_content, dict):
                # Trường hợp thông tin riêng cho từng cơ sở
                for location_key, location_content in topic_content.items():
                    location_fullname = "Hà Nội" if location_key == "hn" else "TP.HCM"
                    doc_content = f"Chủ đề: {full_name} - {topic_key} (Cơ sở {location_fullname}). Nội dung: {location_content}"
                    documents.append(doc_content)
                    metadatas.append({'major': major_key, 'topic': topic_key, 'location': location_key})
                    ids.append(f"doc_{id_counter}")
                    id_counter += 1

    # --- Phần 4: Nạp dữ liệu vào ChromaDB ---
    print(f"Đang nạp {len(documents)} tài liệu vào collection '{COLLECTION_NAME}'...")
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    print("✅ Hoàn tất! Cơ sở dữ liệu vector đã được xây dựng và lưu thành công.")
    print(f"Tổng số tài liệu được nạp: {collection.count()}")


if __name__ == "__main__":
    build_database()