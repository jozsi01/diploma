<template>
<button class="createDocument" @click="showCreateDocumentModal = true;"> Create Document</button>
        <Modal :show="showCreateDocumentModal" @close="showCreateDocumentModal = false">
            <template #header>
                <h3>Create Document</h3>
            </template>
            <template #body>
                <label for="docName">Document name: </label>
                <input v-model="doc_name" required id="docName" type="text">
                <label for="docx_file">Document file: </label>
                <input id="docx_file" type="file">
            </template>
            <template #footer>
                <button style="float: right;" @click="createDocument"> Create
                </button>
            </template>
        </Modal>
</template>


<script setup>
import { ref } from 'vue';
import Modal from './Modal.vue';
import { useStore } from '../store/store';
import customAxios from '../helper/axios';
const store = useStore();


const showCreateDocumentModal = ref(false);
const doc_name = ref('');

async function createDocument() {
    const fileInput = document.getElementById('docx_file');
    const file = fileInput.files[0];
    const formData = new FormData();

    formData.append('document_name', doc_name.value);

    if (file) {
        formData.append('file', file);
    } else {
        console.log("No file selected, sending empty file.");
        const emptyFile = new Blob([], { type: 'text/plain' });
        formData.append('file', emptyFile, `${doc_name.value}.docx`);
    }

    try {
        const { data } = await customAxios.post('/documents', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });

        console.log('Document created:', data);
        store.documents.push(data);
        showCreateDocumentModal.value = false;
        doc_name.value = '';
        fileInput.value = '';
    } catch (error) {
        console.error('Error creating document:', error);
    }
}

</script>



<style scoped >
.createDocument {
    margin-top: 20px;
    padding: 10px 20px;
    background-color: #36a372;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    float: right;
    margin: 5px;
    font-weight: bold;
}

.createDocument:hover {
    background-color: #1e583e;
}
</style>