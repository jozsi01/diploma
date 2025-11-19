
<template>

    <div class="shared-with-person">
        <User />
        <span>{{ username }}</span>
    </div>

</template>

<script setup>
import { User } from 'lucide-vue-next';



defineProps
({
    username: String,
})

</script>

<style scoped>
.shared-with-person {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size:24px;
    background-color: #2a62aa;
    border-radius: 5px;
    padding: 4px

}
.shared-with-person:hover {
    cursor: pointer;
    background-color: #1e4e8c;
}
</style>