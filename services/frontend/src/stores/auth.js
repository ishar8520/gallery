import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, tokenRef } from '../api/index.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)

  // Вызывается при загрузке приложения.
  // Пробуем refresh cookie → получаем access token → получаем user info.
  async function fetchMe() {
    try {
      const { data } = await authApi.refresh()
      tokenRef.value = data.access_token
      const me = await authApi.me()
      user.value = me.data
    } catch {
      user.value = null
      tokenRef.value = null
    }
  }

  // Вызывается из LoginView: сохраняем токен из ответа на login, потом берём user info.
  async function onLogin(accessToken) {
    tokenRef.value = accessToken
    try {
      const { data } = await authApi.me()
      user.value = data
    } catch {
      user.value = null
      tokenRef.value = null
    }
  }

  async function logout() {
    await authApi.logout().catch(() => {})
    user.value = null
    tokenRef.value = null
  }

  return { user, fetchMe, onLogin, logout }
})
