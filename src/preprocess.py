import re
from underthesea import word_tokenize

def preprocess_text(text: str) -> str:
    """Làm sạch và tokenize văn bản"""
    text = text.lower().strip()
    text = re.sub(r"[^a-zA-ZÀ-ỹ0-9\s]", "", text)  # bỏ ký tự đặc biệt  
    text = word_tokenize(text, format="text")       # tách từ
    text = " ".join(text.split())
    return text
