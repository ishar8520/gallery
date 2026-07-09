<script setup>
import { ref, onMounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import { authApi } from '../api/index.js'

const users      = ref([])
const loading    = ref(false)
const error      = ref('')

// edit modal
const editUser   = ref(null)
const editName   = ref('')
const editEmail  = ref('')
const editError  = ref('')
const editSaving = ref(false)

// role toggle state: userId → loading
const roleLoading = ref({})

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

function closeEdit() {
  editUser.value = null
}

async function saveEdit() {
  editError.value = ''
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
      <div class="content-area" style="padding: 32px; max-width: 900px">

        <div class="content-header" style="margin-bottom: 24px">
          <h2>Панель администратора</h2>
        </div>

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
                    <button
                      class="btn btn-ghost btn-sm"
                      @click="openEdit(user)"
                      title="Редактировать"
                    >✏️</button>
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
</style>
