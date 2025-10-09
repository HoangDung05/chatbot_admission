from src.chatbot import get_response

print("🤖Xin chào bạn,\nChatbot tư vấn tuyển sinh CNTT (gõ 'exit' để thoát)")
while True:
    user_input = input("Bạn: ")
    if user_input.lower() == "exit":
        print("Chatbot: Tạm biệt, hẹn gặp lại!")
        break
    response = get_response(user_input)
    print("🤖Chatbot:", response)
