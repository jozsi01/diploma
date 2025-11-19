<template>

    <div v-if="!isLoggedIn">
        <p>Please log in to view your documents.</p>
        <RouterLink to="/auth">Go to Login</RouterLink>
    </div>
    <div v-else>
        <h2>Documents</h2>
        <Document @click="editDocument(doc.id)" v-for="doc in store.documents" :key="doc.id" :documentId="doc.id"
            :title="doc.name" :createdAt="doc.created_at" />
        <CreateDocument />

        <h2 style="margin-top:40px;">Shared Documents</h2>
        <h3> With Me</h3>
        <Document @click="editDocument(doc.id)" v-for="doc in store.sharedDocumentsWithUser" :key="doc.id"
            :documentId="doc.id" :title="doc.name" :createdAt="doc.created_at">
            <template #share>
                <p>Shared by: {{ doc.invited_by_user_name }}</p>
            </template>
            <template #action-buttons>
                <Eye class="inspect-button" @click="inspectDoc" :size="32" />
            </template>

        </Document>


        <h3> By Me</h3>



        <template v-for="doc in store.sharedDocumentsByUser" :key="doc.doc.id">
            <Document @click="toggleOpenDicId(doc.doc.id)" :documentId="doc.doc.id" :title="doc.doc.name"
                :createdAt="doc.doc.created_at">
                <template #action-buttons>
                    <div>
                    </div>
                </template>
            </Document>
            <Transition name="persons">
                <div class="personContainer" v-if="openDocID === doc.doc.id">
                    <SharedWithPerson v-for="user in doc.shared_with" :key="user.id" :username="user.username"
                        @click="selectedPerson = user; showRemoveModal = true" />
                </div>
            </Transition>


        </template>
        <Modal :show="showRemoveModal" @close="closeModal">
            <!-- Header -->
            <template #header>
                <h3 class="modal-header">Remove Sharing</h3>
            </template>

            <!-- Body -->
            <template #body>
                <p class="modal-body">
                    Are you sure you want to remove sharing for
                    <span class="username">{{ selectedPerson.username }}</span>?
                </p>
            </template>

            <!-- Footer -->
            <template #footer>
                <div class="modal-footer">
                    <button class="btn remove" @click="removeSharing">
                        Remove
                    </button>
                    <button class="btn cancel" @click="showRemoveModal = false">
                        Cancel
                    </button>
                    
                </div>
            </template>
        </Modal>





</div>
</template>

<script setup>
import { onMounted, ref, } from 'vue';
import { useStore } from '../store/store';
import Document from '../components/Document.vue';
import { useRouter } from 'vue-router';
import CreateDocument from '../components/CreateDocument.vue';
import { Eye } from 'lucide-vue-next';
import customAxios from '../helper/axios';
import SharedWithPerson from '../components/SharedWithPerson.vue';
import Modal from '../components/Modal.vue';

const router = useRouter();

const store = useStore();

const isLoggedIn = ref(false); // Placeholder for actual authentication check
function editDocument(docId) {
    router.push({ name: 'editor', params: { document_id: docId } });
}
function inspectDoc() {
    alert("Inspect document - feature not implemented yet.");
}
const openDocID = ref(null);
const selectedPerson = ref(null);
const showRemoveModal = ref(false);
function closeModal() {
    showRemoveModal.value = false;
}
function toggleOpenDicId(docId) {
    if (openDocID.value === docId) {
        openDocID.value = null;
    } else {
        openDocID.value = docId;
    }
}

function removeSharing() {
    customAxios.post('/collab/unshare', {
        document_id: openDocID.value,
        invited_user_id: selectedPerson.value.id,
    }).then(() => {
        console.log('Sharing removed successfully');
        getSharedDocumentsByUser();
    }).catch((error) => {
        console.error('Error removing sharing:', error);
        const message =
            error.response?.data?.error || 'Unknown error occurred while removing sharing.';
        alert('Error removing sharing: ' + message);
    });
    showRemoveModal.value = false;
}


async function getDocuments() {
    try {
        const { data } = await customAxios.get('/documents');
        store.documents = data;
        isLoggedIn.value = true;
        console.log('Documents fetched:', data);
    } catch (error) {
        console.error('Error fetching documents:', error);
    }
}

// Fetch documents shared *with* the user
async function getSharedDocumentsWithUser() {
    try {
        const { data } = await customAxios.get('/collab/shared_documents/with_user');
        console.log('Shared Documents fetched (with user):', data);
        store.sharedDocumentsWithUser = data.shared_documents;
    } catch (error) {
        console.error('Error fetching shared documents (with user):', error);
    }
}

// Fetch documents shared *by* the user
async function getSharedDocumentsByUser() {
    try {
        const { data } = await customAxios.get('/collab/shared_documents/by_user');
        console.log('Shared Documents fetched (by user):', data);
        store.sharedDocumentsByUser = data.shared_documents;
    } catch (error) {
        console.error('Error fetching shared documents (by user):', error);
    }
}


onMounted(async () => {
    await getDocuments();
    getSharedDocumentsWithUser();
    getSharedDocumentsByUser();
});

</script>

<style scoped>
.inspect-button {
    margin: 8px 5px;
    color: white;
    border: none;
    background: none;
    padding: 0;
    font: inherit;
}

.inspect-button:hover {
    cursor: pointer;
    color: #0cb8fc;
}

.personContainer {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-left: 40px;
    margin-bottom: 20px;
}

.persons-enter-active,
.persons-leave-active {
    transition: all 0.3s ease;
    /* Adjust speed here */
    overflow: hidden;
}

.persons-enter-from,
.persons-leave-to {
    opacity: 0;
    transform: translateY(-10px);
    max-height: 0;
}

.persons-enter-to,
.persons-leave-from {
    opacity: 1;
    transform: translateY(0);
    max-height: 500px;
    /* Should be higher than your expected content height */
}
.modal-header {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.modal-body {
  color: #555;
  font-size: 1rem;
  line-height: 1.5;
}

.username {
  font-weight: 600;
  color: #1a1a1a;
}

/* Footer layout */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  font-size: 0.95rem;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn.cancel {
  background-color: #f0f0f0;
  color: #333;
}

.btn.cancel:hover {
  background-color: #e0e0e0;
}

.btn.remove {
  background-color: #e74c3c;
  color: white;
}

.btn.remove:hover {
  background-color: #c0392b;
}

/* Optional: modal fade-in animation */
.Modal-enter-active,
.Modal-leave-active {
  transition: opacity 0.3s ease;
}

.Modal-enter-from,
.Modal-leave-to {
  opacity: 0;
}
</style>
