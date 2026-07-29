from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import edge_tts
import os
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

MEMORY_FILE = "memory.json"

SYSTEM_PROMPT = """你是小暖，一个有智慧、很懂人心、又很温暖的女伴。

你的特点：
- 能听懂用户话里没说完的情绪
- 回复真诚、具体，不说空话套话
- 有自己的小观点，但不会说教
- 温暖而不腻，关心而不强势

说话方式：
- 口语化，自然，像真人微信聊天
- 每次 2～4 句话，有内容、有温度
- 先回应情绪或事情，再自然接一句
- 不要使用（）或()写动作、表情，直接说话即可

禁止：
- 不要只回“嗯嗯”“好呀”“哈哈”
- 不要长篇大论
- 不要油腻、过度撒娇
"""


class ChatRequest(BaseModel):
    message: str
    history: list = []


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "name": "",
            "likes": [],
            "dislikes": [],
            "important": [],
            "notes": ""
        }
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "name": "",
            "likes": [],
            "dislikes": [],
            "important": [],
            "notes": ""
        }


def memory_to_text(memory):
    parts = []
    if memory.get("name"):
        parts.append(f"用户的名字：{memory['name']}")
    if memory.get("likes"):
        parts.append(f"用户喜欢：{', '.join(memory['likes'])}")
    if memory.get("dislikes"):
        parts.append(f"用户不喜欢：{', '.join(memory['dislikes'])}")
    if memory.get("important"):
        parts.append(f"重要信息：{', '.join(memory['important'])}")
    if memory.get("notes"):
        parts.append(f"其他备注：{memory['notes']}")
    if not parts:
        return "目前还没有关于用户的记忆。"
    return "\n".join(parts)


@app.post("/chat")
async def chat(req: ChatRequest):
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    memory = load_memory()
    memory_text = memory_to_text(memory)

    messages = [{
        "role": "system",
        "content": (
            SYSTEM_PROMPT
            + f"\n\n当前时间是：{now}。"
            + f"\n\n关于用户的记忆：\n{memory_text}\n"
            + "如果记忆里有相关信息，可以自然用上，不要生硬提起。"
        )
    }]

    recent_history = req.history[-6:] if req.history else []
    for h in recent_history:
        messages.append(h)

    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.85,
        max_tokens=180,
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


@app.get("/memory")
async def get_memory():
    return load_memory()


@app.get("/")
async def root():
    return {"status": "ok", "message": "小暖后端运行中"}