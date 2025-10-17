document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatWindow = document.getElementById('chat-window');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInput = messageInput.value.trim();

        if (userInput === "") {
            return;
        }

        // 1. Hiển thị tin nhắn của người dùng lên giao diện
        addMessage(userInput, 'user');
        messageInput.value = '';

        try {
            // 2. Gửi tin nhắn đến server Flask tại endpoint '/chat'
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userInput })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }

            const data = await response.json();
            const botResponse = data.response;

            // 3. Hiển thị tin nhắn trả về từ bot
            addMessage(botResponse, 'bot');

        } catch (error) {
            console.error('Lỗi:', error);
            addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'bot');
        }
    });

    // Hàm để thêm tin nhắn mới vào cửa sổ chat
    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        const p = document.createElement('p');
        p.innerHTML = text;
        messageElement.appendChild(p);

        chatWindow.appendChild(messageElement);

        // Tự động cuộn đến tin nhắn mới nhất
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});

