<template>
    <div class="sidebar" :class="{ expanded: isExpanded }" @mouseenter="isExpanded = true"
        @mouseleave="isExpanded = false">
        <RouterLink style="text-decoration: none; color: inherit;" to="/" class="title">{{ isExpanded ? 'Editor' : 'E'
        }}</RouterLink>

        <div class="options" :class="{ expanded: isExpanded }">
            <RouterLink style="text-decoration: none; color: inherit;" to="/documents" class="option">
                <BookText v-if="!isExpanded" />
                <div v-else>Documents</div>
            </RouterLink>

            <RouterLink style="text-decoration: none; color: inherit;" to="/collaboration" class="option">
                <MessageSquareText v-if="!isExpanded" />
                <div v-else>Collaboration</div>
            </RouterLink>


            <div class="option logout">
                <LogOut v-if="!isExpanded" />
                <div v-else @click="logout">Logout</div>
            </div>
        </div>


    </div>
</template>

<script setup>
import { ref } from 'vue'
import { BookText, LogOut, MessageSquareText } from 'lucide-vue-next';

import { useRouter } from 'vue-router';

const isExpanded = ref(false)

const router = useRouter();
async function logout() {
    let res = await fetch('/api/auth/logout', {
        method: 'POST',
    })
    if (res.ok) {
        router.push('/auth');
        console.log('Logged out successfully');
    } else {
        console.error('Logout failed');
    }
}

</script>

<style scoped>
.sidebar {
    max-height: 100vh;
    overflow: hidden;
    background-color: #2a62aa;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: width 0.3s ease;
    overflow: hidden;
    padding: 10px 0;
    width: 40px;
    /* collapsed */
}

.sidebar.expanded {
    align-items: flex-start;
    width: 220px;
    /* expanded */
}

.title {
    font-size: 24px;
    font-weight: bold;
    padding: 0 16px;
}

.logout {
    margin-top: auto;
}

.options {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    height: 100%;
    margin-top: 20px;
}

.options.expanded {
    align-items: flex-start;
}

.option {
    width: 100%;
    /* fills the sidebar width */
    padding: 12px 16px;
    font-size: 18px;
    white-space: nowrap;

    display: flex;
    /* make the inner content a flex container */
    justify-content: center;
    /* center the icon/text horizontally */
    align-items: center;

    transition: background-color 0.2s ease, justify-content 0.3s ease;
}

.options.expanded .option {
    justify-content: flex-start;
    /* align left when expanded */
}


.option:hover {
    background-color: #1e4a7a;
    cursor: pointer;
}
</style>
