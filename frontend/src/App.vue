<template>
  <div class="chat-card">
    <!-- 消息气泡流 -->
    <ChatBubbleList :messages="messages" />
    <!-- 输入栏 + 语音识别按钮 -->
    <ChatInput @send="handleUserSend" @voice="handleVoiceInput" />
  </div>
</template>

<script setup lang="ts">
// 声明全局 window 支持 webkitSpeechRecognition
declare global {
  interface Window {
    webkitSpeechRecognition: any
  }
}

import { ref, nextTick } from 'vue'
import axios from 'axios'
import ChatBubbleList from './components/ChatBubbleList.vue'
import ChatInput from './components/ChatInput.vue'

interface Message {
  role: 'user' | 'ai' | 'system'
  text: string
  type: 'up' | 'down' | 'evaluate' | 'explain' | 'system' | 'thinking'
  timestamp: number
  uuid?: string
}

const messages = ref<Message[]>([])

/**
 * 判断输入内容是否为“赏析/解释”问题
 */
function isExplainQuestion(input: string) {
  const text = input.trim()
  const explainKeywords = [
    '为什么', '为啥', '怎么', '请解释', '赏析', '能否分析', '详细说', '哪里写得好', '哪里写得不好',
    '讲讲','讲一讲', '讲一下','不足', '解释', '请评价', '好在哪', '帮我分析', '优缺点', '点评', '可改进', '?', '？'
  ]
  return explainKeywords.some(k => text.includes(k))
}

/**
 * 判断是否为“换一个下联”类指令
 */
function isRetryCouplet(text: string) {
  const normText = text.replace(/\s/g, '')
  const retryTriggers = [
    '换一个下联',
    '再来一个下联',
    '再来一个',
    '换下联',
    '新的下联',
    '新下联',
    '重新生成下联',
    '再出一个下联',
    '你能再出一个下联吗',
    '你可以给我一片新的下联吗',
    '再给我一个下联',
    '再写一个下联'
  ]
  return retryTriggers.some(key => normText.includes(key))
}

// ============ 核心对话发送逻辑 ============
async function handleUserSend(text: string) {
  // 指令判定提前
  if (isRetryCouplet(text)) {
    await retryCouplet()
    return
  }

  const isExplain = isExplainQuestion(text)

  // 新增用户消息
  messages.value.push({
    role: 'user',
    text,
    type: isExplain ? 'explain' : 'up',
    timestamp: Date.now(),
  })

  // 立即插入AI思考中气泡
  const thinkingMsg: Message = {
    role: 'ai',
    text: '思考中…',
    type: 'thinking',
    timestamp: Date.now() + 1,
    uuid: `thinking-${Date.now()}`
  }
  messages.value.push(thinkingMsg)

  await nextTick()
  scrollToBottom()

  if (isExplain) {
    // ==== 调用 /api/explain ====
    let aiReply = ''
    try {
      const lastUp = [...messages.value].reverse().find(m => m.type === 'up')?.text || ''
      const lastDown = [...messages.value].reverse().find(m => m.type === 'down')?.text || ''
      const res = await axios.post('/api/explain', {
        question: text,
        up_text: lastUp,
        down_text: lastDown
      })
      aiReply = res.data?.data?.explanation || res.data?.data || res.data?.msg || '（无详细赏析回复）'
    } catch (e: any) {
      aiReply = '赏析接口异常'
    }
    // 替换思考气泡为赏析回复
    const idx = messages.value.findIndex(m => m.type === 'thinking')
    if (idx !== -1) {
      messages.value[idx] = {
        role: 'ai',
        text: aiReply,
        type: 'explain',
        timestamp: Date.now()
      }
    } else {
      messages.value.push({
        role: 'ai',
        text: aiReply,
        type: 'explain',
        timestamp: Date.now()
      })
    }
    await nextTick()
    scrollToBottom()
    return // explain 流程结束
  }

  // ====== 下面是普通对联生成+评分流程 ======
  let down_text = ''
  try {
    const res = await axios.post('/api/couplet', { text })
    if (res.data?.code === 0) {
      down_text = res.data.data.down_text
    } else {
      down_text = `生成下联失败：${res.data?.msg || '未知错误'}`
    }
  } catch (e: any) {
    down_text = '下联生成异常'
  }

  // 替换“思考中”气泡为 AI下联
  const idx = messages.value.findIndex(m => m.type === 'thinking')
  if (idx !== -1) {
    messages.value[idx] = {
      role: 'ai',
      text: down_text,
      type: 'down',
      timestamp: Date.now()
    }
  } else {
    messages.value.push({
      role: 'ai',
      text: down_text,
      type: 'down',
      timestamp: Date.now()
    })
  }

  await nextTick()
  scrollToBottom()

  // === 自动追加评分 ===
  if (down_text && !down_text.startsWith('生成下联失败')) {
    try {
      const evalRes = await axios.post('/api/evaluate', {
        up_text: text,
        down_text
      })
      if (evalRes.data?.code === 0) {
        const d = evalRes.data.data
        messages.value.push({
          role: 'ai',
          text: d, // 直接传对象，便于结构化评分
          type: 'evaluate',
          timestamp: Date.now()
        })
      } else {
        messages.value.push({
          role: 'ai',
          text: '评分失败：' + (evalRes.data?.msg || '未知错误'),
          type: 'evaluate',
          timestamp: Date.now()
        })
      }
    } catch (e: any) {
      messages.value.push({
        role: 'ai',
        text: '评分异常',
        type: 'evaluate',
        timestamp: Date.now()
      })
    }
    await nextTick()
    scrollToBottom()
  }
}

