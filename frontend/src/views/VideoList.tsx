import { defineComponent, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ElRow, ElCol, ElCard, ElTable, ElTableColumn, ElButton, 
  ElPagination 
} from 'element-plus'
import { Plus, View, Edit, Download } from '@element-plus/icons-vue'
import { videoApi } from '../services/api'
import type { Video, PaginationParams } from '../types'
import './VideoList.css'

export default defineComponent({
  name: 'VideoList',
  setup() {
    const router = useRouter()

    // 响应式数据
    const videos = ref<Video[]>([])
    const loading = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(0)

    // 方法
    const loadVideos = async (): Promise<void> => {
      loading.value = true
      try {
        const params: PaginationParams = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        const data = await videoApi.getVideos(params)
        videos.value = data
        total.value = data.length // 这里应该从后端获取总数
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '加载失败'
        ElMessage.error('加载视频列表失败：' + errorMessage)
      } finally {
        loading.value = false
      }
    }

    const formatDuration = (seconds?: number): string => {
      if (!seconds) return '未知'
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    }

    const formatFileSize = (bytes?: number): string => {
      if (!bytes) return '未知'
      const mb = bytes / 1024 / 1024
      return `${mb.toFixed(2)} MB`
    }

    const formatDate = (dateString?: string): string => {
      if (!dateString) return '未知'
      return new Date(dateString).toLocaleString()
    }

    const viewVideo = (video: Video): void => {
      // 查看视频详情
      console.log('查看视频:', video)
      // 可以跳转到详情页面
      // router.push(`/video/${video.id}`)
    }

    const editVideo = (video: Video): void => {
      // 跳转到编辑页面
      router.push(`/edit/${video.id}`)
    }

    const downloadVideo = async (video: Video): Promise<void> => {
      try {
        const blob = await videoApi.downloadVideo(video.id)
        
        // 创建下载链接
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', video.filename)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('下载开始')
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '下载失败'
        ElMessage.error('下载失败：' + errorMessage)
      }
    }

    const handleSizeChange = (val: number): void => {
      pageSize.value = val
      loadVideos()
    }

    const handleCurrentChange = (val: number): void => {
      currentPage.value = val
      loadVideos()
    }

    // 生命周期
    onMounted(() => {
      loadVideos()
    })

    return () => (
      <div class="video-list">
        <ElRow gutter={20}>
          <ElCol span={24}>
            <ElCard>
              {{
                header: () => (
                  <div class="card-header">
                    <h2>📹 视频列表</h2>
                    <ElButton type="primary" onClick={() => router.push('/download')}>
                      <Plus />
                      添加视频
                    </ElButton>
                  </div>
                ),
                default: () => (
                  <div>
                    <ElTable data={videos.value} loading={loading.value} style="width: 100%">
                      <ElTableColumn prop="id" label="ID" width={80} />
                      <ElTableColumn prop="title" label="标题" minWidth={200} />
                      <ElTableColumn prop="duration" label="时长" width={100}>
                        {{
                          default: ({ row }: { row: Video }) => formatDuration(row.duration)
                        }}
                      </ElTableColumn>
                      <ElTableColumn prop="resolution" label="分辨率" width={120} />
                      <ElTableColumn prop="file_size" label="文件大小" width={100}>
                        {{
                          default: ({ row }: { row: Video }) => formatFileSize(row.file_size)
                        }}
                      </ElTableColumn>
                      <ElTableColumn prop="created_at" label="创建时间" width={180}>
                        {{
                          default: ({ row }: { row: Video }) => formatDate(row.created_at)
                        }}
                      </ElTableColumn>
                      <ElTableColumn label="操作" width={200} fixed="right">
                        {{
                          default: ({ row }: { row: Video }) => (
                            <div>
                              <ElButton size="small" onClick={() => viewVideo(row)}>
                                <View />
                                查看
                              </ElButton>
                              <ElButton size="small" type="primary" onClick={() => editVideo(row)}>
                                <Edit />
                                编辑
                              </ElButton>
                              <ElButton size="small" type="success" onClick={() => downloadVideo(row)}>
                                <Download />
                                下载
                              </ElButton>
                            </div>
                          )
                        }}
                      </ElTableColumn>
                    </ElTable>
                    
                    <div class="pagination">
                      <ElPagination
                        v-model:currentPage={currentPage.value}
                        v-model:pageSize={pageSize.value}
                        pageSizes={[10, 20, 50, 100]}
                        total={total.value}
                        layout="total, sizes, prev, pager, next, jumper"
                        onSizeChange={handleSizeChange}
                        onCurrentChange={handleCurrentChange}
                      />
                    </div>
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