<script setup>
import { ref, onMounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import { authApi, ugcApi } from '../api/index.js'

// ── Users ─────────────────────────────────────────────────────────────────────
const users      = ref([])
const loading    = ref(false)
const error      = ref('')

const editUser   = ref(null)
const editName   = ref('')
const editEmail  = ref('')
const editError  = ref('')
const editSaving = ref(false)
const roleLoading = ref({})

// ── Stats ─────────────────────────────────────────────────────────────────────
const activeTab    = ref('users')
const statsLoading = ref(false)
const statsError   = ref('')
const photoStats   = ref(null)
const authStats    = ref(null)
const clickStats   = ref(null)

async function loadUsers() {
  loading.value = true
  error.value   = ''
  try {
    const { data } = await authApi.listUsers()
    users.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки пользователей'
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  if (photoStats.value) return
  statsLoading.value = true
  statsError.value   = ''
  try {
    const [photos, auth, clicks] = await Promise.all([
      ugcApi.statsPhotos(),
      ugcApi.statsAuth(),
      ugcApi.statsClicks(),
    ])
    photoStats.value = photos.data
    authStats.value  = auth.data
    clickStats.value = clicks.data
  } catch (e) {
    statsError.value = e.response?.data?.detail || 'Ошибка загрузки статистики'
  } finally {
    statsLoading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'stats') loadStats()
}

onMounted(loadUsers)

async function deleteUser(user) {
  if (!confirm(`Удалить пользователя «${user.username}»? Это действие необратимо.`)) return
  try {
    await authApi.deleteUser(user.user_id)
    users.value = users.value.filter(u => u.user_id !== user.user_id)
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка удаления')
  }
}

function openEdit(user) {
  editUser.value  = user
  editName.value  = user.username
  editEmail.value = user.email
  editError.value = ''
}

function closeEdit() { editUser.value = null }

async function saveEdit() {
  editError.value  = ''
  editSaving.value = true
  try {
    await authApi.patchUser(editUser.value.user_id, {
      username: editName.value,
      email:    editEmail.value,
    })
    editUser.value.username = editName.value
    editUser.value.email    = editEmail.value
    closeEdit()
  } catch (e) {
    editError.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    editSaving.value = false
  }
}

async function toggleAdmin(user) {
  const id      = user.user_id
  const isAdmin = user.roles.includes('ADMIN')
  roleLoading.value[id] = true
  try {
    if (isAdmin) {
      await authApi.deleteRole(id, 'ADMIN')
      user.roles = user.roles.filter(r => r !== 'ADMIN')
    } else {
      await authApi.addRole(id, 'ADMIN')
      user.roles = [...user.roles, 'ADMIN']
    }
  } catch (e) {
    alert(e.response?.data?.detail || 'Ошибка изменения роли')
  } finally {
    delete roleLoading.value[id]
  }
}
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="main-content">
      <div class="content-area" style="padding: 32px; max-width: 960px">

        <div class="content-header" style="margin-bottom: 24px">
          <h2>Панель администратора</h2>
          <div style="display:flex;gap:8px">
            <button
              class="btn"
              :class="activeTab === 'users' ? 'btn-primary' : 'btn-ghost'"
              @click="switchTab('users')"
            >Пользователи</button>
            <button
              class="btn"
              :class="activeTab === 'stats' ? 'btn-primary' : 'btn-ghost'"
              @click="switchTab('stats')"
            >Статистика</button>
          </div>
        </div>

        <!-- ── Users tab ─────────────────────────────────────────────────── -->
        <template v-if="activeTab === 'users'">
          <div v-if="error" class="error-msg" style="margin-bottom:16px">{{ error }}</div>

          <div v-if="loading" class="empty-state">
            <div class="spinner" style="width:32px;height:32px"></div>
          </div>

          <div v-else class="card" style="padding: 0; overflow: hidden">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Пользователь</th>
                  <th>Email</th>
                  <th>Роли</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.user_id">
                  <td>
                    <div class="admin-user-name">{{ user.username }}</div>
                    <div class="admin-user-id">{{ user.user_id }}</div>
                  </td>
                  <td>{{ user.email }}</td>
                  <td>
                    <span
                      v-for="role in user.roles"
                      :key="role"
                      class="profile-badge"
                      :style="role === 'ADMIN' ? 'background:#fef3c7;color:#92400e' : ''"
                    >{{ role }}</span>
                  </td>
                  <td>
                    <div class="admin-actions">
                      <button class="btn btn-ghost btn-sm" @click="openEdit(user)" title="Редактировать">✏️</button>
                      <button
                        class="btn btn-ghost btn-sm"
                        :disabled="!!roleLoading[user.user_id]"
                        @click="toggleAdmin(user)"
                        :title="user.roles.includes('ADMIN') ? 'Снять ADMIN' : 'Назначить ADMIN'"
                      >
                        <span v-if="roleLoading[user.user_id]" class="spinner" style="width:12px;height:12px"></span>
                        <span v-else>{{ user.roles.includes('ADMIN') ? '⬇ ADMIN' : '⬆ ADMIN' }}</span>
                      </button>
                      <button
                        class="btn btn-ghost btn-sm"
                        style="color:var(--danger)"
                        @click="deleteUser(user)"
                        title="Удалить"
                      >🗑</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="users.length === 0">
                  <td colspan="4" style="text-align:center;color:var(--text-muted);padding:32px">
                    Нет пользователей
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- ── Stats tab ─────────────────────────────────────────────────── -->
        <template v-else-if="activeTab === 'stats'">
          <div v-if="statsError" class="error-msg" style="margin-bottom:16px">{{ statsError }}</div>

          <div v-if="statsLoading" class="empty-state">
            <div class="spinner" style="width:32px;height:32px"></div>
          </div>

          <div v-else-if="photoStats" class="stats-grid">

            <!-- Photos -->
            <div class="stat-card card">
              <div class="stat-title">Фотографии</div>
              <div class="stat-row">
                <span class="stat-label">Загружено</span>
                <span class="stat-value">{{ photoStats.total_uploaded }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">Удалено</span>
                <span class="stat-value">{{ photoStats.total_deleted }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">Хранится</span>
                <span class="stat-value">{{ photoStats.total_uploaded - photoStats.total_deleted }}</span>
              </div>
            </div>

            <!-- Auth -->
            <div class="stat-card card">
              <div class="stat-title">Авторизации</div>
              <div class="stat-row">
                <span class="stat-label">Всего</span>
                <span class="stat-value">{{ authStats.total }}</span>
              </div>
              <div
                v-for="p in authStats.by_provider"
                :key="p.provider"
                class="stat-row"
              >
                <span class="stat-label">{{ p.provider }}</span>
                <span class="stat-value">{{ p.count }}</span>
              </div>
            </div>

            <!-- Clicks -->
            <div class="stat-card card">
              <div class="stat-title">Клики</div>
              <div class="stat-row">
                <span class="stat-label">Всего</span>
                <span class="stat-value">{{ clickStats.total }}</span>
              </div>
            </div>

            <!-- Top pages -->
            <div class="stat-card card" style="grid-column: span 2">
              <div class="stat-title">Топ страниц</div>
              <table class="stats-table">
                <thead><tr><th>Страница</th><th>Клики</th></tr></thead>
                <tbody>
                  <tr v-for="p in clickStats.top_pages" :key="p.page">
                    <td>{{ p.page }}</td>
                    <td>{{ p.count }}</td>
                  </tr>
                  <tr v-if="!clickStats.top_pages.length">
                    <td colspan="2" style="color:var(--text-muted);text-align:center">Нет данных</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Top elements -->
            <div class="stat-card card" style="grid-column: span 1">
              <div class="stat-title">Топ элементов</div>
              <table class="stats-table">
                <thead><tr><th>Элемент</th><th>Клики</th></tr></thead>
                <tbody>
                  <tr v-for="e in clickStats.top_elements" :key="e.element">
                    <td>{{ e.element }}</td>
                    <td>{{ e.count }}</td>
                  </tr>
                  <tr v-if="!clickStats.top_elements.length">
                    <td colspan="2" style="color:var(--text-muted);text-align:center">Нет данных</td>
                  </tr>
                </tbody>
              </table>
            </div>

          </div>
        </template>
      </div>
    </div>
  </div>

  <!-- Edit modal -->
  <div class="modal-overlay" v-if="editUser" @click.self="closeEdit">
    <div class="modal" style="max-width:420px">
      <h3>Редактировать пользователя</h3>
      <div class="auth-form" style="margin-top:16px">
        <div v-if="editError" class="error-msg">{{ editError }}</div>
        <div class="form-group">
          <label>Имя пользователя</label>
          <input class="input" v-model="editName" />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input class="input" type="email" v-model="editEmail" />
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="closeEdit">Отмена</button>
        <button class="btn btn-primary" @click="saveEdit" :disabled="editSaving">
          <span v-if="editSaving" class="spinner" style="width:14px;height:14px"></span>
          {{ editSaving ? 'Сохраняем...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.admin-table thead th {
  background: var(--bg);
  padding: 10px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.admin-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.admin-table tbody tr:last-child td { border-bottom: none; }
.admin-table tbody tr:hover td { background: var(--bg); }
.admin-user-name { font-weight: 500; }
.admin-user-id   { font-family: monospace; font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.admin-actions   { display: flex; gap: 4px; }

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.stat-card {
  padding: 20px;
}
.stat-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}
.stat-row:last-child { border-bottom: none; }
.stat-label { color: var(--text-muted); font-size: 13px; }
.stat-value { font-weight: 600; font-variant-numeric: tabular-nums; }
.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.stats-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  padding: 4px 0 8px;
  border-bottom: 1px solid var(--border);
}
.stats-table td {
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}
.stats-table tr:last-child td { border-bottom: none; }
</style>
