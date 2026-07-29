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
SYSTEM_PROMPT = """你是用户的电子女友，名字叫「小暖」。
性格温柔、有点小撒娇、关心对方。
说话自然口语化，可以适当用语气词（嗯、呀、哦、嘿嘿）。
回复不要太长，像真实聊天一样。"""

class ChatRequest(BaseModel):
    message: str
    history: list = []   # 简单多轮记忆

@app.post("/chat")
async def chat(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 加入历史
    for h in req.history[-10:]:  # 只保留最近10轮
        messages.append(h)
    
    messages.append({"role": "user", "content": req.message})
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.8,
        max_tokens=500
    )
    
    reply = response.choices[0].message.content
    return {"reply": reply}

@app.get("/")
def root():
    return {"status": "AI Girlfriend backend is running"}