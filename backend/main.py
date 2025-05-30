from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware  # 加入 CORS 支持
from models import CoupletRequest, EvaluateRequest
from datetime import datetime, timezone
from config import VERSION

app = FastAPI()

# 关键：添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 本地开发用 *，上线建议写前端实际域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
def read_root():
    return {"Hello": "World"}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/asr")
async def upload_audio(file: UploadFile = File(...)):
    # 检查文件类型
    if not file.content_type.startswith("audio/"):
        return {"code": 1, "msg": "请上传音频文件"}

    # 保存文件到本地（可选）
    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 返回文件名和类型等信息+模拟识别结果
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "filename": file.filename,
            "content_type": file.content_type,
            "save_path": save_path,
            "text": "山中相送罢"
        }
    }

@app.post("/api/couplet")
def generate_couplet(req: CoupletRequest):
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "up_text": req.text,
            "down_text": "日暮掩柴扉"
        }
    }

@app.post("/api/evaluate")
def evaluate_couplet(req: EvaluateRequest):
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "score": 95,
            "duizhang_score": 90,
            "pingze_score": 80,
            "detail": "模拟评分：对仗工整，平仄合格。"
        }
    }
