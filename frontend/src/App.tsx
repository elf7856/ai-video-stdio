import { defineComponent } from 'vue'
import { ElContainer, ElHeader, ElMain } from 'element-plus'
import NavBar from './components/NavBar'
import { RouterView } from 'vue-router'
import './App.css'

export default defineComponent({
  name: 'App',
  setup() {
    return () => (
      <div id="app">
        <ElContainer>
          <ElHeader>
            <NavBar />
          </ElHeader>
          <ElMain>
            <RouterView />
          </ElMain>
        </ElContainer>
      </div>
    )
  }
}) 