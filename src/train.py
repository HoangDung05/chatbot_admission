import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from preprocess import preprocess_text


# Đọc dữ liệu intents.json
def load_data(file_path="../data/intents.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    X, y = [], []
    for intent in data["intents"]:
        for req in intent["requests"]:
            X.append(preprocess_text(req))
            y.append(intent["tag"])
    return X, y


# Hàm test accuracy với train/test split
def test_accuracy():
    X, y = load_data()
    vectorizer = TfidfVectorizer()
    X_vec = vectorizer.fit_transform(X)

    # Chia train/test 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    # Dự đoán trên tập test
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"Độ chính xác (accuracy): {acc:.2f}")


# Hàm train full dataset và lưu model
def train_full():
    X, y = load_data()
    vectorizer = TfidfVectorizer()
    X_vec = vectorizer.fit_transform(X)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_vec, y)

    # Tạo thư mục models nếu chưa có
    os.makedirs("../models", exist_ok=True)

    # Lưu vectorizer
    with open("../models/vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    # Lưu model
    with open("../models/classifier.pkl", "wb") as f:
        pickle.dump(model, f)

    print("✅ Đã train full dữ liệu và lưu model thành công.")


if __name__ == "__main__":
    # Bạn có thể chọn chạy test_accuracy hoặc train_full
    test_accuracy()
    # train_full()
