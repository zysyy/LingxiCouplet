<!-- src/Layout.vue -->
<template>
  <div class="layout-root">
    <!-- 顶部标题栏 -->
    <header>
      <h1>灵犀对句 AI</h1>
      <!-- 可加副标题、logo，后期拓展方便 -->
    </header>
    <!-- 主内容区域（居中） -->
    <main>
      <!-- 这里渲染聊天卡片区域：App.vue -->
      <App />
    </main>
  </div>
</template>

<script setup lang="ts">
import App from './App.vue'; // 引入主聊天组件
</script>

<style scoped>
.layout-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #252525;
}
header {
  text-align: center;
  padding: 32px 0 12px 0;
}
h1 {
  font-size: 2.6rem;     /* 标题大小适中，原来太大 */
  font-weight: 800;
  color: #f5f6fa;
  letter-spacing: 1.5px;
  margin: 0;
  line-height: 1.1;
}
main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;  /* 卡片顶部对齐，不要垂直居中 */
  /* 可加padding-top微调 */
}
</style>
