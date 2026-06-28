<template>
  <node-view-wrapper class="comment" @mouseover="handleMouseOver" @mouseleave="store.selectedCommentId = null">
    <node-view-content class="comment-content" :class="{ selected: isSelected }" @click="handleClick" />
  </node-view-wrapper>
</template>

<script setup>
import { nodeViewProps, NodeViewWrapper, NodeViewContent } from '@tiptap/vue-3'
import { useStore } from '../store/store.js';
import { computed, watch } from 'vue';
import customAxios from '../helper/axios';
import { useRoute } from 'vue-router';

const props = defineProps(nodeViewProps)
const store = useStore()
const route = useRoute();
function handleClick() {
  // Emit the event to the Tiptap editor instance
  props.editor?.emit('comment-clicked', {
    id: props.node.attrs['comment-id'],
    content: props.node.textContent,
  })
}

watch(() => store.comments, (newComments) => {
  // If the selected comment was resolved and removed, clear the selection
  console.log("Watching comments:", newComments)
  if (newComments.find(c => c.id === props.node.attrs['comment-id']).resolved === true) {
    props.editor.commands.insertContentAt(props.getPos(), props.node.textContent);

    props.deleteNode();
    customAxios.put('/comments/save', {
      document_id: route.params.document_id,
      html_content: props.editor.getHTML(),
    }).then((resp) => {
      console.log("Comment saved successfully!");
    }).catch((error) => {
      console.error("Error saving comment:", error)
    })

  }


});
const isSelected = computed(() => {
  return store.selectedCommentId && store.selectedCommentId.id === props.node.attrs['comment-id'];
});
function handleMouseOver() {
  store.selectedCommentId = { id: props.node.attrs['comment-id'], from: "editor" };
}
</script>

<style scoped>
.comment {
  display: inline;
  cursor: pointer;
  background-color: rgba(255, 255, 0, 0.4);
  border-radius: 4px;
  padding: 0 3px;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}


.selected {
  background-color: rgba(255, 255, 0, 0.6);
  box-shadow: 0 0 0 2px rgba(255, 255, 0, 0.4);
}

.comment-content {
  display: inline;
}
</style>
