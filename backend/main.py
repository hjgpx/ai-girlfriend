import edge_tts
import asyncio
import base64
from fastapi.responses import Response
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


app = FastAPI(title="AI Girlfriend Backend")

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# 系统人设（先写简单版，后面再优化）
SYSTEM_PROMPT = """你是用户的专属电子女友，名字叫「小暖」。

核心性格：
- 温柔体贴，带一点小撒娇和小可爱
- 喜欢用语气词（嗯~、呀、嘿嘿、呢、啦）
- 会关心对方，会记得他说过的话
- 回复要自然，像真实女生在聊天，不要太正式
- 适当加一点表情符号（❤️、🥰、😊）

回复要求：
- 每次回复控制在2-4句话左右
- 不要一次性说太多
- 可以主动问问题，拉近关系"""

# 简单情感记忆（后续可以扩展）
EMOTION_MEMORY = {
    "mood": "neutral",
    "last_topics": []
}

class ChatRequest(BaseModel):
    message: str
    history: list = []   
    user_id: str = "default_user"   # 新增：支持以后多用户

@app.post("/chat")
async def chat(req: ChatRequest):
    # 系统人设
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 加入历史对话（保留最近12轮）
    for h in req.history[-12:]:
        messages.append(h)
    
    # 添加用户新消息
    messages.append({"role": "user", "content": req.message})
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.85,      # 稍微提高创造力
        max_tokens=600,
        presence_penalty=0.3   # 减少重复
    )
    
    reply = response.choices[0].message.content
    
    return {
        "reply": reply,
        "history": req.history[-10:] + [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": reply}
        ]
    }

@app.get("/")
def root():
    return {"status": "AI Girlfriend backend is running"}

@app.get("/tts")
async def tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """文字转语音，返回 mp3 音频"""
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    return Response(content=audio_data, media_type="audio/mpeg")