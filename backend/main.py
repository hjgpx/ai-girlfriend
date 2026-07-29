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