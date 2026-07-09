<script setup>
import { ref } from 'vue'
import { authApi } from '../api/index.js'

const email   = ref('')
const error   = ref('')
const sent    = ref(false)
const loading = ref(false)

async function submit() {
  error.value   = ''
  loading.value = true
  try {
    await authApi.forgotPassword(email.value)
    sent.value = true
  } catch {
    error.value = 'Произошла ошибка. Попробуйте ещё раз.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-box card">
      <h1>Сброс пароля</h1>

      <div v-if="sent" style="text-align:center">
        <div style="font-size:48px;margin-bottom:12px">📧</div>
        <p class="subtitle">
          Если аккаунт с таким email существует, мы отправили письмо со ссылкой для сброса пароля.
        </p>
        <RouterLink to="/login" class="btn btn-ghost" style="margin-top:20px;display:inline-flex">
          Вернуться ко входу
        </RouterLink>
      </div>

      <template v-else>
        <p class="subtitle">Введите email, и мы пришлём ссылку для сброса пароля.</p>

        <form class="auth-form" @submit.prevent="submit">
          <div v-if="error" class="error-msg">{{ error }}</div>

          <div class="form-group">
            <label>Email</label>
            <input
              class="input"
              type="email"
              v-model="email"
              placeholder="you@example.com"
              autocomplete="email"
              required
            />
          </div>

          <button class="btn btn-primary" type="submit" :disabled="loading" style="width:100%">
            <span v-if="loading" class="spinner" style="width:14px;height:14px"></span>
            {{ loading ? 'Отправляем...' : 'Отправить ссылку' }}
          </button>
        </form>

        <p class="auth-link" style="margin-top:20px">
          Вспомнили пароль? <RouterLink to="/login">Войти</RouterLink>
        </p>
      </template>
    </div>
  </div>
</template>
