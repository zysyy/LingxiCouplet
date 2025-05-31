<template>
    <div>
      <button @click="startRecording" :disabled="isRecording">开始录音</button>
      <button @click="stopRecording" :disabled="!isRecording">停止录音</button>
      <button v-if="audioBlob" @click="uploadAudio">上传音频</button>
      <audio v-if="audioUrl" :src="audioUrl" controls></audio>
      <div v-if="asrResult">识别结果：{{ asrResult }}</div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  const emit = defineEmits(['recognized']) // 加这一行
  
  const isRecording = ref(false)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])
  const audioBlob = ref(null)
  const audioUrl = ref('')
  const asrResult = ref('')
  
  function startRecording() {
    audioChunks.value = []
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      mediaRecorder.value = new window.MediaRecorder(stream)
      mediaRecorder.value.start()
      isRecording.value = true
  
      mediaRecorder.value.ondataavailable = e => {
        audioChunks.value.push(e.data)
      }
      mediaRecorder.value.onstop = () => {
        audioBlob.value = new Blob(audioChunks.value, { type: 'audio/wav' })
        audioUrl.value = URL.createObjectURL(audioBlob.value)
        isRecording.value = false
      }
    })
  }
  
  function stopRecording() {
    if (mediaRecorder.value) {
      mediaRecorder.value.stop()
    }
  }
  
  async function uploadAudio() {
    if (!audioBlob.value) return
    const formData = new FormData()
    formData.append('file', audioBlob.value, 'record.wav')
    try {
      const response = await axios.post('http://localhost:8000/api/asr', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      asrResult.value = response.data.data.text
      emit('recognized', asrResult.value)   // <<<<<< 这里
    } catch (error) {
      asrResult.value = '上传或识别失败'
    }
  }

  </script>
  