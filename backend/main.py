from fastapi import FastAPI,File, UploadFile,APIRouter
from models import User,CoupletRequest,EvaluateRequest
from datetime import datetime, timezone
from config import VERSION


app = FastAPI()

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

    # 返回文件名和类型等信息
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
    # 用 mock 数据返回，后续再接AI
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "up_text": req.text,
            "down_text": "日暮掩柴扉"  # 你可以写死一条，或者简单拼接
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
