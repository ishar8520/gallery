<script setup>
import { ref } from 'vue'
import { authApi } from '../api/index.js'

const username     = ref('')
const email        = ref('')
const password     = ref('')
const error        = ref('')
const success      = ref('')
const loading      = ref(false)

// Клиентская валидация — сервер повторит эти же проверки,
// но ранний фидбэк снижает количество round-trip'ов.
function validateUsername(val) {
  if (!val) return 'Обязательное поле'
  if (/[^\x00-\x7F]/.test(val)) return 'Только латиница, цифры и символы _ - .'
  if (!/^[a-zA-Z0-9._-]+$/.test(val)) return 'Только латиница, цифры и символы _ - .'
  return ''
}

function validatePassword(pwd) {
  if (pwd.length < 8)               return 'Минимум 8 символов'
  if (/[^\x00-\x7F]/.test(pwd))    return 'Только латиница и спецсимволы'
  if (!/[A-Z]/.test(pwd))           return 'Нужна хотя бы одна заглавная буква'
  if (!/[^a-zA-Z0-9]/.test(pwd))   return 'Нужен хотя бы один спецсимвол'
  return ''
}

const usernameError = ref('')
const passwordError = ref('')

function onUsernameBlur() {
  usernameError.value = validateUsername(username.value)
}

function onPasswordBlur() {
  passwordError.value = validatePassword(password.value)
}

async function submit() {
  error.value   = ''
  success.value = ''

  usernameError.value = validateUsername(username.value)
  passwordError.value = validatePassword(password.value)
  if (usernameError.value || passwordError.value) return

  loading.value = true
  try {
    const { data } = await authApi.register(username.value, email.value, password.value)
    success.value = data.message || 'Проверьте почту для подтверждения регистрации'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-box card">
      <h1>Регистрация</h1>
      <p class="subtitle">Создайте аккаунт Gallery</p>

      <form class="auth-form" @submit.prevent="submit">
        <div v-if="error"   class="error-msg">{{ error }}</div>
        <div v-if="success" class="success-msg">{{ success }}</div>

        <template v-if="!success">
          <div class="form-group">
            <label>Имя пользователя</label>
            <input
              class="input"
              :class="{ 'input-error': usernameError }"
              v-model="username"
              placeholder="username"
              autocomplete="username"
              @blur="onUsernameBlur"
              required
            />
            <span v-if="usernameError" class="field-error">{{ usernameError }}</span>
            <span v-else class="form-hint">Только латиница, цифры и символы _ - .</span>
          </div>

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

          <div class="form-group">
            <label>Пароль</label>
            <input
              class="input"
              :class="{ 'input-error': passwordError }"
              type="password"
              v-model="password"
              placeholder="••••••••"
              autocomplete="new-password"
              @blur="onPasswordBlur"
              required
            />
            <span v-if="passwordError" class="field-error">{{ passwordError }}</span>
            <span v-else class="form-hint">
              Минимум 8 символов, только латиница, хотя бы одна заглавная буква и один спецсимвол
            </span>
          </div>

          <button class="btn btn-primary" type="submit" :disabled="loading" style="width:100%">
            <span v-if="loading" class="spinner" style="width:14px;height:14px"></span>
            {{ loading ? 'Регистрируем...' : 'Зарегистрироваться' }}
          </button>
        </template>
      </form>

      <p class="auth-link" style="margin-top:20px">
        Уже есть аккаунт? <RouterLink to="/login">Войти</RouterLink>
      </p>
    </div>
  </div>
</template>
