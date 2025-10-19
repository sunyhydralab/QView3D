import { createRouter, createWebHistory } from 'vue-router'
import { DEBUG_MODE } from '@/composables/useIPSettings'
import { addToast } from '@/components/Toast.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Dashboard.vue'),
      meta: { title: 'Dashboard', icon: 'fas fa-home' }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/Registration.vue'),
      meta: { title: 'Registration', icon: 'fas fa-plus-circle' }
    },
    {
      path: '/queue',
      name: 'queue',
      component: () => import('../views/Queues.vue'),
      meta: { title: 'Queues', icon: 'fas fa-list' }
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/JobHistory.vue'),
      meta: { title: 'Job History', icon: 'fas fa-history' }
    },
    {
      path: '/issues',
      name: 'issues',
      component: () => import('../views/Issues.vue'),
      meta: { title: 'Issues', icon: 'fas fa-exclamation-triangle' }
    },
    {
      path: '/emulator',
      name: 'emulator',
      component: () => import('../views/EmulatorView.vue'),
      meta: { title: 'Emulator', icon: 'fas fa-microchip', requiresDebug: true }
    }
  ],
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresDebug && !DEBUG_MODE.value) {
    addToast('Debug mode is required to access this page', 'warning')
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
