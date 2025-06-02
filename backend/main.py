from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from models import CoupletRequest, EvaluateRequest
from datetime import datetime, timezone
from config import VERSION
import os
import re
import requests
import json

from dotenv import load_dotenv
from aip import AipSpeech
from pydub import AudioSegment

# 加载 .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 百度AIP配置
BAIDU_APP_ID = os.getenv("BAIDU_APP_ID")
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")
aip_client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

# DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_punctuation(text: str) -> str:
    """去除文本结尾标点，去除文字前面注释字样，仅用于对联模式"""
    text = re.sub(r"^(下联|下句)[：:\s]", "", text)
    return re.sub(r'[，。！？、,.!?;；:：~～\s]+$', '', text)

def ask_deepseek(up_text: str) -> str:
    """调用 DeepSeek API 生成下联"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"请为这个上联对出一个下联，要求符合对仗和平仄规范，只输出下联文本：\n上联：{up_text}\n下联："
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.8
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    down_text = data["choices"][0]["message"]["content"].strip()
    return clean_punctuation(down_text)

def evaluate_deepseek(up_text: str, down_text: str):
    """用大模型对对联评分和分析"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = (
        f"请对下面这副对联进行评分和详细分析。\n"
        f"上联：{up_text}\n"
        f"下联：{down_text}\n"
        "请从总分（100分制）、对仗分、平仄分分别给出具体分数，并用简要语言分析理由。"
        "请以如下 JSON 格式返回："
        '{"score":xx,"duizhang_score":xx,"pingze_score":xx,"detail":"你的详细点评"}'
    )
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.7
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    answer = result["choices"][0]["message"]["content"]
    # 尝试解析大模型的JSON
    try:
        match = re.search(r'\{.*\}', answer, re.DOTALL)
        if match:
            eval_result = json.loads(match.group(0))
        else:
            raise ValueError("未找到有效的 JSON 格式评分结果")
        # 检查字段
        return {
            "score": eval_result.get("score", 0),
            "duizhang_score": eval_result.get("duizhang_score", 0),
            "pingze_score": eval_result.get("pingze_score", 0),
            "detail": eval_result.get("detail", "无详细点评")
        }
    except Exception as e:
        # fallback: 用原文返回
        return {
            "score": 0,
            "duizhang_score": 0,
            "pingze_score": 0,
            "detail": f"自动解析失败，原始回复：{answer}，错误：{e}"
        }

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/asr")
async def upload_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        return {"code": 1, "msg": "请上传音频文件"}

    save_dir = "uploads"
    os.makedirs(save_dir, exist_ok=True)
    raw_path = os.path.join(save_dir, file.filename)
    content = await file.read()
    with open(raw_path, "wb") as f:
        f.write(content)

    wav_path = os.path.splitext(raw_path)[0] + "_16k.wav"
    try:
        audio = AudioSegment.from_file(raw_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")
    except Exception as e:
        return {"code": 2, "msg": f"转码失败: {e}", "data": {}}

    try:
        with open(wav_path, "rb") as f:
            wav_data = f.read()
        result = aip_client.asr(wav_data, "wav", 16000, {'dev_pid': 1537})
        if result.get("err_no") == 0:
            text = result["result"][0]
            text = clean_punctuation(text)
            msg = "ok"
            code = 0
        else:
            text = ""
            msg = f"识别失败: {result.get('err_msg')}"
            code = 3
    except Exception as e:
        text = ""
        msg = f"语音识别接口异常: {e}"
        code = 4

    return {
        "code": code,
        "msg": msg,
        "data": {
            "filename": file.filename,
            "content_type": file.content_type,
            "save_path": wav_path,
            "text": text
        }
    }

@app.post("/api/couplet")
def generate_couplet(req: CoupletRequest):
    try:
        down_text = ask_deepseek(req.text)
    except Exception as e:
        return {
            "code": 1,
            "msg": f"生成失败: {e}",
            "data": {"up_text": req.text, "down_text": ""}
        }
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "up_text": req.text,
            "down_text": down_text
        }
    }

@app.post("/api/evaluate")
def evaluate_couplet(req: EvaluateRequest):
    try:
        eval_result = evaluate_deepseek(req.up_text, req.down_text)
        return {
            "code": 0,
            "msg": "ok",
            "data": eval_result
        }
    except Exception as e:
        return {
            "code": 1,
            "msg": f"自动评分失败: {str(e)}",
            "data": {}
        }

# ===== explain 路由（赏析/解释） =====
@app.post("/api/explain")
def explain(
    question: str = Body(..., embed=True),
    up_text: str = Body("", embed=True),
    down_text: str = Body("", embed=True)
):
    """
    用大模型/DeepSeek对上下联进行‘对话式赏析’回复
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    # 构造 prompt，建议大模型生成时用序号、换行分段回答
    prompt = (
        "你是一位对中国诗词对联非常懂行的AI助手。"
        "现在用户希望你基于以下上下联和提出的问题进行赏析或详细讲解。"
        f"\n上联：{up_text}\n下联：{down_text}\n用户问题：{question}\n"
        "请用自然、详细、有逻辑、有见地的语言来回答用户。请将不同要点尽量用1. 2. 3.等序号分段（或多用换行），便于用户分段阅读。内容不限字数，不要输出多余格式，直接进入点评。"
    )
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.75
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        explanation = data["choices"][0]["message"]["content"].strip()
        return {
            "code": 0,
            "msg": "ok",
            "data": {
                "explanation": explanation
            }
        }
    except Exception as e:
        return {
            "code": 1,
            "msg": f"赏析生成失败: {str(e)}",
            "data": {}
        }
