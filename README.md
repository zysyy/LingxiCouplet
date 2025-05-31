# 灵犀对句 LingxiCouplet

> 基于 FastAPI + Vue3 + Whisper + DeepSeek API 的 AI 语音诗词对联互动系统  
> An AI-powered interactive voice couplet system using FastAPI, Vue3, Whisper, and DeepSeek API

---

## 项目说明

本项目为个人学习和实践用途，旨在通过实际开发过程熟悉前后端分离架构、现代前端（Vue3）、后端API（FastAPI）、语音识别（Whisper）以及大语言模型API（DeepSeek）的工程集成方法。

项目持续更新中，欢迎交流学习。

---

## 功能
- 支持浏览器录音，语音转文字（ASR）
- 输入上联，自动生成下联
- 上下联自动评分（对仗、平仄、综合）
- 交互流程流畅体验

---

## 快速启动

### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```
### API 说明
```
POST /api/asr 语音识别（上传音频文件，返回文本）

POST /api/couplet 输入上联生成下联

POST /api/evaluate 上下联评分
```

### 环境变量说明
.env 请勿上传，模板见 .env.example

### 目录结构
```
backend/

frontend/

README.md
```
### TODO
 对接真实 AI 能力

 更丰富的评分逻辑

 UI 美化


