<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import AppHeader from '../components/AppHeader.vue'

const auth   = useAuthStore()
const router = useRouter()

const isAdmin = computed(() => auth.user?.roles?.includes('ADMIN') ?? false)
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="main-content">
      <div class="content-area">
        <div class="profile-page">
          <h2>Профиль</h2>

          <div class="card" style="padding: 0 20px">
            <div class="profile-field">
              <label>Имя пользователя</label>
              <span>{{ auth.user?.username }}</span>
            </div>
            <div class="profile-field">
              <label>Email</label>
              <span>{{ auth.user?.email }}</span>
            </div>
            <div class="profile-field">
              <label>Роли</label>
              <span>
                <span
                  v-for="role in auth.user?.roles"
                  :key="role"
                  class="profile-badge"
                >{{ role }}</span>
              </span>
            </div>
            <div class="profile-field">
              <label>ID пользователя</label>
              <span style="font-family: monospace; font-size: 13px; color: var(--text-muted)">
                {{ auth.user?.user_id }}
              </span>
            </div>
          </div>

          <div style="display:flex;flex-direction:column;gap:10px;margin-top:20px">
            <button class="btn btn-ghost" style="align-self:start" @click="router.push('/change-password')">
              🔑 Изменить пароль
            </button>
            <button
              v-if="isAdmin"
              class="btn btn-primary"
              style="align-self:start"
              @click="router.push('/admin')"
            >
              ⚙️ Панель администратора
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
