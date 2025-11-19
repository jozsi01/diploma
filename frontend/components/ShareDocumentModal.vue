<template>
    <Modal :show="showModal" @close="showModal = false">
        <template #header>Share Document {{ documentName }}</template>
        <template #body>
            <div class="relative mt-2 w-full">
                <select  class="appearance-none w-full px-4 py-2 pr-8 border border-gray-300 rounded-lg text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"  name="users" id="cars" v-model="selectedUser">
                    <option v-for="user in users" :key="user.id" :value="user">{{ user.username }}</option>
                </select>
            </div>


        </template>
        <template #footer>
            <button @click="shareDocument">Share</button>
        </template>
    </Modal>
</template>


<script setup>
import Modal from './Modal.vue';
import { onMounted, ref } from 'vue';
import customAxios from '../helper/axios';
const showModal = defineModel()
const users = ref([])
const selectedUser = ref(null)


const props = defineProps({
    documentName: String,
    documentId: String,
})

onMounted(() => {
    fetchUsers();
});


async function shareDocument() {
    console.log("Sharing document", props.documentId, "with user", selectedUser.value);

    try {
        await customAxios.post('/collab/share', {
            document_id: props.documentId,
            invited_user_id: selectedUser.value.id,
        });

        console.log('Document shared successfully');
        showModal.value = false;
    } catch (error) {
        console.error('Error sharing document:', error);
        const message =
            error.response?.data?.error || 'Unknown error occurred while sharing document.';
        alert('Error sharing document: ' + message);
    }
}

async function fetchUsers() {
    try {
        const { data } = await customAxios.get('/users');
        users.value = data;
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}


</script>