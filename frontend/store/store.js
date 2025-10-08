import { defineStore } from "pinia";
import { ref } from "vue";

export const useStore = defineStore("store", () => {
    const currentDocument = ref("<p>Hello World! 🌎️</p>");  
    async function checkIfLoggedIn() {
        try {
            const resp = await fetch('/api/documents', {
                method: 'GET',
                credentials: 'include', // Include cookies for authentication
                headers: {
                    'Content-Type': 'application/json',

                },
            })
            if (resp.ok) {
                console.log("User is logged in");
                return true;
            } else {
                if (resp.status === 401) {
                    console.log("User is not logged in");
                    return false;
                }
            }
        } catch (error) {
            console.error("Error checking login status:", error);
            return false;
        }
        
    }
    return { checkIfLoggedIn, currentDocument };
});
