<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '../api/index.js'

const route  = useRoute()
const router = useRouter()
const status = ref('loading') // loading | success | error
const error  = ref('')

onMounted(async () => {
  const token = route.query.token
  if (!token) { status.value = 'error'; error.value = 'Токен не найден'; return }
  try {
    await authApi.confirm(token)
    status.value = 'success'
  } catch (e) {
    status.value = 'error'
    error.value  = e.response?.data?.detail || 'Ссылка недействительна или уже использована'
  }
})
</script>

<template>
  <div class="auth-page">
    <div class="auth-box card" style="text-align:center">
      <div v-if="status === 'loading'">
        <div class="spinner" style="width:32px;height:32px;margin:0 auto 16px"></div>
        <p class="subtitle">Подтверждаем email...</p>
      </div>

      <div v-else-if="status === 'success'">
        <div style="font-size:48px;margin-bottom:12px">✅</div>
        <h1 style="margin-bottom:8px">Email подтверждён!</h1>
        <p class="subtitle">Аккаунт активирован. Можно войти.</p>
        <RouterLink to="/login" class="btn btn-primary" style="margin-top:20px;display:inline-flex">
          Войти
        </RouterLink>
      </div>

      <div v-else>
        <div style="font-size:48px;margin-bottom:12px">❌</div>
        <h1 style="margin-bottom:8px">Ошибка</h1>
        <p class="error-msg" style="text-align:left">{{ error }}</p>
        <RouterLink to="/register" class="btn btn-ghost" style="margin-top:20px;display:inline-flex">
          Зарегистрироваться снова
        </RouterLink>
      </div>
    </div>
  </div>
</template>
