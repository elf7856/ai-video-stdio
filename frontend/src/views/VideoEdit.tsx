import { defineComponent, ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ElRow, ElCol, ElCard, ElDescriptions, ElDescriptionsItem, 
  ElForm, ElFormItem, ElInput, ElButton 
} from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { videoApi } from '../services/api'
import type { Video, EditForm, ApiResponse } from '../types'
import './VideoEdit.css'

export default defineComponent({
  name: 'VideoEdit',
  setup() {
    const route = useRoute()

    // 响应式数据
    const video = ref<Video | null>(null)
    const processing = ref(false)
    const editResult = ref<ApiResponse | null>(null)

    // 表单数据
    const editForm = reactive<EditForm>({
      instruction: ''
    })

    // 方法
    const loadVideo = async (): Promise<void> => {
      try {
        const videoId = Number(route.params.id)
        if (isNaN(videoId)) {
          ElMessage.error('无效的视频ID')
          return
        }
        
        const data = await videoApi.getVideo(videoId)
        video.value = data
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '加载失败'
        ElMessage.error('加载视频信息失败：' + errorMessage)
      }
    }

    const processEdit = async (): Promise<void> => {
      if (!editForm.instruction.trim()) {
        ElMessage.error('请输入编辑指令')
        return
      }
      
      if (!video.value) {
        ElMessage.error('视频信息未加载')
        return
      }
      
      processing.value = true
      try {
        const response = await videoApi.editVideo(video.value.id, editForm.instruction)
        
        editResult.value = response
        if (response.success) {
          ElMessage.success('编辑处理完成！')
        } else {
          ElMessage.error('编辑失败：' + (response.error || '未知错误'))
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '编辑失败'
        ElMessage.error('编辑失败：' + errorMessage)
      } finally {
        processing.value = false
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

    // 生命周期
    onMounted(() => {
      loadVideo()
    })

    return () => (
      <div class="video-edit">
        <ElRow gutter={20}>
          <ElCol span={24}>
            <ElCard>
              {{
                header: () => <h2>✏️ 视频编辑</h2>,
                default: () => (
                  <div>
                    {video.value && (
                      <div class="video-info">
                        <ElDescriptions column={2} border>
                          <ElDescriptionsItem label="标题">{video.value.title}</ElDescriptionsItem>
                          <ElDescriptionsItem label="时长">{formatDuration(video.value.duration)}</ElDescriptionsItem>
                          <ElDescriptionsItem label="分辨率">{video.value.resolution}</ElDescriptionsItem>
                          <ElDescriptionsItem label="文件大小">{formatFileSize(video.value.file_size)}</ElDescriptionsItem>
                        </ElDescriptions>
                      </div>
                    )}
                    
                    <div class="edit-section">
                      <h3>🎯 自然语言编辑</h3>
                      <p>使用自然语言描述你想要对视频进行的编辑操作</p>
                      
                      <ElForm model={editForm} labelWidth="120px">
                        <ElFormItem label="编辑指令">
                          <ElInput
                            v-model={editForm.instruction}
                            type="textarea"
                            rows={4}
                            placeholder="例如：在视频开头添加一个标题，内容是'欢迎观看'"
                          />
                        </ElFormItem>
                        <ElFormItem>
                          <ElButton type="primary" onClick={processEdit} loading={processing.value}>
                            <MagicStick />
                            开始编辑
                          </ElButton>
                        </ElFormItem>
                      </ElForm>
                    </div>
                    
                    {editResult.value && (
                      <div class="edit-result">
                        <h3>📋 编辑结果</h3>
                        <ElCard>
                          {{
                            header: () => <span>编辑分析</span>,
                            default: () => (
                              <ElDescriptions column={1} border>
                                <ElDescriptionsItem label="编辑类型">{editResult.value?.edit_type}</ElDescriptionsItem>
                                <ElDescriptionsItem label="指令分析">{editResult.value?.instruction_analysis}</ElDescriptionsItem>
                                <ElDescriptionsItem label="内容描述">{editResult.value?.content_description}</ElDescriptionsItem>
                              </ElDescriptions>
                            )
                          }}
                        </ElCard>
                      </div>
                    )}
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