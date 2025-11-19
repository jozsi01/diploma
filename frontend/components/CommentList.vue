<template>
  <div class="comments-panel" ref="panel">
    <!-- The draggable resize handle -->
    <div class="resize-handle" @mousedown="startResizing"></div>

    <div class="comments-header">
      <h3>Comments</h3>
      <div class="closeSign" @click="$emit('close-comments')">&#10006;</div>
    </div>

    <div class="statusButtonsContainer">
            <button class="statusButtons" :class="{ active: isShowingOpenedComments }" @click="isShowingOpenedComments = true">Opened</button>
            <button class="statusButtons" :class="{ active: !isShowingOpenedComments }" @click="isShowingOpenedComments = false">Resolved</button>
        </div>
    <div class="comment-list" v-if="isAuthorized">
      <CommentDisplay
        v-for="comment in selectedStatusCommments"
        :key="comment.id"
        :comment="comment"
        :document_id="document_id"
      />
    </div>

    <div v-else>
      <p>You are not authorized to view comments for this document.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import CommentDisplay from './CommentDisplay.vue'
import customAxios from '../helper/axios'
import { useStore } from '../store/store.js'
import { storeToRefs } from 'pinia'

const props = defineProps({
  document_id: String,
})

const store = useStore()

const { comments } = storeToRefs(store)
const selectedStatusCommments = computed(() => {
  return comments.value.filter(comment => 
    isShowingOpenedComments.value ? !comment.resolved : comment.resolved
  )
})

const isAuthorized = ref(false)
const panel = ref(null)
const isShowingOpenedComments = ref(true)
let isResizing = false

// Handle resizing logic
function startResizing(e) {
  isResizing = true
  document.addEventListener('mousemove', resize)
  document.addEventListener('mouseup', stopResizing)
}

function resize(e) {
  if (!isResizing || !panel.value) return
  const newWidth = panel.value.getBoundingClientRect().right - e.clientX
  if (newWidth > 200 && newWidth < 600) {
    panel.value.style.width = `${newWidth}px`
  }
}

function stopResizing() {
  isResizing = false
  document.removeEventListener('mousemove', resize)
  document.removeEventListener('mouseup', stopResizing)
}

onMounted(() => {
  fetchComments()
})

async function fetchComments() {
  try {
    const response = await customAxios.get('/comments/' + props.document_id)
    if (response.status === 200) {
      isAuthorized.value = true
      store.comments = response.data
      console.log('Fetched comments:', store.comments )
    } else {
      isAuthorized.value = false
    }
  } catch (error) {
    console.error('Error fetching comments:', error)
  }
}
</script>

<style scoped>
.statusButtonsContainer {
    display: flex;
    justify-content: space-around;
    margin: 8px;
}
.statusButtons {
    padding: 6px 12px;
    font-size: 14px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    border: 1px solid black;
    background-color: transparent;
    color: black;
}
.active {
    background-color: #e0e0e0;
}
.comments-panel {
  width: 300px;
  min-width: 200px;
  max-width: 600px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  border-left: 2px solid #ccc;
  background-color: white;
  overflow: hidden;
}

/* Left edge resize handle */
.resize-handle {
  position: absolute;
  left: -3px;
  top: 0;
  width: 6px;
  height: 100%;
  cursor: ew-resize;
  z-index: 10;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px;
  border-bottom: 1px solid #ccc;
  background: #f8f8f8;
  user-select: none;
}

.comment-list {
  overflow-y: auto;
  flex-grow: 1;
}

.closeSign {
  cursor: pointer;
  font-size: 18px;
  padding: 0 5px;
  transition: color 0.2s ease;
}

.closeSign:hover {
  color: red;
}
</style>
