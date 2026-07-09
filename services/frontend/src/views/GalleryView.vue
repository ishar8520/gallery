<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader  from '../components/AppHeader.vue'
import PhotoCard  from '../components/PhotoCard.vue'
import { photosApi, albumsApi } from '../api/index.js'

const router = useRouter()

// ── Данные ────────────────────────────────────────────────
const photos        = ref([])
const albums        = ref([])
// null = все фото, 'NO_ALBUM' = без папки, <uuid> = конкретный альбом
const selectedAlbum = ref(null)
const loading       = ref(false)
const loadError     = ref('')

// ── Групповое выделение ───────────────────────────────────
const selectedIds   = ref(new Set())

function toggleSelect(id) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

function clearSelection() {
  selectedIds.value = new Set()
}

function openPhoto(photoId) {
  const query = {}
  if (selectedAlbum.value === 'NO_ALBUM') query.no_album = 'true'
  else if (selectedAlbum.value)           query.album_id = selectedAlbum.value
  router.push({ path: `/photo/${photoId}`, query })
}

function selectAll() {
  selectedIds.value = new Set(photos.value.map(p => p.id))
}

const selectionCount = computed(() => selectedIds.value.size)

// ── Bulk удаление ─────────────────────────────────────────
async function bulkDelete() {
  if (!confirm(`Удалить ${selectionCount.value} фото? Это действие необратимо.`)) return
  try {
    await Promise.all([...selectedIds.value].map(id => photosApi.delete(id)))
    photos.value = photos.value.filter(p => !selectedIds.value.has(p.id))
    selectedIds.value = new Set()
  } catch (e) {
    alert(e.response?.data?.detail || 'Не удалось удалить часть фотографий')
    await loadPhotos()
  }
}

// ── Bulk перемещение ──────────────────────────────────────
const showBulkMove  = ref(false)
const bulkTarget    = ref('')
const bulkMoving    = ref(false)

async function bulkMove() {
  bulkMoving.value = true
  try {
    await Promise.all(
      [...selectedIds.value].map(id => photosApi.move(id, bulkTarget.value || null))
    )
    showBulkMove.value = false
    bulkTarget.value   = ''
    selectedIds.value  = new Set()
    await loadPhotos()
  } finally {
    bulkMoving.value = false
  }
}

// ── Загрузка данных ───────────────────────────────────────
async function loadAlbums() {
  try {
    const { data } = await albumsApi.list()
    albums.value = data
  } catch (e) {
    loadError.value = e.response?.data?.detail || 'Не удалось загрузить альбомы'
  }
}

async function loadPhotos() {
  loading.value = true
  loadError.value = ''
  clearSelection()
  try {
    let params = {}
    if (selectedAlbum.value === 'NO_ALBUM') {
      params = { no_album: true }
    } else if (selectedAlbum.value) {
      params = { album_id: selectedAlbum.value }
    }
    const { data } = await photosApi.list(params)
    photos.value = data
  } catch (e) {
    loadError.value = e.response?.data?.detail || 'Не удалось загрузить фотографии'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadAlbums(), loadPhotos()])
})

async function selectAlbum(albumId) {
  selectedAlbum.value = albumId
  await loadPhotos()
}

const currentAlbumName = computed(() => {
  if (!selectedAlbum.value) return 'Все фотографии'
  if (selectedAlbum.value === 'NO_ALBUM') return 'Фото без папки'
  return albums.value.find(a => a.id === selectedAlbum.value)?.name ?? ''
})

// ── Мультизагрузка ────────────────────────────────────────
const showUpload    = ref(false)
const uploadFiles   = ref([])      // File[]
const uploadAlbum   = ref('')
const uploading     = ref(false)
const uploadIdx     = ref(0)       // текущий файл в процессе
const uploadResults = ref([])      // [{ name, status: 'pending'|'done'|'error', error }]
const uploadDone    = ref(false)

function onFilesChange(e) {
  uploadFiles.value   = Array.from(e.target.files)
  uploadResults.value = []
  uploadDone.value    = false
}

function resetUpload() {
  uploadFiles.value   = []
  uploadAlbum.value   = ''
  uploading.value     = false
  uploadIdx.value     = 0
  uploadResults.value = []
  uploadDone.value    = false
}

async function doUpload() {
  if (!uploadFiles.value.length) return
  uploading.value    = true
  uploadDone.value   = false
  uploadResults.value = uploadFiles.value.map(f => ({
    name: f.name, status: 'pending', error: '',
  }))

  for (let i = 0; i < uploadFiles.value.length; i++) {
    uploadIdx.value = i
    const file = uploadFiles.value[i]
    const fd   = new FormData()
    fd.append('file', file)
    fd.append('title', file.name.replace(/\.[^.]+$/, ''))
    if (uploadAlbum.value) fd.append('album_id', uploadAlbum.value)
    try {
      await photosApi.upload(fd)
      uploadResults.value[i].status = 'done'
    } catch (e) {
      uploadResults.value[i].status = 'error'
      uploadResults.value[i].error  = e.response?.data?.detail || 'Ошибка загрузки'
    }
  }

  uploading.value  = false
  uploadDone.value = true
  await loadPhotos()

  if (uploadResults.value.every(r => r.status === 'done')) {
    resetUpload()
    showUpload.value = false
  }
}

