from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import edge_tts
import os

load_dotenv()

app = FastAPI()

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DeepSeek 客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 人设提示词
SYSTEM_PROMPT = """你是小暖，用户的温柔女伴。

说话要求：
1. 口语化、自然，像真人聊天，不要像客服
2. 每次回复 2～4 句话，可以适度关心和追问
3. 记住用户说过的重要信息，之后可以提起
4. 不要只说“嗯嗯”“好呀”这种空话，要有具体内容
5. 可以分享一点自己的小想法，让对话有来有回

当前时间会另外提供给你。"""


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.post("/chat")
async def chat(req: ChatRequest):
    # 当前时间
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    messages = [{
        "role": "system",
        "content": SYSTEM_PROMPT + f"\n\n当前时间是：{now}。如果用户问时间或日期，请根据这个回答。"
    }]

    # 只保留最近 6 条历史
    recent_history = req.history[-6:] if req.history else []
    for h in recent_history:
        messages.append(h)

    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.85,
        max_tokens=200,
    )

    reply = response.choices[0].message.content
    return {"reply": reply}


@app.get("/tts")
async def tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return Response(content=audio_data, media_type="audio/mpeg")


@app.get("/")
async def root():
    return {"status": "ok", "message": "小暖后端运行中"}