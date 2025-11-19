<template>
    <div>
        <div class="document-card">
            <BookText class="document-icon" />
            <div class="document-title">{{ props.title }}</div>
            <p>Created: {{ formatIsoDate(props.createdAt) }}</p>
            <div style="margin-left: 10px;">
                <slot name="share"></slot>
            </div>

            <div class="document-actions" @click.stop.prevent>
                <slot name="action-buttons">
                    <Download @click.stop="downloadDocument" class="document-icon download" />
                    <Trash @click.stop="deleteDocument" class="document-icon delete" />
                    <Share2 class="document-icon share" @click.stop="showShareModal = true" />
                    <ShareDocumentModal v-model="showShareModal" :documentName="props.title"
                        :documentId="props.documentId" />
                </slot>

            </div>



        </div>
    </div>

</template>

<script setup>
import { BookText } from 'lucide-vue-next';
import { Download, Trash, Share2 } from 'lucide-vue-next';
import ShareDocumentModal from './ShareDocumentModal.vue';
import { ref } from 'vue';
import customAxios from '../helper/axios';

const showShareModal = ref(false);

const props = defineProps({
    documentId: String,
    title: String,
    createdAt: String,

});

function formatIsoDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
async function downloadDocument() {
    try {
        const response = await customAxios.get(`/documents/${props.documentId}/docx`, {
            responseType: 'blob', // important for file downloads
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${props.title}.docx`);
        document.body.appendChild(link);
        link.click();
        link.remove();

        console.log('Document downloaded:', props.title);
    } catch (error) {
        console.error('Error downloading document:', error);
    }
}

async function deleteDocument() {
    const confirmDelete = confirm(
        `Are you sure you want to delete the document "${props.title}"? This action cannot be undone.`
    );
    if (!confirmDelete) return;

    try {
        await customAxios.delete(`/documents/${props.documentId}`);
        console.log('Document deleted successfully');
        window.location.reload(); // Refresh the list (simple way)
        // Optionally emit an event instead of reload if using a framework like Vue or React
        // emit('documentDeleted', props.documentId);
    } catch (error) {
        console.error('Error deleting document:', error);
    }
}



</script>

<style scoped>
.document-card {
    display: flex;
    align-items: center;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #2a62aa;
    margin: 8px 5px;
}

.document-icon {
    margin: 10px;
    color: white;
}

.document-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
}

.share:hover {
    cursor: pointer;
    color: rgb(0, 255, 213);
}

.delete:hover {
    cursor: pointer;
    color: red;
    border-radius: 10px;
}

.download:hover {
    cursor: pointer;
    color: rgb(28, 219, 53);
    border-radius: 10px;
}

.document-title {
    font-weight: bold;
    font-size: 18px;

    padding: 10px;
}

.document-card:hover {
    background-color: #1e4e8c;
    cursor: pointer;
}
</style>