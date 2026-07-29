const chatBox = document.getElementById('chatBox');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const clearBtn = document.getElementById('clearBtn');

// 聊天历史
let history = JSON.parse(localStorage.getItem('chatHistory') || '[]');

// 持续对话状态
let recognition = null;
let isContinuous = false;
let isSpeaking = false;
let isRecognizing = false;

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

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  addMessage(message, true);
  userInput.value = '';
  sendBtn.disabled = true;

  history.push({ role: 'user', content: message });
  localStorage.setItem('chatHistory', JSON.stringify(history));

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
        history: history.slice(0, -1)
      })
    });

    const data = await res.json();
    const reply = data.reply || '嗯...我有点走神了，再说一次好不好？';

    const loading = document.getElementById('loading');
    if (loading) loading.remove();

    addMessage(reply, false);

    history.push({ role: 'assistant', content: reply });
    localStorage.setItem('chatHistory', JSON.stringify(history));

    await speak(reply);

  } catch (err) {
    console.error(err);
    const loading = document.getElementById('loading');
    if (loading) loading.remove();
    addMessage('哎呀，网络出了点问题，稍后再试好不好？', false);
  }

  sendBtn.disabled = false;
}

// 播放语音（自动去掉括号里的动作描写）
async function speak(text) {
  try {
    isSpeaking = true;

    if (recognition && isRecognizing) {
      try {
        recognition.stop();
      } catch (e) {}
      isRecognizing = false;
    }

    // 去掉（）和()里的内容，避免被读出来
    let speakText = text
      .replace(/（[^）]*）/g, '')
      .replace(/\([^)]*\)/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    if (!speakText) {
      isSpeaking = false;
      if (isContinuous) {
        setTimeout(() => startListening(), 500);
      }
      return;
    }

    const res = await fetch(
      `http://127.0.0.1:8000/tts?text=${encodeURIComponent(speakText)}&voice=zh-CN-XiaoxiaoNeural`
    );
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);

    audio.onended = () => {
      isSpeaking = false;
      if (isContinuous) {
        setTimeout(() => startListening(), 500);
      }
    };

    audio.onerror = () => {
      isSpeaking = false;
      if (isContinuous) {
        setTimeout(() => startListening(), 500);
      }
    };

    await audio.play();
  } catch (err) {
    console.error('语音播放失败', err);
    isSpeaking = false;
    if (isContinuous) {
      setTimeout(() => startListening(), 500);
    }
  }
}

// 回车发送
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// 发送按钮
sendBtn.addEventListener('click', sendMessage);

// 清空历史
if (clearBtn) {
  clearBtn.addEventListener('click', () => {
    if (confirm('确定清空所有聊天记录吗？')) {
      history = [];
      localStorage.removeItem('chatHistory');
      loadHistory();
    }
  });
}

// ========== 持续语音对话 ==========
function startListening() {
  if (!recognition || isSpeaking || isRecognizing) return;

  try {
    recognition.start();
    isRecognizing = true;
    voiceBtn.innerText = '🔴 聆听中...';
    voiceBtn.style.background = '#ef4444';
  } catch (e) {
    console.log('启动识别:', e.message || e);
  }
}

function stopContinuous() {
  isContinuous = false;
  isRecognizing = false;

  if (recognition) {
    try {
      recognition.stop();
    } catch (e) {}
  }

  voiceBtn.innerText = '🎤 说话';
  voiceBtn.style.background = '#ec4899';
}

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    isRecognizing = false;

    if (!text) {
      if (isContinuous && !isSpeaking) {
        setTimeout(() => startListening(), 300);
      }
      return;
    }

    userInput.value = text;
    sendMessage();
  };

  recognition.onerror = (event) => {
    console.error('语音识别错误:', event.error);
    isRecognizing = false;

    if (event.error === 'aborted') return;

    if (isContinuous && !isSpeaking) {
      setTimeout(() => startListening(), 800);
    } else {
      stopContinuous();
    }
  };

  recognition.onend = () => {
    isRecognizing = false;
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

    if (!isContinuous) {
      isContinuous = true;
      startListening();
    } else {
      stopContinuous();
    }
  });
}

// 页面加载时恢复历史
loadHistory();