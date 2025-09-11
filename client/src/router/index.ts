import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Dashboard.vue'),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/Registration.vue'),
    },
    {
      path: '/queue',
      name: 'queue',
      component: () => import('../views/Queues.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/JobHistory.vue'),
    },
    {
      path: '/emulator',
      name: 'emulator',
      component: () => import('../views/EmulatorView.vue'),
    },
    {
      path: '/issues',
      name: 'issues',
      component: () => import('../views/IssuesView.vue'),
    }
  ],
})

export default router
