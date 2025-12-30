import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home'
import VideoDownload from '../views/VideoDownload'
import VideoList from '../views/VideoList'
import VideoEdit from '../views/VideoEdit'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/download',
    name: 'VideoDownload',
    component: VideoDownload
  },
  {
    path: '/videos',
    name: 'VideoList',
    component: VideoList
  },
  {
    path: '/edit/:id',
    name: 'VideoEdit',
    component: VideoEdit
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 