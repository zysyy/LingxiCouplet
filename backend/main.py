import os
import re
import json
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from models import CoupletRequest, EvaluateRequest
from datetime import datetime, timezone
from config import VERSION
import requests

from dotenv import load_dotenv
from aip import AipSpeech
from pydub import AudioSegment

# ==== 加载 .env ====
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ==== 加载对联知识库 ====
try:
    kb_path = os.path.join(os.path.dirname(__file__), "../data/duilian.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        COUPLET_KB = json.load(f)
except Exception as e:
    print(f"加载对联知识库失败: {e}")
    COUPLET_KB = []

# ==== 基本配置 ====
BAIDU_APP_ID = os.getenv("BAIDU_APP_ID")
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")
aip_client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

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

# ======= 工具函数 =======
def clean_punctuation(text: str) -> str:
    """去除文本结尾标点，去除文字前面注释字样，仅用于对联模式"""
    text = re.sub(r"^(下联|下句)[：:\s]", "", text)
    return re.sub(r'[，。！？、,.!?;；:：~～\s]+$', '', text)

# ==== 本地知识库简单相似度召回 ====
from difflib import SequenceMatcher

def get_top_k_similar(up_text, kb, k=3, min_score=0.3):
    """
    取知识库内和up_text最相似的K条，不足则返回实际数量，没找到返回空列表。
    min_score 控制最小相关度。
    """
    scored = []
    for item in kb:
        up = item.get("上联", "")
        score = SequenceMatcher(None, up_text, up).ratio()
        scored.append((score, item))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [x[1] for x in scored[:k] if x[0] >= min_score]

# ======== 生成下联（含知识库RAG）========
def ask_deepseek(up_text: str) -> str:
    """调用 DeepSeek API 生成下联，结合知识库辅助（RAG）"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    # 检索相关性最高的三条
    kb_examples = get_top_k_similar(up_text, COUPLET_KB, k=3, min_score=0.3)
    example_str = ""
    if kb_examples:
        example_str = "【对联参考】\n"
        for i, ex in enumerate(kb_examples, 1):
            example_str += f"{i}. 上联：{ex['上联']}  下联：{ex['下联']}\n"
        example_str += "（仅供风格和结构参考，不要照搬内容）\n"

    # 拼接 Prompt
    prompt = f"""
你是一位中国古典对联大师，请为下列上联创作一个工整规范的下联，必须严格满足以下要求：

1. **对仗要求**：下联须与上联在词性、结构、语义等方面严格对仗，名词对名词，动词对动词，虚词对虚词，意象需相对。
2. **平仄要求**：遵循传统对联平仄相对规则，平仄交错，不得出律。
3. **内容要求**：意境优美、内容新颖、与上联呼应，避免机械重复和用词生硬。
4. **仅输出下联文本**，不要加任何说明、标点或注释。

{example_str}
上联：{up_text}
下联：
"""
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

# ==== JSON修复（兼容大模型输出） ====
def safe_json_loads(text):
    """
    尝试修复LLM输出的非法JSON，兼容裸回车/多行detail字段。
    """
    try:
        return json.loads(text)
    except Exception:
        # 只处理 detail 字段，把裸换行变成 \n，支持多字段
        def fix_multiline_field(match):
            inner = match.group(1)
            inner_fixed = inner.replace('\r', '').replace('\n', '\\n')
            return f'"detail": "{inner_fixed}"'
        text_fixed = re.sub(
            r'"detail"\s*:\s*"([\s\S]*?)"',  # 捕获可能跨行的 detail 字段
            fix_multiline_field,
            text
        )
        return json.loads(text_fixed)

# ======= 自动评分 =======
def evaluate_deepseek(up_text: str, down_text: str):
    """用大模型对对联评分和分析（兼容内容分 content_score 字段，并自动修正JSON）"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
你是一位中国古典诗词和对联评审专家，请对下面这副对联按照严格标准打分，并给出详细专业点评：

【评分标准】（总分100分）：
1. 对仗分（40分）：主要考察上下联词性、结构、意象等方面是否对仗工整。若有词性不对、结构不对、词义失配等情况要扣分。
2. 平仄分（30分）：评判上下联的平仄格律是否合乎规范。严格遵循对联传统平仄相对要求，如有出律需扣分。
3. 内容分（30分）：考察意境表达、内容创新、诗意美感。内容要有新意和意境，空洞、重复、缺乏文化底蕴需扣分。

【输出要求】
- 必须以**如下JSON格式**输出，不要输出多余的说明或其他内容。
- 点评部分用诗词/对联专业术语，分条表述，逻辑清晰。

【输出格式】
{{
"score": 总分,
"duizhang_score": 对仗分,
"pingze_score": 平仄分,
"content_score": 内容分,
"detail": "详细点评，至少分点（如 1. 2. 3.）写明优缺点及修改建议，用专业术语。"
}}

【评分示例】
上联：春风又绿江南岸
下联：明月何时照我还

输出：
{{
"score": 95,
"duizhang_score": 38,
"pingze_score": 28,
"content_score": 29,
"detail": "1. 对仗基本工整，“春风”对“明月”，“江南岸”对“我还”略显松散。\\n2. 平仄基本合律，仅个别字稍有瑕疵。\\n3. 意境优美，富有诗意，整体为佳作。"
}}

请用以上标准对下列对联打分与点评，只输出JSON：

上联：{up_text}
下联：{down_text}
"""
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
    try:
        match = re.search(r'\{.*\}', answer, re.DOTALL)
        if match:
            eval_result = safe_json_loads(match.group(0))
        else:
            raise ValueError("未找到有效的 JSON 格式评分结果")
        return {
            "score": eval_result.get("score", 0),
            "duizhang_score": eval_result.get("duizhang_score", 0),
            "pingze_score": eval_result.get("pingze_score", 0),
            "content_score": eval_result.get("content_score", None),
            "detail": eval_result.get("detail", "无详细点评")
        }
    except Exception as e:
        return {
            "score": 0,
            "duizhang_score": 0,
            "pingze_score": 0,
            "content_score": None,
            "detail": f"自动解析失败，原始回复：{answer}，错误：{e}"
        }

# ========== FastAPI 路由 ==========

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
        #print(f"explain raw LLM response: {explanation}")

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
