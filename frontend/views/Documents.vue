<template>
    <h2>Documents</h2>
    <div v-if="!isLoggedIn">
        <p>Please log in to view your documents.</p>
        <RouterLink to="/auth">Go to Login</RouterLink>
    </div>
    <div v-else>
        <Document @click="editDocument(doc.id)" v-for="doc in documents" :key="doc.id" :documentId="doc.id" :title="doc.name" :createdAt="doc.created_at" />
    </div>
</template>

<script setup>
import { onMounted, ref, } from 'vue';
import { useStore } from '../store/store';
import Document from '../components/Document.vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const store = useStore();
const documents = ref([]);  

const isLoggedIn = ref(false); // Placeholder for actual authentication check
function editDocument(docId) {
    router.push({ name: 'editor', params: { document_id: docId } });
}


async function getDocuments() {
    try {
        const resp = await fetch('/api/documents', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        if (resp.ok) {
            const data = await resp.json();
            documents.value = data;
            console.log('Documents fetched:', data);
            // Handle the fetched documents (e.g., store them in a reactive variable)
        } else {
            console.error('Failed to fetch documents');
        }
    } catch (error) {
        console.error('Error fetching documents:', error);
    }
    
}


onMounted(async () => {
    isLoggedIn.value = await store.checkIfLoggedIn();
    await getDocuments();
});

</script>