# src/chatbot.py
import os
import json
import random
import pickle
from src.preprocess import preprocess_text

# Xác định đường dẫn tuyệt đối tới thư mục models
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Load vectorizer + model
with open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "rb") as f:
    vectorizer = pickle.load(f)

with open(os.path.join(MODEL_DIR, "classifier.pkl"), "rb") as f:
    classifier = pickle.load(f)

# Load intents
with open(os.path.join(DATA_DIR, "intents.json"), "r", encoding="utf-8") as f:
    intents = json.load(f)

def get_response(user_input: str) -> str:
    """Trả lời người dùng dựa trên intent dự đoán"""
    X = vectorizer.transform([preprocess_text(user_input)])
    intent = classifier.predict(X)[0]

    for intent_data in intents["intents"]:
        if intent_data["tag"] == intent:
            return random.choice(intent_data["responses"])

    return "Xin lỗi, tôi chưa hiểu câu hỏi của bạn."
