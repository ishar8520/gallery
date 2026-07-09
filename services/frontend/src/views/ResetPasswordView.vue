<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '../api/index.js'

const route    = useRoute()
const router   = useRouter()
const token    = ref('')
const password = ref('')
const confirm  = ref('')
const error    = ref('')
const done     = ref(false)
const loading  = ref(false)

onMounted(() => {
  token.value = route.query.token ?? ''
  if (!token.value) error.value = 'Ссылка недействительна: токен не найден.'
})

async function submit() {
  error.value = ''
  if (password.value !== confirm.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  loading.value = true
  try {
    await authApi.resetPassword(token.value, password.value)
    done.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ссылка недействительна или истекла'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-box card">
      <h1>Новый пароль</h1>

      <div v-if="done" style="text-align:center">
        <div style="font-size:48px;margin-bottom:12px">✅</div>
        <p class="subtitle">Пароль успешно изменён. Теперь можно войти.</p>
        <RouterLink to="/login" class="btn btn-primary" style="margin-top:20px;display:inline-flex">
          Войти
        </RouterLink>
      </div>

      <template v-else>
        <p class="subtitle">Придумайте новый пароль для вашего аккаунта.</p>

        <form class="auth-form" @submit.prevent="submit">
          <div v-if="error" class="error-msg">{{ error }}</div>

          <div class="form-group">
            <label>Новый пароль</label>
            <input
              class="input"
              type="password"
              v-model="password"
              placeholder="••••••••"
              autocomplete="new-password"
              required
              :disabled="!token"
            />
          </div>

          <div class="form-group">
            <label>Повторите пароль</label>
            <input
              class="input"
              type="password"
              v-model="confirm"
              placeholder="••••••••"
              autocomplete="new-password"
              required
              :disabled="!token"
            />
          </div>

          <button
            class="btn btn-primary"
            type="submit"
            :disabled="loading || !token"
            style="width:100%"
          >
            <span v-if="loading" class="spinner" style="width:14px;height:14px"></span>
            {{ loading ? 'Сохраняем...' : 'Сохранить пароль' }}
          </button>
        </form>
      </template>
    </div>
  </div>
</template>
