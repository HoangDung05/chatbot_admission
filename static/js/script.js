// Đợi cho toàn bộ nội dung HTML được tải xong rồi mới chạy mã JS
document.addEventListener('DOMContentLoaded', function() {

    // --- PHẦN 1: LẤY CÁC PHẦN TỬ GIAO DIỆN ---
    // Lấy ra tất cả các phần tử HTML cần thiết để điều khiển popup chat
    const chatIcon = document.getElementById('chat-icon');
    const chatPopup = document.getElementById('chat-popup');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const chatBody = document.getElementById('chat-body');

    // --- PHẦN 2: GẮN CÁC SỰ KIỆN ĐIỀU KHIỂN GIAO DIỆN ---

    // Sự kiện click vào icon để bật/tắt popup chat
    chatIcon.addEventListener('click', () => {
        chatPopup.classList.toggle('hidden');
    });

    // Sự kiện click vào nút X để đóng popup chat
    closeChatBtn.addEventListener('click', () => {
        chatPopup.classList.add('hidden');
    });

    // --- PHẦN 3: XỬ LÝ GỬI TIN NHẮN ---

    // Sự kiện click vào nút gửi
    sendChatBtn.addEventListener('click', handleSendMessage);

    // Sự kiện nhấn phím Enter trong ô input
    chatInput.addEventListener('keydown', (event) => {
        // Nếu phím được nhấn là 'Enter' và không nhấn kèm phím Shift (để xuống dòng)
        if (event.key === 'Enter' && !event.shiftKey) {
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
        appendMessage(userText, 'user-message');
        chatInput.value = ''; // Xóa nội dung trong ô input

        // 2. Hiển thị typing indicator (typing bubbles)
        showTypingIndicator();

        try {
            // 3. Gửi tin nhắn của người dùng đến server backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userText })
            });

            // Nếu server trả về lỗi, ném ra một lỗi để khối catch() xử lý
            if (!response.ok) {
                throw new Error(`Lỗi mạng: ${response.status}`);
            }

            const data = await response.json();
            const botResponse = data.response; // Lấy câu trả lời từ JSON

            // 4. Ẩn typing indicator và hiển thị tin nhắn trả về từ bot
            hideTypingIndicator();
            appendMessage(botResponse, 'bot-message');

        } catch (error) {
            console.error('Đã có lỗi xảy ra khi gọi API:', error);
            // Ẩn typing indicator và hiển thị một tin nhắn lỗi thân thiện trên giao diện
            hideTypingIndicator();
            appendMessage('Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau.', 'bot-message');
        }
    }

    /**
     * Hàm để thêm một tin nhắn mới (của người dùng hoặc bot) vào khung chat.
     * @param {string} text - Nội dung tin nhắn.
     * @param {string} className - Lớp CSS để định dạng ('user-message' hoặc 'bot-message').
     */
    function appendMessage(text, className) {
        const messageElement = document.createElement('div');
        messageElement.className = className;

        const textNode = document.createElement(className === 'bot-message' ? 'div' : 'p');
        if (className === 'bot-message' && window.DOMPurify) {
            textNode.innerHTML = window.DOMPurify.sanitize(String(text), {
                ALLOWED_TAGS: ['p', 'br', 'ul', 'ol', 'li', 'strong', 'em', 'b', 'i'],
                ALLOWED_ATTR: []
            });
        } else {
            // Người dùng là văn bản thuần; thiếu sanitizer thì bot cũng hiển thị an toàn.
            textNode.textContent = String(text);
        }

        messageElement.appendChild(textNode);
        chatBody.appendChild(messageElement);

        // Tự động cuộn xuống tin nhắn mới nhất
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    /**
     * Hàm để hiển thị typing indicator (typing bubbles)
     */
    function showTypingIndicator() {
        // Xóa typing indicator cũ nếu có (để tránh duplicate)
        hideTypingIndicator();
        
        // Tạo typing indicator mới
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing-indicator';
        typingIndicator.className = 'typing-indicator';
        
        const bubblesContainer = document.createElement('div');
        bubblesContainer.className = 'typing-bubbles';
        
        // Tạo 3 bubbles
        for (let i = 0; i < 3; i++) {
            const bubble = document.createElement('div');
            bubble.className = 'typing-bubble';
            bubblesContainer.appendChild(bubble);
        }
        
        typingIndicator.appendChild(bubblesContainer);
        chatBody.appendChild(typingIndicator);
        
        // Tự động cuộn xuống typing indicator
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    /**
     * Hàm để ẩn typing indicator
     */
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            // Xóa hoàn toàn khỏi DOM thay vì chỉ ẩn
            typingIndicator.remove();
        }
    }
});
