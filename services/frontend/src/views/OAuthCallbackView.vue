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
    error.value = 'Не удалось получить данные пользователя.'
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
        <div style="font-size:48px;margin-bottom:12px">❌</div>
        <p class="error-msg" style="text-align:left">{{ error }}</p>
        <RouterLink to="/login" class="btn btn-ghost" style="margin-top:20px;display:inline-flex">
          Вернуться ко входу
        </RouterLink>
      </div>
    </div>
  </div>
</template>
