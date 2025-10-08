import re
from underthesea import word_tokenize

def preprocess_text(text: str) -> str:
    """Làm sạch và tokenize văn bản"""
<<<<<<< Updated upstream
    text = text.lower()
    text = re.sub(r"[^a-zA-ZÀ-ỹ0-9\s]", "", text)  # bỏ ký tự đặc biệt
    text = word_tokenize(text, format="text")       # tách từ
    return text
=======
    text = text.lower().strip()
    text = re.sub(r"[^a-zA-ZÀ-ỹ0-9\s]", "", text)  # bỏ ký tự đặc biệt  
    text = word_tokenize(text, format="text")       # tách từ
    text = " ".join(text.split())
    
    return text
>>>>>>> Stashed changes
