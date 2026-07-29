# AI Girlfriend（电子女友）

一个使用 DeepSeek 大模型开发的智能电子女友项目。

## 功能
- 温柔会撒娇的 AI 女友「小暖」
- 支持多轮对话记忆
- FastAPI 后端 + 简单前端

## 如何运行

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000