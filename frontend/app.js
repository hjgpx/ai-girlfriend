const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// 简单的历史记录（只保留最近几轮）
let history = [];

function addMessage(text, isUser = false) {
  const div = document.createElement('div');
  div.className = `message ${isUser ? 'user' : 'bot'}`;
  div.innerHTML = `<div class="bubble">${text}</div>`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // 显示用户消息
  addMessage(message, true);
  userInput.value = '';
  sendBtn.disabled = true;

  // 显示“正在输入”
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'message bot';
  loadingDiv.id = 'loading';
  loadingDiv.innerHTML = `<div class="bubble">小暖正在想怎么回你...</div>`;
  chatBox.appendChild(loadingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const res = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        history: history
      })
    });

    const data = await res.json();
    
    // 移除加载提示
    document.getElementById('loading')?.remove();

    // 显示回复
    addMessage(data.reply);

    // 更新历史
    history.push({ role: 'user', content: message });
    history.push({ role: 'assistant', content: data.reply });

    // 只保留最近 10 轮
    if (history.length > 20) {
      history = history.slice(-20);
    }

  } catch (err) {
    document.getElementById('loading')?.remove();
    addMessage('哎呀，网络出了点问题，稍后再试好不好？');
    console.error(err);
  }

  sendBtn.disabled = false;
  userInput.focus();
}

// 事件绑定
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});