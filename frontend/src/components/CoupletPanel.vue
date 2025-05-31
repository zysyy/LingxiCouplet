<template>
  <div class="couplet-panel">
    <!-- 录音部分 -->
    <AudioRecorder @recognized="onRecognized" />

    <div style="margin-top: 20px;">
      <label>上联：</label>
      <input v-model="upText" placeholder="请输入上联或从语音识别获得" />
    </div>

    <button 
      @click="generateCouplet"
      :disabled="loading || !upText"
      style="margin-top: 10px;"
    >
      <span v-if="loading">生成中...</span>
      <span v-else>生成下联</span>
    </button>

    <div v-if="downText" style="margin-top: 16px;">
      <label>下联：</label>
      <span>{{ downText }}</span>
    </div>

    <button
      @click="evaluateCouplet"
      :disabled="!upText || !downText || evalLoading"
      style="margin-top: 10px;"
    >
      <span v-if="evalLoading">评分中...</span>
      <span v-else>评分</span>
    </button>
    <div v-if="evalResult" class="score-panel">
      <div><b>总分：</b>{{ evalResult.score }}</div>
      <div><b>对仗分：</b>{{ evalResult.duizhang_score }}</div>
      <div><b>平仄分：</b>{{ evalResult.pingze_score }}</div>
      <div><b>详情：</b>{{ evalResult.detail }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import AudioRecorder from './AudioRecorder.vue'

const upText = ref('')
const downText = ref('')
const loading = ref(false)
const evalLoading = ref(false)
const evalResult = ref<any>(null)

async function generateCouplet() {
  if (!upText.value) return
  loading.value = true
  try {
    const res = await axios.post('/api/couplet', { text: upText.value })
    downText.value = res.data.data.down_text
  } catch (e) {
    alert('生成失败')
  }
  loading.value = false
}

async function evaluateCouplet() {
  if (!upText.value || !downText.value) return
  evalLoading.value = true
  try {
    const res = await axios.post('/api/evaluate', {
      up_text: upText.value,
      down_text: downText.value
    })
    evalResult.value = res.data.data
  } catch (e) {
    evalResult.value = { detail: '评分失败' }
  }
  evalLoading.value = false
}

function onRecognized(text: string) {
  upText.value = text
}
</script>

<style scoped>
.couplet-panel {
  padding: 24px;
}
.score-panel {
  background: #f6f8fa;
  border-radius: 8px;
  padding: 12px 18px;
  margin-top: 16px;
  font-size: 1.1em;
  color: #222; /* 新增，确保文字为深色 */
}
</style>
