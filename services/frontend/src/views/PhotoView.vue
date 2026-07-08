<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { photosApi } from '../api/index.js'

const route  = useRoute()
const router = useRouter()

// ── Данные ────────────────────────────────────────────────
const photos     = ref([])
const loading    = ref(true)
const imgLoading = ref(true)

const currentId = computed(() => route.params.id)

const currentIndex = computed(() =>
  photos.value.findIndex(p => p.id === currentId.value)
)
const currentPhoto = computed(() => photos.value[currentIndex.value] ?? null)
const prevPhoto    = computed(() =>
  currentIndex.value > 0 ? photos.value[currentIndex.value - 1] : null
)
const nextPhoto    = computed(() =>
  currentIndex.value < photos.value.length - 1
    ? photos.value[currentIndex.value + 1]
    : null
)

// ── Загрузка списка (для filmstrip + навигации) ───────────
async function loadPhotos() {
  loading.value = true
  try {
    const params = {}
    if (route.query.album_id)             params.album_id = route.query.album_id
    else if (route.query.no_album === 'true') params.no_album = true
    const { data } = await photosApi.list(params)
    photos.value = data
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPhotos()
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => window.removeEventListener('keydown', onKey))

// ── Навигация ─────────────────────────────────────────────
function goTo(photo) {
  router.replace({ path: `/photo/${photo.id}`, query: route.query })
}

function goBack() {
  router.push('/gallery')
}

function onKey(e) {
  if (e.key === 'ArrowLeft'  && prevPhoto.value) goTo(prevPhoto.value)
  if (e.key === 'ArrowRight' && nextPhoto.value) goTo(nextPhoto.value)
  if (e.key === 'Escape') goBack()
}

// Сбрасываем состояние загрузки изображения при смене фото
watch(currentId, () => { imgLoading.value = true })

// ── Filmstrip — прокрутка к текущему элементу ─────────────
const filmstripRef = ref(null)

watch(currentIndex, (idx) => {
  if (idx < 0) return
  nextTick(() => {
    const el = filmstripRef.value?.children[idx]
    el?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  })
}, { immediate: true })

// ── Утилиты ───────────────────────────────────────────────
function formatSize(bytes) {
  if (!bytes) return ''
  return bytes < 1024 * 1024
    ? `${Math.round(bytes / 1024)} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}
</script>

<template>
  <div class="pv">

    <!-- ── Шапка ──────────────────────────────────────────── -->
    <header class="pv-header">
      <button class="pv-back" @click="goBack" title="Назад (Esc)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <polyline points="10,3 5,8 10,13" stroke="currentColor" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Галерея
      </button>

      <div class="pv-title" :title="currentPhoto?.title">
        {{ currentPhoto?.title ?? '' }}
      </div>

      <div class="pv-counter" v-if="photos.length">
        {{ currentIndex + 1 }}&nbsp;/&nbsp;{{ photos.length }}
      </div>
    </header>

    <!-- ── Загрузка списка ────────────────────────────────── -->
    <div v-if="loading" class="pv-center">
      <div class="pv-spinner"></div>
    </div>

    <template v-else>

      <!-- ── Главная область просмотра ─────────────────────── -->
      <div class="pv-stage">

        <!-- Стрелка влево -->
        <button
          class="pv-arrow pv-arrow-l"
          :disabled="!prevPhoto"
          @click="prevPhoto && goTo(prevPhoto)"
          title="Предыдущее (←)"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <polyline points="13,4 7,10 13,16" stroke="currentColor" stroke-width="2.5"
                      stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <!-- Изображение -->
        <div class="pv-img-wrap">
          <div v-show="imgLoading" class="pv-center">
            <div class="pv-spinner"></div>
          </div>
          <img
            v-if="currentPhoto?.url"
            :key="currentPhoto.id"
            :src="currentPhoto.url"
            :alt="currentPhoto.title"
            class="pv-img"
            v-show="!imgLoading"
            @load="imgLoading = false"
            @error="imgLoading = false"
            draggable="false"
          />
        </div>

        <!-- Стрелка вправо -->
        <button
          class="pv-arrow pv-arrow-r"
          :disabled="!nextPhoto"
          @click="nextPhoto && goTo(nextPhoto)"
          title="Следующее (→)"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <polyline points="7,4 13,10 7,16" stroke="currentColor" stroke-width="2.5"
                      stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <!-- ── Инфо-строка ────────────────────────────────────── -->
      <div class="pv-info" v-if="currentPhoto">
        <span class="pv-info-size">{{ formatSize(currentPhoto.size_bytes) }}</span>
        <span class="pv-info-sep">·</span>
        <span class="pv-info-type">{{ currentPhoto.mime_type }}</span>
        <span v-if="currentPhoto.exif_date" class="pv-info-sep">·</span>
        <span v-if="currentPhoto.exif_date" class="pv-info-date">
          📷 {{ formatDate(currentPhoto.exif_date) }}
        </span>
      </div>

      <!-- ── Filmstrip ───────────────────────────────────────── -->
      <div class="pv-filmstrip" ref="filmstripRef">
        <div
          v-for="photo in photos"
          :key="photo.id"
          class="pv-thumb"
          :class="{ active: photo.id === currentId }"
          @click="goTo(photo)"
          :title="photo.title"
        >
          <img
            v-if="photo.url"
            :src="photo.url"
            :alt="photo.title"
            loading="lazy"
          />
          <div v-else class="pv-thumb-ph">🖼</div>
        </div>
      </div>

    </template>
  </div>
</template>

<style scoped>
/* ── Корневой контейнер ───────────────────────────────────── */
.pv {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #111;
  color: #e5e7eb;
  overflow: hidden;
}

/* ── Шапка ───────────────────────────────────────────────── */
.pv-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  height: 52px;
  background: #1a1a1a;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}

.pv-back {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid #383838;
  border-radius: 6px;
  color: #a0a0a0;
  font-size: 13px;
  padding: 5px 10px;
  cursor: pointer;
  transition: background .12s, color .12s;
  white-space: nowrap;
  flex-shrink: 0;
}
.pv-back:hover { background: #2a2a2a; color: #e5e7eb; }

.pv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 500;
  color: #e5e7eb;
  text-align: center;
}

.pv-counter {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── Главная область ─────────────────────────────────────── */
.pv-stage {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 0;
}

.pv-img-wrap {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.pv-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
}

/* ── Стрелки ─────────────────────────────────────────────── */
.pv-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  background: rgba(0,0,0,.5);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  color: #e5e7eb;
  width: 48px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background .12s, opacity .12s;
}
.pv-arrow:hover:not(:disabled) { background: rgba(0,0,0,.75); }
.pv-arrow:disabled { opacity: .18; cursor: default; }
.pv-arrow-l { left: 12px; }
.pv-arrow-r { right: 12px; }

/* ── Инфо-строка ─────────────────────────────────────────── */
.pv-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: #161616;
  border-top: 1px solid #2a2a2a;
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
}
.pv-info-sep { color: #383838; }

/* ── Filmstrip ───────────────────────────────────────────── */
.pv-filmstrip {
  display: flex;
  gap: 3px;
  padding: 6px 8px;
  background: #0d0d0d;
  border-top: 1px solid #2a2a2a;
  overflow-x: auto;
  flex-shrink: 0;
  height: 82px;
  align-items: center;

  scrollbar-width: thin;
  scrollbar-color: #333 transparent;
}
.pv-filmstrip::-webkit-scrollbar { height: 3px; }
.pv-filmstrip::-webkit-scrollbar-track { background: transparent; }
.pv-filmstrip::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

.pv-thumb {
  width: 68px;
  height: 64px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  background: #222;
  transition: border-color .12s, transform .12s, opacity .12s;
  opacity: .65;
}
.pv-thumb.active {
  border-color: #e5e7eb;
  transform: scale(1.06);
  opacity: 1;
}
.pv-thumb:hover:not(.active) {
  border-color: rgba(255,255,255,.35);
  opacity: .9;
}
.pv-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.pv-thumb-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #444;
}

/* ── Спиннер ─────────────────────────────────────────────── */
.pv-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pv-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(255,255,255,.12);
  border-top-color: rgba(255,255,255,.7);
  border-radius: 50%;
  animation: pv-spin .7s linear infinite;
}
@keyframes pv-spin { to { transform: rotate(360deg); } }
</style>
