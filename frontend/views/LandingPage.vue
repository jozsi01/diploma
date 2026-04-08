<template>
  <div class="landing-container">
    <div class="content">
      <h1>Welcome to DocShare</h1>
      <p>Your secure and seamless document sharing platform</p>
      <button class="cta-btn" @click="navigateToAuth">Get Started</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
const router = useRouter();

function navigateToAuth() { 
    router.push({ name: 'documents' });
}

</script>

<style scoped>
.landing-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #2a62aa;
  color: white;
  text-align: center;
}
.content{
    padding: 0;
}

.content h1 {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.content p {
  font-size: 1.2rem;
  opacity: 0.9;
  margin-bottom: 2rem;
}

.cta-btn {
  padding: 1rem 2.5rem;
  background-color: white;
  color: #2a62aa;
  border: none;
  border-radius: 15px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
}

.cta-btn:hover {
  transform: scale(1.07);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.25);
}
</style>
