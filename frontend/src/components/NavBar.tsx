import { defineComponent } from 'vue'
import { ElMenu, ElMenuItem } from 'element-plus'
import { House, Download, VideoPlay } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import './NavBar.css'

export default defineComponent({
  name: 'NavBar',
  setup() {
    const router = useRouter()

    return () => (
      <div class="nav-bar">
        <div class="nav-left">
          <h2>🎬 视频创作平台</h2>
        </div>
        <div class="nav-right">
          <ElMenu mode="horizontal" router={true} backgroundColor="#409EFF" textColor="#fff" activeTextColor="#ffd04b">
            <ElMenuItem index="/">
              <House />
              首页
            </ElMenuItem>
            <ElMenuItem index="/download">
              <Download />
              视频下载
            </ElMenuItem>
            <ElMenuItem index="/videos">
              <VideoPlay />
              视频列表
            </ElMenuItem>
          </ElMenu>
        </div>
      </div>
    )
  }
}) 