<script setup>
import { ref } from 'vue'
import { photosApi } from '../api/index.js'

const props = defineProps({
  photo:    { type: Object,  required: true },
  albums:   { type: Array,   default: () => [] },
  selected: { type: Boolean, default: false },
})
const emit = defineEmits(['deleted', 'moved', 'toggle-select', 'open'])

const showMove    = ref(false)
const targetAlbum = ref('')

async function deletePhoto() {
  if (!confirm(`Удалить «${props.photo.title}»?`)) return
  await photosApi.delete(props.photo.id)
  emit('deleted', props.photo.id)
}

async function movePhoto() {
  await photosApi.move(props.photo.id, targetAlbum.value || null)
  showMove.value = false
  emit('moved')
}

function formatSize(bytes) {
  if (!bytes) return ''
  return bytes < 1024 * 1024
    ? `${Math.round(bytes / 1024)} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div class="photo-card card" :class="{ 'is-selected': selected }">
    <!-- Чекбокс выделения (видим при наведении или когда выбрано) -->
    <div
      class="photo-check"
      :class="{ 'is-checked': selected }"
      @click.stop="emit('toggle-select', photo.id)"
      :title="selected ? 'Снять выделение' : 'Выбрать'"
    >
      <svg v-if="selected" width="12" height="12" viewBox="0 0 12 12" fill="none">
        <polyline points="2,6 5,9 10,3" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <!-- Превью — клик открывает просмотрщик -->
    <img
      v-if="photo.url"
      :src="photo.url"
      :alt="photo.title"
      class="photo-img"
      loading="lazy"
      @click.stop="emit('open', photo.id)"
    />
    <div v-else class="photo-placeholder" @click.stop="emit('open', photo.id)">🖼</div>

    <!-- Инфо -->
    <div class="photo-info">
      <div class="photo-title" :title="photo.title">{{ photo.title }}</div>
      <div class="photo-meta">{{ formatSize(photo.size_bytes) }}</div>
      <div class="photo-actions">
        <button class="btn btn-ghost btn-sm" @click.stop="showMove = true">Переместить</button>
        <button class="btn btn-danger btn-sm" @click.stop="deletePhoto">Удалить</button>
      </div>
    </div>
  </div>

  <!-- Модалка перемещения -->
  <div class="modal-overlay" v-if="showMove" @click.self="showMove = false">
    <div class="modal" style="max-width:360px">
      <h3>Переместить фото</h3>
      <div class="form-group">
        <label>Альбом</label>
        <select class="input" v-model="targetAlbum">
          <option value="">— Без альбома —</option>
          <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showMove = false">Отмена</button>
        <button class="btn btn-primary" @click="movePhoto">Переместить</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.photo-check {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,.85);
  background: rgba(0,0,0,.25);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity .15s, background .15s, border-color .15s;
  z-index: 2;
  backdrop-filter: blur(2px);
}
.photo-card:hover .photo-check,
.photo-check.is-checked {
  opacity: 1;
}
.photo-check.is-checked {
  background: var(--primary);
  border-color: var(--primary);
}

.photo-card { position: relative; }
.photo-card.is-selected {
  outline: 2px solid var(--primary);
  outline-offset: 1px;
}
.photo-card.is-selected .photo-img,
.photo-card.is-selected .photo-placeholder {
  opacity: .85;
}
</style>
