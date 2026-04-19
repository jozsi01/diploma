<template>

    <div class="container">
        <div class="auth_container">
            <div style="display: flex; justify-content: space-around;">
                <h2 class="authMode" @click="authMode = 'login'">Login</h2>
                <h2 class="authMode" @click="authMode = 'register'">Register</h2>
            </div>

            <form @submit.prevent="sendCredentials">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input v-model="username" type="text" id="username" name="username" required />
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input v-model="password" type="password" id="password" name="password" required />
                </div>
                <button type="submit">{{ authMode === 'login' ? 'Login' : 'Register' }}</button>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router';
const router = useRouter();




const authMode = ref('login') // 'login' or 'register'
const password = ref('')
const username = ref('')

async function sendCredentials() {
    // Implement the logic to send credentials to the backend
    if (authMode.value === 'login') {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username.value,
                password: password.value,
            }),
        })
        if (resp.ok) {
            console.log('Login successful:');
            const data = await resp.json();
            localStorage.setItem("access_token", data.access_token);
            router.push({ name: 'documents' });
            
        } else {
            const data = await resp.text();
            console.error('Login failed:', data);
        }
    } else {
        const resp = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username.value,
                password: password.value,
            }),
        })
        if (resp.ok) {
            const data = await resp.json();
            console.log(data.msg);
        } else {
            const data = await resp.text();
            console.error('Registration failed:', data);
        }
    }
}

</script>

<style scoped>
.container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    border: 1px solid rgb(173, 24, 24);
}

.authMode {
    cursor: pointer;

}

.authMode:hover {
    text-decoration: underline;
    color: #0056b3;
}

.auth_container {
    background-color: #f9f9f9;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    width: 300px;
}

h2 {
    text-align: center;
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"],
input[type="password"] {
    width: 100%;
    padding: 8px;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 4px;
}

button {
    width: 100%;
    padding: 10px;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #218838;
}
</style>