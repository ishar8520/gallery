<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { authApi } from '../api/index.js'
import AppHeader from '../components/AppHeader.vue'

const router  = useRouter()
const auth    = useAuthStore()

const current  = ref('')
const next     = ref('')
const confirm  = ref('')
const error    = ref('')
const success  = ref('')
const loading  = ref(false)

function validatePassword(pwd) {
  if (pwd.length < 8) return 'Минимум 8 символов'
  if (/[^\x00-\x7F]/.test(pwd)) return 'Только латиница и спецсимволы'
  if (!/[A-Z]/.test(pwd)) return 'Нужна хотя бы одна заглавная буква'
  if (!/[^a-zA-Z0-9]/.test(pwd)) return 'Нужен хотя бы один спецсимвол'
  return ''
}

async function submit() {
  error.value   = ''
  success.value = ''

  if (next.value !== confirm.value) {
    error.value = 'Новые пароли не совпадают'
    return
  }
  const pwdErr = validatePassword(next.value)
  if (pwdErr) { error.value = pwdErr; return }

  loading.value = true
  try {
    await authApi.changePassword(auth.user.user_id, current.value, next.value)
    success.value = 'Пароль успешно изменён'
    current.value = ''
    next.value    = ''
    confirm.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка смены пароля'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="main-content">
      <div class="content-area">
        <div class="profile-page">
          <h2>Изменить пароль</h2>

          <div class="card" style="padding: 24px">
            <div v-if="error"   class="error-msg"   style="margin-bottom:16px">{{ error }}</div>
            <div v-if="success" class="success-msg" style="margin-bottom:16px">{{ success }}</div>

            <form class="auth-form" @submit.prevent="submit">
              <div class="form-group">
                <label>Текущий пароль</label>
                <input
                  class="input"
                  type="password"
                  v-model="current"
                  placeholder="••••••••"
                  autocomplete="current-password"
                  required
                />
              </div>

              <div class="form-group">
                <label>Новый пароль</label>
                <input
                  class="input"
                  type="password"
                  v-model="next"
                  placeholder="••••••••"
                  autocomplete="new-password"
                  required
                />
                <span class="form-hint">
                  Минимум 8 символов, только латиница, хотя бы одна заглавная буква и один спецсимвол
                </span>
              </div>

              <div class="form-group">
                <label>Подтвердите новый пароль</label>
                <input
                  class="input"
                  type="password"
                  v-model="confirm"
                  placeholder="••••••••"
                  autocomplete="new-password"
                  required
                />
              </div>

              <div style="display:flex;gap:12px;margin-top:8px">
                <button type="button" class="btn btn-ghost" @click="router.push('/profile')">
                  Отмена
                </button>
                <button class="btn btn-primary" type="submit" :disabled="loading">
                  <span v-if="loading" class="spinner" style="width:14px;height:14px"></span>
                  {{ loading ? 'Сохраняем...' : 'Изменить пароль' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
