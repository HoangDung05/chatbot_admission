import pandas as pd
import json

def excel_to_json(excel_file, json_file):
    # Đọc file Excel
    df = pd.read_excel(excel_file)

    # Điền giá trị tag và responses xuống các dòng NaN (fill down)
    df["tag"] = df["tag"].fillna(method="ffill")
    df["responses"] = df["responses"].fillna(method="ffill")

    intents = []
    # Gom dữ liệu theo từng tag
    for tag, group in df.groupby("tag"):
        requests = group["requests"].dropna().tolist()
        responses = list(set(group["responses"].dropna().tolist()))  # bỏ trùng

        intent = {
            "tag": tag,
            "patterns": requests,
            "responses": responses
        }
        intents.append(intent)

    # Đóng gói thành dict chuẩn
    data = {"intents": intents}

    # Xuất ra file JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Đã tạo file JSON: {json_file}")


if __name__ == "__main__":
    excel_to_json("intents_chatbot.xlsx", "intents.json")
