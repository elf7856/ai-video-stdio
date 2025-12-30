import { defineComponent } from 'vue'
import { ElRow, ElCol, ElCard, ElIcon } from 'element-plus'
import { Download, VideoPlay, Edit } from '@element-plus/icons-vue'
import './Home.css'

export default defineComponent({
  name: 'Home',
  setup() {
    return () => (
      <div class="home">
        <ElRow gutter={20}>
          <ElCol span={24}>
            <ElCard class="welcome-card">
              {{
                header: () => (
                  <div class="card-header">
                    <h1>🎬 欢迎使用视频创作平台</h1>
                  </div>
                ),
                default: () => (
                  <div class="welcome-content">
                    <p>这是一个强大的视频创作平台，支持从多个平台下载视频，并提供智能分析和编辑功能。</p>
                    <ElRow gutter={20} class="feature-cards">
                      <ElCol span={8}>
                        <ElCard class="feature-card">
                          <ElIcon size={40} color="#409EFF">
                            <Download />
                          </ElIcon>
                          <h3>视频下载</h3>
                          <p>支持YouTube、B站、TikTok等多个平台的视频下载</p>
                        </ElCard>
                      </ElCol>
                      <ElCol span={8}>
                        <ElCard class="feature-card">
                          <ElIcon size={40} color="#67C23A">
                            <VideoPlay />
                          </ElIcon>
                          <h3>智能分析</h3>
                          <p>AI分析视频内容，自动生成标签和摘要</p>
                        </ElCard>
                      </ElCol>
                      <ElCol span={8}>
                        <ElCard class="feature-card">
                          <ElIcon size={40} color="#E6A23C">
                            <Edit />
                          </ElIcon>
                          <h3>视频编辑</h3>
                          <p>使用自然语言指令编辑视频内容</p>
                        </ElCard>
                      </ElCol>
                    </ElRow>
                  </div>
                )
              }}
            </ElCard>
          </ElCol>
        </ElRow>
      </div>
    )
  }
}) 