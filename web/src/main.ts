import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import App from './App.vue'
import router from './router'
import { pinia } from './store'
import '@/assets/styles/index.css'
import 'ant-design-vue/dist/reset.css'
import 'highlight.js/styles/github.css'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(Antd)
app.mount('#app')
