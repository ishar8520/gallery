<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'

const router   = useRouter()
const auth     = useAuthStore()
const username = ref('')
const password = ref('')
const error    = ref('')
const loading  = ref(false)

async function submit() {
  error.value   = ''
  loading.value = true
  try {
    const { data } = await authApi.login(username.value, password.value)
    await auth.onLogin(data.access_token)
    router.push('/gallery')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-box card">
      <h1>Вход</h1>
      <p class="subtitle">Войдите в свой аккаунт Gallery</p>

      <form class="auth-form" @submit.prevent="submit">
        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="form-group">
          <label>Имя пользователя</label>
          <input class="input" v-model="username" placeholder="username" autocomplete="username" required />
        </div>

        <div class="form-group">
          <label>Пароль</label>
          <input class="input" type="password" v-model="password" placeholder="••••••••" autocomplete="current-password" required />
        </div>

        <button class="btn btn-primary" type="submit" :disabled="loading" style="width:100%">
          <span v-if="loading" class="spinner" style="width:14px;height:14px"></span>
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>
      </form>

      <p class="auth-link" style="margin-top:20px">
        Нет аккаунта? <RouterLink to="/register">Зарегистрироваться</RouterLink>
      </p>
    </div>
  </div>
</template>
