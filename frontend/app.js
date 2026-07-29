const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const clearBtn = document.getElementById('clearBtn');

// 从本地存储读取历史
let history = JSON.parse(localStorage.getItem('chatHistory') || '[]');

// 页面加载时恢复历史
function loadHistory() {
  const messages = chatBox.querySelectorAll('.message');
  messages.forEach((msg, index) => {
    if (index > 0) msg.remove();
  });

  history.forEach(item => {
    addMessage(item.content, item.role === 'user');
  });
}

function addMessage(text, isUser = false) {
  const div = document.createElement('div');
  div.className = `message ${isUser ? 'user' : 'bot'}`;
  div.innerHTML = `<div class="bubble">${text}</div>`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// 使用后端 edge-tts 播放语音
async function speak(text) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/tts?text=${encodeURIComponent(text)}&voice=zh-CN-XiaoxiaoNeural`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
  } catch (err) {
    console.error('语音播放失败', err);
  }
}

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  addMessage(message, true);
  userInput.value = '';
  sendBtn.disabled = true;

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
    document.getElementById('loading')?.remove();
    addMessage(data.reply);

    // 播放语音
    speak(data.reply);

    // 更新历史
    history.push({ role: 'user', content: message });
    history.push({ role: 'assistant', content: data.reply });

    if (history.length > 20) {
      history = history.slice(-20);
    }
    localStorage.setItem('chatHistory', JSON.stringify(history));

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

// 清空聊天
if (clearBtn) {
  clearBtn.addEventListener('click', () => {
    if (confirm('确定要清空和小暖的聊天记录吗？')) {
      history = [];
      localStorage.removeItem('chatHistory');
      location.reload();
    }
  });
}

// 页面加载时恢复历史
loadHistory();

// ========== 语音识别部分 ==========
let recognition = null;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    userInput.value = text;
    voiceBtn.innerText = '🎤 说话';
    voiceBtn.style.background = '#ec4899';
    sendMessage();
  };

  recognition.onerror = (event) => {
    console.error('语音识别错误:', event.error);
    voiceBtn.innerText = '🎤 说话';
    voiceBtn.style.background = '#ec4899';
    alert('语音识别失败，请重试或检查麦克风权限');
  };

  recognition.onend = () => {
    voiceBtn.innerText = '🎤 说话';
    voiceBtn.style.background = '#ec4899';
  };
} else {
  if (voiceBtn) {
    voiceBtn.disabled = true;
    voiceBtn.innerText = '不支持语音';
  }
}

if (voiceBtn) {
  voiceBtn.addEventListener('click', () => {
    if (!recognition) return;

    if (voiceBtn.innerText.includes('说话')) {
      recognition.start();
      voiceBtn.innerText = '🔴 聆听中...';
      voiceBtn.style.background = '#ef4444';
    } else {
      recognition.stop();
    }
  });
}