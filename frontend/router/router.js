import { createWebHistory, createRouter } from 'vue-router'
import Editor from '../views/Editor.vue'
import Authentication from '../views/Authentication.vue'
import Documents from '../views/Documents.vue'
import Collaboration from '../views/Collaboration.vue'
import LandingPage from '../views/LandingPage.vue'

const routes = [
  {
    path: '/editor/:document_id',
    name: 'editor',
    component: Editor,
    props: true,
  },
  {path: '/', name: 'landingpage', component: LandingPage},
  { path: '/auth', name: 'auth', component: Authentication },
  { path: '/documents', name: 'documents', component: Documents },
  { path: '/collaboration', name: 'collaboration', component: Collaboration },
  
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})