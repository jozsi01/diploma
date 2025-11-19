import { defineStore } from "pinia";
import { ref } from "vue";

export const useStore = defineStore("store", () => {
    const currentDocument = ref("<p>Hello World! 🌎️</p>");  
    const documents = ref([]);
    const selectedCommentId = ref(null);
    const comments = ref([]);
    const sharedDocumentsWithUser = ref([]);
    const sharedDocumentsByUser = ref([]);
    
    return { currentDocument,comments, sharedDocumentsWithUser, sharedDocumentsByUser, documents, selectedCommentId };
});
