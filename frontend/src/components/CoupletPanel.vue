<template>
    <div class="couplet-panel">
      <!-- 录音部分 -->
      <AudioRecorder @recognized="onRecognized" />
  
      <div style="margin-top: 20px;">
        <label>上联：</label>
        <input v-model="upText" placeholder="请输入上联或从语音识别获得" />
      </div>
  
      <button @click="generateCouplet" :disabled="loading || !upText" style="margin-top: 10px;">
        {{ loading ? '生成中...' : '生成下联' }}
      </button>
  
      <div v-if="downText" style="margin-top: 16px;">
        <label>下联：</label>
        <span>{{ downText }}</span>
      </div>
  
      <button
        @click="evaluateCouplet"
        :disabled="!upText || !downText"
        style="margin-top: 10px;"
      >
        评分
      </button>
      <div v-if="evalResult" style="margin-top: 16px;">
        <div>总分：{{ evalResult.score }}</div>
        <div>对仗分：{{ evalResult.duizhang_score }}</div>
        <div>平仄分：{{ evalResult.pingze_score }}</div>
        <div>详情：{{ evalResult.detail }}</div>
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
    try {
      const res = await axios.post('/api/evaluate', {
        up_text: upText.value,
        down_text: downText.value
      })
      evalResult.value = res.data.data
    } catch (e) {
      evalResult.value = { detail: '评分失败' }
    }
  }
  
  function onRecognized(text: string) {
    upText.value = text
  }
  </script>
  
  <style scoped>
  .couplet-panel {
    padding: 24px;
  }
  </style>
  