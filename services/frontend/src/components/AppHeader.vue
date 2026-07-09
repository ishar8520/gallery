<script setup>
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <RouterLink to="/gallery" class="header-brand">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>
      Gallery
    </RouterLink>
    <nav class="header-nav">
      <RouterLink to="/gallery" class="nav-link">Фотографии</RouterLink>
      <RouterLink to="/profile" class="nav-link">Профиль</RouterLink>
    </nav>
    <div class="header-user" v-if="auth.user">
      <span class="header-username">{{ auth.user.username }}</span>
      <button class="btn btn-ghost btn-sm" @click="handleLogout">Выйти</button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: 56px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 24px;
  flex-shrink: 0;
}
.header-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
}
.header-nav {
  display: flex;
  gap: 4px;
  flex: 1;
}
.nav-link {
  padding: 6px 12px;
  border-radius: 6px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: background .12s, color .12s;
}
.nav-link:hover { background: var(--bg); color: var(--text); }
.nav-link.router-link-active { background: var(--primary-light); color: var(--primary); }
.header-user { display: flex; align-items: center; gap: 10px; }
.header-username { font-size: 13px; color: var(--text-muted); }
</style>
