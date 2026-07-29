from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
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

# 精简后的人设（短一些，响应更快）
SYSTEM_PROMPT = """你是小暖，用户的温柔女伴。说话口语化、简短自然，每次回复控制在2-4句话，不要长篇大论。语气亲切，像在和喜欢的人聊天。"""


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.post("/chat")
async def chat(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 只保留最近 6 条历史，加快速度
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