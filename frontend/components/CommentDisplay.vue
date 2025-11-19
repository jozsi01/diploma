<template>

    <div class="comment-container" @click="toggleComment" @mouseover="handleMouseOver"
        @mouseleave="store.selectedCommentId = null" :class="{ selected: isSelected, resolved: comment.resolved }" >
        
        <div class="comment-header">
            <strong class="username">{{ comment.made_by }}</strong>
            <div> &#183;</div>
            <span class="comment-date">{{ formatToLocalDateTime(comment.created_at) }}</span>
        </div>
        <div class="comment-content">
            {{ comment.content }}
        </div>
        <div class="resolveButtonContainer">
            <Check class="resolveButton" v-if="showFooter" @click="resolveComment" />
        </div>


    </div>
</template>

<script setup>
import { useStore } from '../store/store';
import { computed, ref } from 'vue';
import { Check } from 'lucide-vue-next';
import customAxios from '../helper/axios';

const showFooter = ref(false);
const store = useStore();
const isSelected = computed(() => {
    return store.selectedCommentId && store.selectedCommentId.id === props.comment.id;
});
function toggleComment() {
    if(props.comment.resolved) {
        return;
    }
    showFooter.value = !showFooter.value;
}
const props = defineProps({
    comment: Object,
    document_id: String,
})
function formatToLocalDateTime(isoString) {
    // Parse the ISO string into a Date object
    const date = new Date(isoString);

    // Convert to local time components
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    // Combine into the desired format
    return `${year}:${month}:${day}:${hours}:${minutes}:${seconds}`;
}

function handleMouseOver() {
    store.selectedCommentId = { id: props.comment.id, from: "display" };
}
async function resolveComment() {
    console.log('Resolving comment with ID:', props.comment.id, 'for document ID:', props.document_id);
    try {
        const response = await customAxios.put('/comments/resolve', { comment_id: props.comment.id, document_id: props.document_id });
        if (response.status === 200) {
            console.log('Comment resolved successfully');
            // Optionally, you can emit an event or update the store to remove the comment from the list
        }
    } catch (error) {
        console.error('Error resolving comment:', error);
    }
    try {
        const response = await customAxios.get('/comments/' + props.document_id);
        if (response.status === 200) {
            store.comments = response.data;
            console.log('Updated comments after resolving:', store.comments);
        }
    } catch (error) {
        console.error('Error fetching updated comments:', error);
    }
}

</script>

<style scoped>

.resolved {
    opacity: 0.6;
}   
.resolveButton:hover {
    cursor: pointer;
    color: green
}

.resolveButtonContainer {
    display: flex;
    justify-content: flex-end;

}

.comment-container {
    border: 1px solid #ccc;
    border-radius: 5px;
    max-width: 200px;
    padding: 5px 10px;
    font-size: 16px;
    margin: 12px 5px;

}

.selected {
    background-color: #f0f0f0;
    cursor: pointer;
    border-color: rgba(255, 255, 0, 0.6);
}

.username {
    font-size: 14px;
}

.comment-content {
    margin-top: 4px;
    font-size: 14px;
    margin: 5px 10px 0px 10px;

}

.comment-header {
    display: flex;
    align-items: center;
    justify-content: space-around;
    margin-bottom: 4px;
}

.comment-date {
    font-size: 12px;
    color: #666;
    margin-left: 5px;
}
</style>