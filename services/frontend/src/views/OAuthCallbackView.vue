<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { tokenRef } from '../api/index.js'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()
const error  = ref('')

onMounted(async () => {
  const oauthError = route.query.error
  if (oauthError) {
    error.value = decodeURIComponent(oauthError)
    return
  }

  const token = route.query.access_token
  if (!token) {
    error.value = 'Токен не получен. Попробуйте войти снова.'
    return
  }

  tokenRef.value = token
  await auth.fetchMe()
  if (auth.user) {
    router.replace('/gallery')
  } else {
    error.value = 'Не удалось получить данные пользователя. Попробуйте снова.'
  }
})
</script>

<template>
  <div class="auth-page">
    <div class="auth-box card" style="text-align:center">
      <div v-if="!error">
        <div class="spinner" style="width:32px;height:32px;margin:0 auto 16px"></div>
        <p class="subtitle">Выполняется вход...</p>
      </div>

      <div v-else>
        <div style="font-size:48px;margin-bottom:16px">⚠️</div>
        <h1 style="margin-bottom:8px">Не удалось войти</h1>
        <p class="subtitle" style="margin-bottom:20px">{{ error }}</p>
        <RouterLink to="/login" class="btn btn-primary" style="display:inline-flex">
          Попробовать снова
        </RouterLink>
      </div>
    </div>
  </div>
</template>
