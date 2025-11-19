<template>
    <div class="editor-view">
        <div div class="editor-container">
            <TipTap @comment-clicked="handleCommentClicked" :document_id="document_id" />
        </div>
        <div class="comments-container" v-if="showComments">
            <CommentList @close-comments="showComments = false" :document_id="document_id" />
        </div>

    </div>



</template>


<script setup>
import TipTap from '../components/TipTap.vue';
import CommentList from '../components/CommentList.vue';
import { ref } from 'vue';

const showComments = ref(false);
defineProps({
    document_id: String,
})

function handleCommentClicked(comment) {
    showComments.value = true;
    console.log('Comment clicked:', comment);
}


</script>

<style scoped>

.comments-container {
    flex-shrink: 0;
    padding-left: 10px;
}
.comments {
    margin-top: 20px;
    margin-left: 20px;
    
    padding-top: 10px;
}
.editor-container {
    flex: 1;
    padding: 10px;
}
.editor-view {
    display: flex;
}
</style>