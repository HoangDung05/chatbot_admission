import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from src.preprocess import preprocess_text

# Load dữ liệu
with open("../data/intents.json", "r", encoding="utf-8") as f:
    intents = json.load(f)

texts = []
labels = []
for intent in intents["intents"]:
    for req in intent["requests"]:
        texts.append(preprocess_text(req))
        labels.append(intent["tag"])

# TF-IDF
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# Train model
clf = LogisticRegression()
clf.fit(X, labels)

# Save model
with open("../models/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)
with open("../models/classifier.pkl", "wb") as f:
    pickle.dump(clf, f)

print("✅ Đã train và lưu model thành công!")
