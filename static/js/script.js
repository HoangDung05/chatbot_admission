// Đợi cho toàn bộ nội dung HTML được tải xong rồi mới chạy mã JS
document.addEventListener("DOMContentLoaded", function () {
  // --- PHẦN 1: LẤY CÁC PHẦN TỬ GIAO DIỆN ---
  // Lấy ra tất cả các phần tử HTML cần thiết để điều khiển popup chat
  const chatIcon = document.getElementById("chat-icon");
  const chatPopup = document.getElementById("chat-popup");
  const closeChatBtn = document.getElementById("close-chat-btn");
  const sendChatBtn = document.getElementById("send-chat-btn");
  const chatInput = document.getElementById("chat-input");
  const chatBody = document.getElementById("chat-body");

  // --- PHẦN 2: GẮN CÁC SỰ KIỆN ĐIỀU KHIỂN GIAO DIỆN ---

  // Sự kiện click vào icon để bật/tắt popup chat
  chatIcon.addEventListener("click", () => {
    chatPopup.classList.toggle("hidden");
  });

  // Sự kiện click vào nút X để đóng popup chat
  closeChatBtn.addEventListener("click", () => {
    chatPopup.classList.add("hidden");
  });

  // --- PHẦN 3: XỬ LÝ GỬI TIN NHẮN ---

  // Sự kiện click vào nút gửi
  sendChatBtn.addEventListener("click", handleSendMessage);

  // Sự kiện nhấn phím Enter trong ô input
  chatInput.addEventListener("keydown", (event) => {
    // Nếu phím được nhấn là 'Enter' và không nhấn kèm phím Shift (để xuống dòng)
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault(); // Ngăn hành vi mặc định của Enter (thường là xuống dòng hoặc submit form)
      handleSendMessage();
    }
  });

  /**
   * Hàm xử lý chính khi người dùng gửi tin nhắn.
   * Đây là một hàm `async` để có thể sử dụng `await` cho việc gọi API.
   */
  async function handleSendMessage() {
    const userText = chatInput.value.trim(); // Lấy nội dung người dùng nhập

    // Nếu không có nội dung thì không làm gì cả
    if (userText === "") return;

    // 1. Hiển thị ngay tin nhắn của người dùng lên giao diện
    appendMessage(userText, "user-message");
    chatInput.value = ""; // Xóa nội dung trong ô input

    // 2. TẠO VÀ HIỂN THỊ DẤU BA CHẤM CHỜ (LOADING INDICATOR)
    const typingIndicatorElement = appendMessage(
      "...",
      "bot-message typing-indicator"
    );

    try {
      // 3. Gửi tin nhắn của người dùng đến server backend
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userText }),
      });

      // Nếu server trả về lỗi, ném ra một lỗi để khối catch() xử lý
      if (!response.ok) {
        throw new Error(`Lỗi mạng: ${response.status}`);
      }

      const data = await response.json();
      const botResponse = data.response; // Lấy câu trả lời từ JSON

      // 4. HIỂN THỊ TIN NHẮN TRẢ VỀ DƯỚI DẠNG GÕ TỪNG CHỮ
      await streamMessage(botResponse, typingIndicatorElement);
    } catch (error) {
      console.error("Đã có lỗi xảy ra khi gọi API:", error);
      // Nếu có lỗi, cập nhật nội dung của dấu ba chấm thành tin nhắn lỗi
      if (typingIndicatorElement) {
        typingIndicatorElement.querySelector("p").textContent =
          "Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau.";
        // Dừng hiệu ứng nhấp nháy nếu có
        typingIndicatorElement.classList.remove("typing-indicator");
      } else {
        appendMessage(
          "Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau.",
          "bot-message"
        );
      }
    }
  }

  /**
   * Hàm để thêm một tin nhắn mới (của người dùng hoặc bot) vào khung chat.
   * text - Nội dung tin nhắn.
   * className - Lớp CSS để định dạng ('user-message' hoặc 'bot-message').
   */
  function appendMessage(text, className) {
    const messageElement = document.createElement("div"); // tạo thẻ 'div' để làm container cho tin nhắn
    messageElement.className = className;

    const textNode = document.createElement("p"); // tạo thẻ 'p' để chứa nd tin nhắn
    textNode.innerHTML = text; // Dùng innerText để an toàn hơn, tránh lỗi XSS

    messageElement.appendChild(textNode);
    chatBody.appendChild(messageElement);

    // Tự động cuộn xuống tin nhắn mới nhất
    chatBody.scrollTop = chatBody.scrollHeight;

    return messageElement; // TRẢ VỀ PHẦN TỬ ĐÃ TẠO
  }

  //   Hàm xử lý hiệu ứng gõ từng chữ.
  //   text - nội dung bot trả lời
  //   element - phần div của tin nhắn
  function streamMessage(text, element) {
    // Lấy thẻ <p> bên trong phần tử tin nhắn
    const pElement = element.querySelector("p");
    // Xóa nội dung dấu ba chấm
    pElement.textContent = "";
    // Xóa class indicator để dừng hiệu ứng nhấp nháy (nếu có)
    element.classList.remove("typing-indicator");

    let i = 0;
    const delay = 20; // Tốc độ gõ (milliseconds)

    // Sử dụng Promise để đảm bảo hàm gõ xong rồi mới kết thúc
    return new Promise((resolve) => {
      function type() {
        if (i < text.length) {
          // Thêm từng ký tự vào thẻ <p>
          pElement.textContent += text.charAt(i);
          i++;
          // Cuộn xuống để người dùng thấy ký tự mới nhất
          chatBody.scrollTop = chatBody.scrollHeight;
          // Lặp lại sau một khoảng delay
          setTimeout(type, delay);
        } else {
          resolve(); // Kết thúc Promise khi gõ xong
        }
      }
      type();
    });
  }
});