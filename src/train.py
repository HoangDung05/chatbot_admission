import os
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from src.preprocess import preprocess_text

# === Xác định đường dẫn tuyệt đối ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

# === Load dữ liệu ===
with open(os.path.join(DATA_DIR, "intents.json"), "r", encoding="utf-8") as f:
    intents = json.load(f)

texts, labels = [], []
for intent in intents["intents"]:
    for req in intent["patterns"]:  # lưu ý: nên là "patterns" chứ không phải "requests"
        texts.append(preprocess_text(req))
        labels.append(intent["tag"])

# === TF-IDF ===

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# === Train model ===
clf = LogisticRegression(max_iter=200)
clf.fit(X, labels)

# === Save model ===
os.makedirs(MODEL_DIR, exist_ok=True)
with open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "wb") as f:
    pickle.dump(vectorizer, f)
with open(os.path.join(MODEL_DIR, "classifier.pkl"), "wb") as f:
    pickle.dump(clf, f)

print("✅ Đã train và lưu model thành công!")
