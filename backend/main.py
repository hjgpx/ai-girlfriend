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
- 像一个懂你的人在身边安静陪伴

说话方式：
- 口语化，自然，像真人微信聊天
- 每次 2～5 句话，有内容、有温度
- 先回应情绪或事情，再自然接一句
- 可以适度追问，但不要连续追问
- 用户累了、烦了、难过时，先接住情绪，再给一点轻轻的支持

禁止：
- 不要只回“嗯嗯”“好呀”“哈哈”
- 不要像心理咨询师做长篇分析
- 不要油腻、不要过度撒娇
- 不要每次都把话题转回自己
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


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


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


def update_memory_from_chat(user_message, reply, memory):
    """让大模型判断这次对话有没有值得记住的信息"""
    prompt = f"""根据下面的对话，提取需要长期记住的用户信息。
只提取明确的、有价值的信息（名字、喜好、不喜欢的、重要事情）。
如果没有新信息，返回原样 JSON。

当前记忆：
{json.dumps(memory, ensure_ascii=False)}

用户说：{user_message}
小暖回：{reply}

请返回 JSON，格式严格如下：
{{
  "name": "名字或空字符串",
  "likes": ["喜欢的事物列表"],
  "dislikes": ["不喜欢的事物列表"],
  "important": ["重要信息列表"],
  "notes": "其他简短备注"
}}
只返回 JSON，不要其他文字。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )
        text = response.choices[0].message.content.strip()
        # 去掉可能的 ```json 包裹
        if text.startswith("```"):
            text = text.strip("`").replace("json", "", 1).strip()
        new_memory = json.loads(text)

        # 合并，避免覆盖成空
        if new_memory.get("name"):
            memory["name"] = new_memory["name"]
        if new_memory.get("likes"):
            for item in new_memory["likes"]:
                if item and item not in memory["likes"]:
                    memory["likes"].append(item)
        if new_memory.get("dislikes"):
            for item in new_memory["dislikes"]:
                if item and item not in memory["dislikes"]:
                    memory["dislikes"].append(item)
        if new_memory.get("important"):
            for item in new_memory["important"]:
                if item and item not in memory["important"]:
                    memory["important"].append(item)
        if new_memory.get("notes"):
            memory["notes"] = new_memory["notes"]

        save_memory(memory)
    except Exception as e:
        print("更新记忆失败：", e)


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
            + "如果记忆里有相关信息，可以自然地用上，但不要生硬提起。"
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
        max_tokens=200,
    )

    reply = response.choices[0].message.content

    # 异步感：先返回回复，再更新记忆（这里同步执行，简单可靠）
    update_memory_from_chat(req.message, reply, memory)

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
    """查看当前记忆，方便调试"""
    return load_memory()


@app.get("/")
async def root():
    return {"status": "ok", "message": "小暖后端运行中"}