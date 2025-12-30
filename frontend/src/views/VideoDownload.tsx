import { defineComponent, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile, type UploadInstance } from 'element-plus'
import { 
  ElRow, ElCol, ElCard, ElTabs, ElTabPane, ElForm, ElFormItem, 
  ElInput, ElSwitch, ElButton, ElAlert, ElUpload, ElResult, 
  ElDescriptions, ElDescriptionsItem 
} from 'element-plus'
import { Download, Upload } from '@element-plus/icons-vue'
import { videoApi } from '../services/api'
import type { DownloadResult, UrlDownloadForm, CookiesDownloadForm } from '../types'
import './VideoDownload.css'

export default defineComponent({
  name: 'VideoDownload',
  setup() {
    const router = useRouter()

    // 响应式数据
    const activeTab = ref<'url' | 'cookies'>('url')
    const urlLoading = ref(false)
    const cookiesLoading = ref(false)
    const downloadResult = ref<DownloadResult | null>(null)
    const cookiesFile = ref<File | null>(null)
    const cookiesUploadRef = ref<UploadInstance>()

    // 表单数据
    const urlForm = reactive<UrlDownloadForm>({
      url: '',
      autoAnalyze: true
    })

    const cookiesForm = reactive<CookiesDownloadForm>({
      url: ''
    })

    // 方法
    const downloadFromUrl = async (): Promise<void> => {
      if (!urlForm.url.trim()) {
        ElMessage.error('请输入视频URL')
        return
      }
      
      urlLoading.value = true
      try {
        const response = await videoApi.processFromUrl(urlForm.url, urlForm.autoAnalyze)
        
        if (response.success) {
          downloadResult.value = {
            success: true,
            title: response.data?.title,
            platform: response.data?.platform,
            duration: response.data?.duration,
            file_path: response.data?.file_path
          }
          ElMessage.success('视频下载成功！')
        } else {
          downloadResult.value = {
            success: false,
            error: response.error || '下载失败'
          }
          ElMessage.error('下载失败：' + (response.error || '未知错误'))
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '下载失败'
        downloadResult.value = {
          success: false,
          error: errorMessage
        }
        ElMessage.error('下载失败：' + errorMessage)
      } finally {
        urlLoading.value = false
      }
    }

    const handleCookiesFileChange = (file: UploadFile): void => {
      if (file.raw) {
        cookiesFile.value = file.raw
      }
    }

    const downloadWithCookies = async (): Promise<void> => {
      if (!cookiesForm.url.trim()) {
        ElMessage.error('请输入视频URL')
        return
      }
      
      if (!cookiesFile.value) {
        ElMessage.error('请选择Cookies文件')
        return
      }
      
      cookiesLoading.value = true
      try {
        // 读取cookies文件并转为base64
        const cookiesContent = await readFileAsBase64(cookiesFile.value)
        const result = await videoApi.downloadWithCookies(cookiesForm.url, cookiesContent)
        
        downloadResult.value = result
        if (result.success) {
          ElMessage.success('视频下载成功！')
        } else {
          ElMessage.error('下载失败：' + (result.error || '未知错误'))
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '下载失败'
        downloadResult.value = {
          success: false,
          error: errorMessage
        }
        ElMessage.error('下载失败：' + errorMessage)
      } finally {
        cookiesLoading.value = false
      }
    }

    const readFileAsBase64 = (file: File): Promise<string> => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          if (typeof reader.result === 'string') {
            resolve(btoa(reader.result))
          } else {
            reject(new Error('文件读取失败'))
          }
        }
        reader.onerror = () => reject(new Error('文件读取失败'))
        reader.readAsText(file)
      })
    }

    const formatDuration = (seconds?: number): string => {
      if (!seconds) return '未知'
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    }

    const viewVideoList = (): void => {
      router.push('/videos')
    }

    return () => (
      <div class="video-download">
        <ElRow gutter={20}>
          <ElCol span={24}>
            <ElCard>
              {{
                header: () => <h2>📥 视频下载</h2>,
                default: () => (
                  <ElTabs v-model={activeTab.value} type="card">
                    <ElTabPane label="URL下载" name="url">
                      <div class="download-section">
                        <ElForm model={urlForm} labelWidth="120px">
                          <ElFormItem label="视频URL">
                            <ElInput 
                              v-model={urlForm.url} 
                              placeholder="请输入视频链接（支持YouTube、B站、TikTok等）"
                              clearable
                            />
                          </ElFormItem>
                          <ElFormItem label="自动分析">
                            <ElSwitch v-model={urlForm.autoAnalyze} />
                          </ElFormItem>
                          <ElFormItem>
                            <ElButton type="primary" onClick={downloadFromUrl} loading={urlLoading.value}>
                              <Download />
                              开始下载
                            </ElButton>
                          </ElFormItem>
                        </ElForm>
                      </div>
                    </ElTabPane>
                    
                    <ElTabPane label="Cookies下载" name="cookies">
                      <div class="download-section">
                        <ElAlert
                          title="Cookies下载说明"
                          type="info"
                          closable={false}
                          showIcon
                        >
                          <p>某些平台（如YouTube）需要登录验证，请先导出cookies文件：</p>
                          <ol>
                            <li>安装浏览器插件（如"Get cookies.txt"）</li>
                            <li>访问目标网站并登录</li>
                            <li>导出cookies.txt文件</li>
                            <li>上传cookies文件并输入视频URL</li>
                          </ol>
                        </ElAlert>
                        
                        <ElForm model={cookiesForm} labelWidth="120px" style="margin-top: 20px;">
                          <ElFormItem label="视频URL">
                            <ElInput 
                              v-model={cookiesForm.url} 
                              placeholder="请输入视频链接"
                              clearable
                            />
                          </ElFormItem>
                          <ElFormItem label="Cookies文件">
                            <ElUpload
                              ref={cookiesUploadRef}
                              autoUpload={false}
                              onChange={handleCookiesFileChange}
                              limit={1}
                              accept=".txt"
                            >
                              <ElButton type="primary">
                                <Upload />
                                选择Cookies文件
                              </ElButton>
                              <template #tip>
                                <div class="el-upload__tip">
                                  只能上传txt文件，且不超过1MB
                                </div>
                              </template>
                            </ElUpload>
                          </ElFormItem>
                          <ElFormItem>
                            <ElButton type="success" onClick={downloadWithCookies} loading={cookiesLoading.value}>
                              <Download />
                              使用Cookies下载
                            </ElButton>
                          </ElFormItem>
                        </ElForm>
                      </div>
                    </ElTabPane>
                  </ElTabs>
                )
              }}
            </ElCard>
          </ElCol>
        </ElRow>
        
        {/* 下载结果 */}
        {downloadResult.value && (
          <ElRow gutter={20} style="margin-top: 20px;">
            <ElCol span={24}>
              <ElCard>
                {{
                  header: () => <h3>📋 下载结果</h3>,
                  default: () => (
                    <div>
                      {downloadResult.value?.success ? (
                        <ElResult icon="success" title="下载成功">
                          {{
                            extra: () => (
                              <div>
                                <ElDescriptions column={2} border>
                                  <ElDescriptionsItem label="标题">{downloadResult.value?.title}</ElDescriptionsItem>
                                  <ElDescriptionsItem label="平台">{downloadResult.value?.platform}</ElDescriptionsItem>
                                  <ElDescriptionsItem label="时长">{formatDuration(downloadResult.value?.duration)}</ElDescriptionsItem>
                                  <ElDescriptionsItem label="文件路径">{downloadResult.value?.file_path}</ElDescriptionsItem>
                                </ElDescriptions>
                                <div style="margin-top: 20px;">
                                  <ElButton type="primary" onClick={viewVideoList}>查看视频列表</ElButton>
                                </div>
                              </div>
                            )
                          }}
                        </ElResult>
                      ) : (
                        <ElResult icon="error" title="下载失败">
                          {{
                            extra: () => (
                              <div>
                                <p>{downloadResult.value?.error}</p>
                                <ElButton type="primary" onClick={() => downloadResult.value = null}>重试</ElButton>
                              </div>
                            )
                          }}
                        </ElResult>
                      )}
                    </div>
                  )
                }}
              </ElCard>
            </ElCol>
          </ElRow>
        )}
      </div>
    )
  }
}) 