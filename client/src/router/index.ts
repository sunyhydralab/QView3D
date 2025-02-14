import { createRouter, createWebHashHistory } from 'vue-router'
import MainView from '@/views/MainView.vue'
import QueueViewVue from '@/views/QueueView.vue'
import RegisteredViewVue from '@/views/RegisteredView.vue'
import SubmitJobVue from '@/components/SubmitJobModal.vue'
import JobHistoryVue from '@/views/JobHistory.vue'
import ErrorView from '@/views/ErrorView.vue'
import EmulatorView from '@/views/EmulatorView.vue'

const routes = [
  {
    path: '/',
    name: 'MainView',
    component: MainView
  },
  {
    path: '/queue',
    name: 'QueueViewVue',
    component: QueueViewVue
  },
  {
    path: '/registration',
    name: 'RegisteredViewVue',
    component: RegisteredViewVue
  },
  {
    path: '/submit/:job?/:printer?',
    name: 'SubmitJobVue',
    component: SubmitJobVue
  },
  {
    path: '/history',
    name: 'JobHistoryVue',
    component: JobHistoryVue
  }, 
  {
    path: '/error',
    name: 'ErrorView',
    component: ErrorView
  },
  {
    path: '/emulator',
    name: 'EmulatorView',
    component: EmulatorView
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router