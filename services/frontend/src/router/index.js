import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  { path: '/',                redirect: '/gallery' },
  { path: '/login',           component: () => import('../views/LoginView.vue'),          meta: { public: true  } },
  { path: '/register',        component: () => import('../views/RegisterView.vue'),       meta: { public: true  } },
  { path: '/confirm',         component: () => import('../views/ConfirmView.vue'),        meta: { public: true  } },
  { path: '/gallery',         component: () => import('../views/GalleryView.vue'),        meta: { public: false } },
  { path: '/profile',         component: () => import('../views/ProfileView.vue'),        meta: { public: false } },
  { path: '/change-password', component: () => import('../views/ChangePasswordView.vue'), meta: { public: false } },
  { path: '/admin',           component: () => import('../views/AdminView.vue'),          meta: { public: false, adminOnly: true } },
  { path: '/photo/:id',      component: () => import('../views/PhotoView.vue'),          meta: { public: false } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user) await auth.fetchMe()
  if (!to.meta.public && !auth.user) return '/login'
  if (to.meta.public && auth.user && to.path !== '/confirm') return '/gallery'
  if (to.meta.adminOnly && !auth.user?.roles?.includes('ADMIN')) return '/gallery'
})

export default router
