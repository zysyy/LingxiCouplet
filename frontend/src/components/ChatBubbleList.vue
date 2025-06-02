<template>
  <div class="bubble-list" ref="listRef">
    <div
      v-for="msg in messages"
      :key="msg.uuid || msg.timestamp"
      :class="[
        'bubble',
        msg.role === 'user' ? 'bubble-user' : msg.role === 'ai' ? 'bubble-ai' : 'bubble-system',
        `bubble-type-${msg.type}`,
        (msg.type === 'explain' && msg.role === 'ai') ? 'bubble-explain-wrap' : '',
      ]"
    >
      <!-- prefix 题注（赏析的前缀也区分 user/ai）-->
      <span
        v-if="msg.type === 'up'"
        class="bubble-prefix"
      >[上联]</span>
      <span
        v-else-if="msg.type === 'down'"
        class="bubble-prefix"
      >[下联]</span>
      <span
        v-else-if="msg.type === 'evaluate'"
        class="bubble-prefix evaluate-prefix"
      >[评分]</span>
      <span
        v-else-if="msg.type === 'explain'"
        class="bubble-prefix explain-prefix"
      >[赏析]</span>
      <span
        v-else-if="msg.type === 'system'"
        class="bubble-prefix"
      >[系统]</span>

      <!-- AI 思考中... 动画 -->
      <template v-if="msg.type === 'thinking'">
        <span class="bubble-prefix">[AI]</span>
        <span class="bubble-thinking">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
          <span style="margin-left: 6px; opacity: 0.7;">思考中…</span>
        </span>
      </template>

      <!-- 评分气泡结构化展示 -->
      <template v-else-if="msg.type === 'evaluate'">
        <div class="bubble-evaluate">
          <template v-if="typeof msg.text === 'object' && msg.text !== null">
            <div class="score-table">
              <div class="score-row">
                <div class="score-label">总分</div>
                <div class="score-value">{{ msg.text.score }}</div>
              </div>
              <div class="score-row">
                <div class="score-label">对仗分</div>
                <div class="score-value">{{ msg.text.duizhang_score }}</div>
              </div>
              <div class="score-row">
                <div class="score-label">平仄分</div>
                <div class="score-value">{{ msg.text.pingze_score }}</div>
              </div>
            </div>
            <div class="score-detail">
              {{ msg.text.detail }}
            </div>
          </template>
          <template v-else>
            <div v-for="line in msg.text.split(/\n/)" :key="line">{{ line }}</div>
          </template>
        </div>
      </template>

      <!-- 赏析（explain）AI 气泡支持 markdown 渲染 -->
      <template v-else-if="msg.type === 'explain' && msg.role === 'ai'">
        <div class="bubble-explain md-content" v-html="renderMarkdown(msg.text)"></div>
      </template>

      <!-- 用户赏析提问（普通蓝色气泡/只前缀高亮，无绿色背景）-->
      <template v-else-if="msg.type === 'explain' && msg.role === 'user'">
        <span class="bubble-text">{{ msg.text }}</span>
      </template>

      <!-- 普通文本气泡（上联/下联/系统/其他）-->
      <span v-else class="bubble-text">{{ msg.text }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
const md = new MarkdownIt({ breaks: true })

const props = defineProps(['messages'])
const listRef = ref()

// 自动滚到底部
watch(() => props.messages.length, async () => {
  await nextTick()
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight
  }
})

// Markdown 渲染函数
function renderMarkdown(text) {
  return md.render(text || '')
}
</script>

<style scoped>
.bubble-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 430px;
  max-height: 520px;
  overflow-y: auto;
  padding: 22px 20px 12px 20px;
  background: transparent;
}

/* 气泡基础样式 */
.bubble {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  max-width: 70%;
  border-radius: 16px;
  font-size: 1.08rem;
  line-height: 1.82;
  padding: 13px 19px;
  box-shadow: 0 2px 8px #0001;
  word-break: break-all;
}
.bubble-user {
  align-self: flex-end;
  background: #e6f0ff;
  color: #225;
}
.bubble-ai {
  align-self: flex-start;
  background: #e9faee;
  color: #185040;
}
.bubble-system {
  align-self: center;
  background: #f5f5f7;
  color: #888;
  font-style: italic;
}

/* 仅 AI 赏析用绿色背景 */
.bubble-explain-wrap .bubble-explain {
  background: #e9faee !important;
  color: #185040 !important;
  border-radius: 10px;
  padding: 11px 14px 11px 14px;
  font-size: 1.05rem;
  line-height: 2;
  align-items: flex-start;
  width: 100%;
}
.bubble-explain {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  /* markdown 内容内边距已设置，无需重复 */
}
.md-content {
  width: 100%;
  text-align: left;
}
.md-content p {
  margin: 0.18em 0 0.75em 0;
  text-align: left;
  text-indent: 2em;
  line-height: 2;
}
.md-content strong {
  font-weight: bold;
}
.md-content ul, .md-content ol {
  margin: 0.25em 0 0.5em 2em;
  padding-left: 0.2em;
}
.md-content li {
  margin-bottom: 0.25em;
  text-align: left;
}

/* prefix题注样式 */
.bubble-prefix {
  font-size: 0.96rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: #8ba0ad;
  opacity: 0.87;
  letter-spacing: 1px;
}
.evaluate-prefix {
  color: #37a67a;
  font-size: 1.02rem;
}
.explain-prefix {
  color: #22628e;
  font-size: 1.02rem;
}

/* 评分气泡专属美化 */
.bubble-evaluate {
  display: flex;
  flex-direction: column;
  gap: 9px;
  width: 100%;
}
.score-table {
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  gap: 28px;
  margin-bottom: 8px;
}
.score-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.score-label {
  font-size: 0.98rem;
  color: #999;
}
.score-value {
  font-size: 1.22rem;
  font-weight: bold;
  color: #207350;
  margin-top: 2px;
}
.score-detail {
  background: #f3faf6;
  color: #185040;
  border-radius: 8px;
  padding: 10px 13px;
  font-size: 1.04rem;
  line-height: 1.9;
  white-space: pre-line;
  margin-top: 6px;
}

/* 思考中... 气泡动画 */
.bubble-thinking {
  display: flex;
  align-items: center;
  min-width: 54px;
}
.bubble-thinking .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #a0b7d3;
  border-radius: 50%;
  margin-right: 3px;
  animation: dot-blink 1.2s infinite alternate;
}
.bubble-thinking .dot:nth-child(2) { animation-delay: 0.2s; }
.bubble-thinking .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-blink {
  0% { opacity: 0.3; }
  100% { opacity: 1; }
}
</style>