// ============ 换一个下联（Retry） ============
async function retryCouplet() {
  // 找到最近的上联
  const lastUp = [...messages.value].reverse().find(m => m.type === 'up')?.text
  if (!lastUp) {
    messages.value.push({
      role: 'system',
      text: '未找到上联，无法重新生成下联。',
      type: 'system',
      timestamp: Date.now()
    })
    return
  }
  // AI思考中气泡
  messages.value.push({
    role: 'ai',
    text: '思考中…',
    type: 'thinking',
    timestamp: Date.now(),
    uuid: `thinking-retry-${Date.now()}`
  })
  await nextTick()
  // 请求新下联
  let down_text = ''
  try {
    const res = await axios.post('/api/couplet', { text: lastUp })
    down_text = res.data?.data?.down_text || '生成下联失败'
  } catch (e) {
    down_text = '下联生成异常'
  }
  // 替换思考气泡为新下联
  const idx = messages.value.findIndex(m => m.type === 'thinking')
  if (idx !== -1) {
    messages.value[idx] = {
      role: 'ai',
      text: down_text,
      type: 'down',
      timestamp: Date.now()
    }
  } else {
    messages.value.push({
      role: 'ai',
      text: down_text,
      type: 'down',
      timestamp: Date.now()
    })
  }
  await nextTick()
  // 自动追加评分
  if (down_text && !down_text.startsWith('生成下联失败')) {
    try {
      const evalRes = await axios.post('/api/evaluate', {
        up_text: lastUp,
        down_text
      })
      if (evalRes.data?.code === 0) {
        const d = evalRes.data.data
        messages.value.push({
          role: 'ai',
          text: d,
          type: 'evaluate',
          timestamp: Date.now()
        })
      }
    } catch (e) {
      messages.value.push({
        role: 'ai',
        text: '评分异常',
        type: 'evaluate',
        timestamp: Date.now()
      })
    }
  }
}

/**
 * 语音输入和文本输入统一处理
 */
function handleVoiceInput(text: string) {
  if (!text) return
  handleUserSend(text)
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
  const listEl = document.querySelector('.bubble-list')
  listEl && listEl.scrollTo({ top: listEl.scrollHeight, behavior: 'smooth' })
}
</script>

<style scoped>
.chat-card {
  width: 640px;
  min-height: 520px;
  margin: 0 auto;
  background: #f7fafd;
  border-radius: 18px;
  box-shadow: 0 4px 28px #0001;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 24px 0 0 0;
}
</style>
