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
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  import axios from 'axios'
  import AudioRecorder from './AudioRecorder.vue' // 注意路径和名字
  
  const upText = ref('')     
  const downText = ref('')
  const loading = ref(false)
  
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
  
  // 语音识别的回调
  function onRecognized(text: string) {
    upText.value = text
  }
  </script>
  
  <style scoped>
  .couplet-panel {
    padding: 24px;
  }
  </style>
  