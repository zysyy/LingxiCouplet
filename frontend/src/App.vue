<template>
  <div class="chat-card">
    <!-- 消息气泡流 -->
    <ChatBubbleList :messages="messages" />
    <!-- 输入栏 -->
    <ChatInput @send="handleUserSend" />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import axios from 'axios'
import ChatBubbleList from './components/ChatBubbleList.vue'
import ChatInput from './components/ChatInput.vue'

interface Message {
  role: 'user' | 'ai'
  text: string
  type: 'up' | 'down' | 'evaluate' | 'explain' | 'system' | 'thinking'
  timestamp: number
  uuid?: string
}

// 可以留空，或者加一条欢迎消息
const messages = ref<Message[]>([
  // { role: 'system', text: '欢迎使用灵犀对句 AI！', type: 'system', timestamp: Date.now() }
])

/**
 * 用户发送上联消息，AI自动生成下联并评分
 */
async function handleUserSend(text: string) {
  // 新增用户消息
  messages.value.push({
    role: 'user',
    text,
    type: 'up',
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

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // === 调用后端 /api/couplet 生成下联 ===
  let down_text = ''
  try {
    const res = await axios.post('/api/couplet', { text })  // 注意这里字段名是 text
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
    // 万一没找到思考气泡，追加
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
          text: `总分：${d.score}\n对仗分：${d.duizhang_score}\n平仄分：${d.pingze_score}\n详情：${d.detail}`,
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
  /* 保证内容上有留白，下方输入栏不挤压 */
}
</style>
