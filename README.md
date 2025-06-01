# 灵犀对句 LingxiCouplet

> 基于 FastAPI + Vue3 + Whisper + DeepSeek API 的 AI 语音诗词对联互动系统  
> An AI-powered interactive voice couplet system using FastAPI, Vue3, Whisper, and DeepSeek API

---

## 项目说明

本项目为个人学习和实践用途，旨在通过实际开发过程熟悉前后端分离架构、现代前端（Vue3）、后端API（FastAPI）、语音识别（Whisper）以及大语言模型API（DeepSeek）的工程集成方法。

项目持续更新中，欢迎交流学习。

---

## 已实现功能
- 支持语音输入：前端内置麦克风按钮，自动上传录音并转文本（调用百度ASR）

- 文本输入体验升级：多行输入+快捷键，发送更便捷

- AI自动对句：输入上联后，自动生成下联，接口基于 DeepSeek 大模型

- 对联评分：AI 自动评分，结构化展示“总分/对仗分/平仄分+详细点评”

- 气泡流UI：仿GPT流式对话气泡体验，AI思考中动画

- 组件化架构：核心UI分为气泡流、输入栏两大子组件，方便维护拓展

- 消息类型区分：支持 up/down/evaluate/thinking/system 类型，扩展性强

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
---
### API 说明
```
POST /api/asr
上传音频，返回语音识别结果（普通话，百度云）

POST /api/couplet
输入上联，调用 DeepSeek LLM 生成高质量下联

POST /api/evaluate
上下联自动评分，输出总分、对仗分、平仄分及详细分析
```

### 环境变量说明
- .env 请勿上传，模板见下文

- 百度 API、DeepSeek API Key 需自行申请填写

### 目录结构
```
LingxiCouplet/
├── backend/                        # 后端代码（FastAPI）
│   ├── config.py                   # 配置项（如版本/常量等）
│   ├── main.py                     # FastAPI 主入口（含API接口逻辑）
│   ├── models.py                   # Pydantic数据模型定义
│   ├── requirements.txt            # Python依赖包列表
│   └── uploads/                    # 上传音频临时存放目录
│   └── .env                        #未上传，需要自己配置，如何配置看下文
├── data/                           # 项目数据/知识库/爬虫脚本
│   ├── duilian_crawler_and_cleaning.ipynb   # 对联数据爬取与清洗脚本
│   ├── duilian.json                # 已清洗的对联知识库（JSON格式）
│   └── raw.html                    # 爬虫抓取的原始HTML
├── frontend/                       # 前端代码（Vue3）
│   ├── index.html                  # 前端入口HTML
│   ├── package.json                # 前端依赖及配置
│   ├── public/
│   │   └── vite.svg                # 前端静态资源示例
│   ├── src/                        # 源码目录（核心开发区）
│   │   ├── App.vue                 # Vue主组件
│   │   ├── Layout。vue             #界面控制组件
│   │   ├── assets/                 # 资源文件夹（图片等）
│   │   ├── components/             # 自定义组件目录
│   │   │   ├── AudioRecorder.vue   # 录音功能组件
│   │   │   └── CoupletPanel.vue    # 对联主交互面板
│   │   │   └── ChatBubbleList.vue
│   │   │   └── ChatInput.vue
│   │   ├── main.ts                 # 入口TS文件
│   │   ├── style.css               # 全局样式
│   │   └── ...                     # 其他TS/Vue类型声明等
│   ├── tsconfig.json               # TypeScript配置
│   └── vite.config.ts              # Vite工具配置
└── README.md                       # 项目说明文档

```

### 如何配置.env
```
BAIDU_APP_ID=
BAIDU_API_KEY=
BAIDU_SECRET_KEY=
DEEPSEEK_API_KEY=

```
- 变量名与等号之间**不要有空格**，输入的内容也不要带空格，否则可能会报错！
- 若你需要用到其它模型/接口的密钥，也可继续在此文件补充。

---
### TODO
- [x] 语音识别接口（百度 API），支持 wav/webm/mp3 统一转码

- [x] 下联智能生成（DeepSeek 大模型）

- [x] 评分分析（DeepSeek 自动点评）

- [x] “思考中...”流式响应/生成动画体验

- [x] 对话式交互体验、支持连续追问

- [ ] UI/UX 美化，适配 GPT 风格对话框

- [ ] 扩展诗意背景图/配乐/多模态输入等
- [ ] 支持 explain（点评分析）、system（欢迎提示等）更多消息类型
- [ ] 支持上下联历史对话一键导出
- [ ] 对接更丰富模型（如 Whisper 本地端 ASR）
- [ ] UI 主题切换、美化
---

### 联系&致谢
- 本项目仅用于个人学习/展示，感谢 DeepSeek、百度语音 API 提供能力。

- 技术交流联系：
  - qq：1348369823@qq.com

- 欢迎 issue / PR / 交流讨论！

