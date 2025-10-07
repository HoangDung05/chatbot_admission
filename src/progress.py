import re
from underthesea import word_tokenize

stop_word=set(['và', 'là', 'thì', 'của', 'những'])
def preprocess_text(text: str) -> str:
    """Làm sạch và tokenize văn bản"""
    text = text.lower()
    # bỏ ký tự đặc biệt
    text = re.sub(r"[^a-zA-ZÀ-ỹ\s]", "", text)
    # tách từ
    text = word_tokenize(text, format="text").split()    
    #bỏ stop_word
    text=[w for w in text if w not in stop_word]

    return " ".join(text)