// ── Альбомы ───────────────────────────────────────────────
const showNewAlbum = ref(false)
const newAlbumName = ref('')
const albumError   = ref('')

const renamingId   = ref(null)
const renameName   = ref('')

async function createAlbum() {
  if (!newAlbumName.value.trim()) return
  albumError.value = ''
  try {
    await albumsApi.create(newAlbumName.value.trim())
    newAlbumName.value = ''
    showNewAlbum.value = false
    await loadAlbums()
  } catch (e) {
    albumError.value = e.response?.data?.detail || 'Ошибка создания альбома'
  }
}

async function deleteAlbum(id) {
  if (!confirm('Удалить альбом? Фотографии останутся без альбома.')) return
  await albumsApi.delete(id)
  if (selectedAlbum.value === id) selectedAlbum.value = null
  await Promise.all([loadAlbums(), loadPhotos()])
}

function startRename(album) {
  renamingId.value = album.id
  renameName.value = album.name
}

async function commitRename(id) {
  if (!renameName.value.trim()) return
  await albumsApi.rename(id, renameName.value.trim())
  renamingId.value = null
  await loadAlbums()
}
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="main-content">

      <!-- ── Sidebar ─────────────────────────────────────── -->
      <aside class="sidebar">
        <div class="sidebar-title">Альбомы</div>

        <button
          class="sidebar-item"
          :class="{ active: !selectedAlbum }"
          @click="selectAlbum(null)"
        >
          📷 Все фотографии
          <span class="item-count" v-if="!selectedAlbum">{{ photos.length }}</span>
        </button>

        <button
          class="sidebar-item"
          :class="{ active: selectedAlbum === 'NO_ALBUM' }"
          @click="selectAlbum('NO_ALBUM')"
        >
          📂 Фото без папки
          <span class="item-count" v-if="selectedAlbum === 'NO_ALBUM'">{{ photos.length }}</span>
        </button>

        <template v-for="album in albums" :key="album.id">
          <div class="sidebar-item" :class="{ active: selectedAlbum === album.id }" @click="selectAlbum(album.id)">
            <template v-if="renamingId === album.id">
              <input
                class="input"
                v-model="renameName"
                style="flex:1;padding:2px 6px;font-size:13px"
                @click.stop
                @keyup.enter="commitRename(album.id)"
                @keyup.escape="renamingId = null"
                @blur="commitRename(album.id)"
                v-focus
              />
            </template>
            <template v-else>
              📁 {{ album.name }}
              <div style="margin-left:auto;display:flex;gap:4px" @click.stop>
                <button class="btn btn-ghost btn-sm" style="padding:2px 6px" @click="startRename(album)">✏️</button>
                <button class="btn btn-ghost btn-sm" style="padding:2px 6px" @click="deleteAlbum(album.id)">🗑</button>
              </div>
            </template>
          </div>
        </template>

        <button class="btn btn-ghost btn-sm" style="margin-top:8px;width:100%" @click="showNewAlbum = true">
          + Новый альбом
        </button>
      </aside>

      <!-- ── Content ─────────────────────────────────────── -->
      <main class="content-area">

        <!-- Header -->
        <div class="content-header">
          <h2>{{ currentAlbumName }}</h2>
          <button class="btn btn-primary" @click="showUpload = true">+ Загрузить фото</button>
        </div>

        <!-- Selection bar -->
        <div v-if="selectionCount > 0" class="selection-bar">
          <span class="selection-count">Выбрано: <strong>{{ selectionCount }}</strong></span>
          <button class="btn btn-ghost btn-sm" @click="selectAll">Выбрать все</button>
          <button class="btn btn-ghost btn-sm" @click="showBulkMove = true">Переместить</button>
          <button class="btn btn-danger btn-sm" @click="bulkDelete">Удалить</button>
          <button class="btn btn-ghost btn-sm" style="margin-left:auto" @click="clearSelection">✕ Снять выделение</button>
        </div>

        <!-- Error -->
        <div v-if="loadError" class="error-msg" style="margin-bottom:16px">{{ loadError }}</div>

        <!-- States -->
        <div v-if="loading" class="empty-state">
          <div class="spinner" style="width:32px;height:32px"></div>
        </div>

        <div v-else-if="photos.length === 0" class="empty-state">
          <div class="empty-icon">🖼</div>
          <p>Нет фотографий</p>
          <button class="btn btn-primary" @click="showUpload = true">Загрузить первую</button>
        </div>

        <div v-else class="photo-grid">
          <PhotoCard
            v-for="photo in photos"
            :key="photo.id"
            :photo="photo"
            :albums="albums"
            :selected="selectedIds.has(photo.id)"
            @open="openPhoto"
            @toggle-select="toggleSelect"
            @deleted="id => { photos.value = photos.value.filter(p => p.id !== id); selectedIds.value.delete(id) }"
            @moved="loadPhotos"
          />
        </div>
      </main>
    </div>

    <!-- ── Upload modal ────────────────────────────────────── -->
    <div class="modal-overlay" v-if="showUpload" @click.self="!uploading && (showUpload = false, resetUpload())">
      <div class="modal" style="max-width:480px">
        <h3>Загрузить фото</h3>

        <div class="auth-form" style="margin-top:16px">
          <!-- File picker -->
          <div class="form-group" v-if="!uploading && !uploadDone">
            <label>Файлы (можно выбрать несколько)</label>
            <input
              class="input"
              type="file"
              accept="image/*"
              multiple
              @change="onFilesChange"
            />
          </div>

          <!-- File list preview -->
          <div v-if="uploadFiles.length && !uploading && !uploadDone" class="upload-file-list">
            <div
              v-for="(file, i) in uploadFiles"
              :key="i"
              class="upload-file-item"
            >
              <span class="upload-file-name">{{ file.name }}</span>
              <span class="upload-file-size">{{ (file.size / 1024 / 1024).toFixed(1) }} MB</span>
            </div>
          </div>

          <!-- Album selector -->
          <div class="form-group" v-if="!uploading && !uploadDone">
            <label>Альбом (необязательно)</label>
            <select class="input" v-model="uploadAlbum">
              <option value="">— Без альбома —</option>
              <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
            </select>
          </div>

          <!-- Progress -->
          <div v-if="uploading" class="upload-progress">
            <div class="spinner" style="width:20px;height:20px"></div>
            <span>Загружаем {{ uploadIdx + 1 }} из {{ uploadFiles.length }}: {{ uploadFiles[uploadIdx]?.name }}</span>
          </div>

          <!-- Results -->
          <div v-if="uploadDone" class="upload-file-list">
            <div
              v-for="(r, i) in uploadResults"
              :key="i"
              class="upload-file-item"
              :class="r.status"
            >
              <span class="upload-status-icon">
                {{ r.status === 'done' ? '✓' : '✗' }}
              </span>
              <span class="upload-file-name">{{ r.name }}</span>
              <span v-if="r.error" class="upload-file-error">{{ r.error }}</span>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button
            class="btn btn-ghost"
            :disabled="uploading"
            @click="showUpload = false; resetUpload()"
          >
            {{ uploadDone ? 'Закрыть' : 'Отмена' }}
          </button>
          <button
            v-if="!uploadDone"
            class="btn btn-primary"
            @click="doUpload"
            :disabled="uploading || !uploadFiles.length"
          >
            <span v-if="uploading" class="spinner" style="width:14px;height:14px"></span>
            {{ uploading ? 'Загружаем...' : `Загрузить${uploadFiles.length > 1 ? ` (${uploadFiles.length})` : ''}` }}
          </button>
          <button
            v-if="uploadDone && uploadResults.some(r => r.status === 'error')"
            class="btn btn-ghost"
            @click="resetUpload"
          >
            Загрузить ещё
          </button>
        </div>
      </div>
    </div>

    <!-- ── Bulk move modal ─────────────────────────────────── -->
    <div class="modal-overlay" v-if="showBulkMove" @click.self="showBulkMove = false">
      <div class="modal" style="max-width:360px">
        <h3>Переместить {{ selectionCount }} фото</h3>
        <div class="form-group" style="margin-bottom:0">
          <label>Альбом</label>
          <select class="input" v-model="bulkTarget">
            <option value="">— Без альбома —</option>
            <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showBulkMove = false">Отмена</button>
          <button class="btn btn-primary" @click="bulkMove" :disabled="bulkMoving">
            <span v-if="bulkMoving" class="spinner" style="width:14px;height:14px"></span>
            Переместить
          </button>
        </div>
      </div>
    </div>

    <!-- ── New album modal ────────────────────────────────── -->
    <div class="modal-overlay" v-if="showNewAlbum" @click.self="showNewAlbum = false">
      <div class="modal" style="max-width:360px">
        <h3>Новый альбом</h3>
        <div class="form-group" style="margin-bottom:0">
          <div v-if="albumError" class="error-msg" style="margin-bottom:12px">{{ albumError }}</div>
          <label>Название</label>
          <input class="input" v-model="newAlbumName" placeholder="Мой альбом" @keyup.enter="createAlbum" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showNewAlbum = false">Отмена</button>
          <button class="btn btn-primary" @click="createAlbum" :disabled="!newAlbumName.trim()">Создать</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// v-focus directive
export default {
  directives: {
    focus: { mounted: el => el.focus() },
  },
}
</script>
