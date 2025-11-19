<template>
  <div class="layout">
    <Sidebar />
    <div class="content">
      <RouterView />
    </div>
  </div>
</template>

<script setup>
import Sidebar from '../components/Sidebar.vue'
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  width: 100%;
}

.content {
  flex: 1;
  transition: margin-left 0.3s ease;
  padding: 5px 0px;
  overflow: hidden;
}
</style>

