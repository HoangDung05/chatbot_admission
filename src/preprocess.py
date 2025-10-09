import re
from underthesea import word_tokenize

def preprocess_text(text: str) -> str:
    # Làm sạch và tokenize văn bản
    text = text.lower().strip()
    # bỏ ký tự đặc biệt  
    text = re.sub(r"[^a-zA-ZÀ-ỹ0-9\s]", "", text)
    # tách từ
    text = word_tokenize(text, format="text")
    text = " ".join(text.split())
    return text