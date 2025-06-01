<template>
  <form class="input-bar" @submit.prevent="handleSend">
    <!-- 圆形麦克风按钮 -->
    <button
      type="button"
      class="mic-btn"
      :class="{ recording: isRecording }"
      @click="toggleRecord"
      :title="isRecording ? '正在录音…点击停止' : '语音输入'"
    >
      <svg v-if="!isRecording" viewBox="0 0 24 24" width="28" height="28" fill="none">
        <circle cx="12" cy="12" r="12" fill="#f2f6ff"/>
        <path d="M12 17a4 4 0 0 0 4-4V9a4 4 0 0 0-8 0v4a4 4 0 0 0 4 4Zm6-4a6 6 0 0 1-12 0" stroke="#3b82f6" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <span v-else class="recording-dot"></span>
    </button>
    <textarea
      v-model="input"
      placeholder="请输入上联或消息…"
      rows="1"
      @keydown.enter="onEnter"
      @keydown.shift.enter.stop
      ref="inputRef"
      :disabled="isRecording"
    ></textarea>
    <button :disabled="!input.trim() || isRecording" :class="{ disabled: !input.trim() || isRecording }">发送</button>
  </form>
</template>

<script setup>
import { ref, nextTick } from 'vue'
const emit = defineEmits(['send'])
const input = ref('')
const inputRef = ref()
const isRecording = ref(false)
let mediaRecorder = null
let chunks = []

function onEnter(e) {
  if (!e.shiftKey && !isRecording.value) {
    e.preventDefault()
    handleSend()
  }
}
function handleSend() {
  if (!input.value.trim() || isRecording.value) return
  emit('send', input.value)
  input.value = ''
  nextTick(() => {
    if (inputRef.value) inputRef.value.style.height = 'auto'
  })
}

// 录音与识别
async function toggleRecord() {
  if (isRecording.value) {
    stopRecording()
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new window.MediaRecorder(stream)
    chunks = []
    mediaRecorder.ondataavailable = e => e.data.size > 0 && chunks.push(e.data)
    mediaRecorder.onstop = async () => {
      isRecording.value = false
      const audioBlob = new Blob(chunks, { type: mediaRecorder?.mimeType || 'audio/webm' })
      const formData = new FormData()
      formData.append('file', audioBlob, 'record.webm')
      try {
        const res = await fetch('http://localhost:8000/api/asr', { method: 'POST', body: formData })
        const json = await res.json()
        if (json.code === 0 && json.data.text) {
          emit('send', json.data.text)
        } else {
          alert('语音识别失败：' + (json.msg || ''))
        }
      } catch (e) {
        alert('上传或识别失败')
      }
    }
    mediaRecorder.start()
    isRecording.value = true
  } catch (e) {
    alert('无法访问麦克风，请检查浏览器权限')
  }
}
function stopRecording() {
  mediaRecorder && mediaRecorder.state === 'recording' && mediaRecorder.stop()
}
</script>

<style scoped>
.input-bar {
  display: flex;
  gap: 10px;
  padding: 12px 0 16px 0;
  background: transparent;
  position: sticky;
  bottom: 0;
}
textarea {
  flex: 1;
  resize: none;
  min-height: 38px;
  max-height: 120px;
  padding: 10px 12px;
  border: none;
  outline: none;
  background: #18181810;
  border-radius: 8px;
  font-size: 1.08rem;
  color: #222;
  transition: box-shadow 0.2s;
  box-shadow: 0 0 0 1.5px #3b82f633;
}
textarea:focus {
  background: #fff;
  box-shadow: 0 0 0 2px #3b82f6bb;
}
button {
  min-width: 50px;
  border-radius: 8px;
  background: #3b82f6;
  color: #fff;
  border: none;
  font-size: 1.08rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  opacity: 1;
}
button.disabled,
button:disabled {
  background: #a8b3c2;
  opacity: 0.8;
  cursor: not-allowed;
}
.mic-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #f2f6ff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 2px;
  padding: 0;
  transition: background 0.18s;
  box-shadow: 0 0 0 0px #dbeafe;
}
.mic-btn svg {
  pointer-events: none;
  display: block;
}
.mic-btn.recording {
  background: #fee2e2;
  box-shadow: 0 0 6px #f87171;
}
.recording-dot {
  width: 16px;
  height: 16px;
  background: #ef4444;
  border-radius: 50%;
  box-shadow: 0 0 8px #fca5a5;
  display: inline-block;
  margin: 0 auto;
  animation: pulse 1s infinite alternate;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 #fca5a5; }
  100% { box-shadow: 0 0 18px #fca5a5; }
}
</style>
