<template>
<div>
    <div class="document-card">
        <BookText class="document-icon" />
        <div class="document-title">{{ props.title }}</div>
        <p>Created: {{ formatIsoDate(props.createdAt) }}</p>
        <Download class="document-icon download" />
    </div>
</div>

</template>

<script setup>
import { BookText } from 'lucide-vue-next';
import { Download } from 'lucide-vue-next';


function formatIsoDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

const props = defineProps({
    documentId: String,
    title: String,
    createdAt: String,

});

</script>

<style scoped>
.document-card {
    display: flex;
    align-items: center;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #2a62aa;
    margin: 8px 0;
}
.document-icon {
    margin: 10px;
    color: white;
}
.download {
    margin-left: auto;
    padding: 2px;

}
.download:hover {
    cursor: pointer;
    border: 2px solid grey;
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