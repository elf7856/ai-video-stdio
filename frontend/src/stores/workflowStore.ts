/**
 * 工作流状态管理 - Zustand Store (稳定优化版)
 */

import { create } from 'zustand';
import { videosApi } from '../api';

const generateId = () => Math.random().toString(36).substring(2, 15);

const getInitialState = () => ({
  stage: 'ideation',
  conversation: [],
  creative: {
    topic: '', style: '专业', targetDuration: 60, shotCount: 6,
    narration: { enabled: false, voice: 'chinese_female', speed: 1.0 },
    pacing: 'balanced'
  },
  script: '',
  shots: [],
  timeline: { id: generateId(), tracks: [], duration: 0 },
  outputConfig: { aspectRatio: '16:9', resolution: '1080p' },
  taskStatus: null,
  flags: { isRunning: false }
});

export const useWorkflowStore = create<any>((set, get) => ({
  ...getInitialState(),

  setStage: (stage: string) => set({ stage }),
  setTopic: (topic: string) => set((s: any) => ({ creative: { ...s.creative, topic } })),
  setStyle: (style: string) => set((s: any) => ({ creative: { ...s.creative, style } })),
  setCreativeConfig: (cfg: any) => set((s: any) => ({ creative: { ...s.creative, ...cfg } })),
  setShots: (shots: any[]) => set({ shots }),
  setScript: (script: string) => set({ script }),
  setTaskStatus: (status: any) => set({ taskStatus: status }),
  setOutputConfig: (cfg: any) => set((s: any) => ({ outputConfig: { ...s.outputConfig, ...cfg } })),

  addMessage: (msg: any) => {
    const id = generateId();
    set((s: any) => ({ conversation: [...s.conversation, { ...msg, id, timestamp: new Date().toISOString() }] }));
    return id;
  },

  updateMessage: (id: string, updates: any) => set((s: any) => ({
    conversation: s.conversation.map((m: any) => m.id === id ? { ...m, ...updates } : m)
  })),

  syncTask: async (taskId: string) => {
    const state = get();
    if (state.flags.isRunning) return;
    set({ flags: { ...state.flags, isRunning: true } });

    let msgId = state.conversation.find((m: any) => m.role === 'assistant' && m.planning)?.id;
    if (!msgId) {
      msgId = get().addMessage({ role: 'assistant', content: '🤖 正在分析任务状态...' });
    }

    try {
      await videosApi.pollTaskStatus(taskId, (task) => {
        const cur = get();
        set({ taskStatus: { ...task, taskId } });
        
        if (task.script) set({ script: task.script });

        if (task.shots && task.shots.length > 0) {
          const mapped = task.shots.map((s: any) => ({
            ...s, imagePath: s.imagePath || s.image_path
          }));
          set({ shots: mapped });

          let content = task.script || '正在构思脚本内容...';
          
          if (task.status === 'waiting_confirmation') {
              content = `✅ 规划已完成！请在下方确认预览。\n\n${task.script}`;
          } else if (task.status === 'generating_videos') {
              content = `🎥 正在渲染镜头 (${mapped.filter(s=>s.videoPath).length}/${mapped.length})...`;
          } else if (task.status === 'completed') {
              content = `🎉 视频制作完成！`;
          }

          get().updateMessage(msgId!, {
            content,
            planning: {
              shots: mapped.map((s: any) => ({ sequence: s.sequence, description: s.prompt, duration: s.duration, imagePath: s.imagePath })),
              estimatedDuration: mapped.reduce((a: number, b: any) => a + b.duration, 0)
            }
          });
        }
        
        if (task.status === 'waiting_confirmation' && cur.stage !== 'editing') set({ stage: 'editing' });
        if (task.status === 'completed') set({ stage: 'completed' });
      }, 600000);
    } catch (err: any) {
      console.warn("Sync error:", err);
      // 如果任务不存在(404)，重置状态以便用户新建
      if (err.response && err.response.status === 404) {
          get().updateMessage(msgId!, { content: '❌ 之前的任务已过期或不存在，请重新开始。' });
          set({ stage: 'ideation', taskStatus: null, script: '', shots: [] });
      }
    } finally {
      set({ flags: { ...get().flags, isRunning: false } });
    }
  },

  initiateTask: async (navigate: any) => {
    const state = get();
    const requestData = {
      topic: state.creative.topic,
      style: state.creative.style,
      targetDuration: state.creative.targetDuration,
      shotCount: state.creative.shotCount,
      enableNarration: state.creative.narration.enabled,
      narrationVoice: state.creative.narration.voice
    };
    const { taskId } = await videosApi.createTask(requestData);
    navigate(`/editor/proj_${taskId}`, { replace: true });
    get().syncTask(taskId);
  },

  regenerateShot: async (sequence: number, prompt: string, duration: number) => {
    const state = get();
    const taskId = state.taskStatus?.taskId;
    if (!taskId) return;
    set((s: any) => ({ shots: s.shots.map((sh: any) => sh.sequence === sequence ? { ...sh, prompt, duration, status: 'regenerating' } : sh) }));
    await videosApi.regenerateShot(taskId, sequence, prompt, duration);
  },

  confirmAndGenerate: async () => {
    const state = get();
    const taskId = state.taskStatus?.taskId;
    if (!taskId) return;
    const options = { enable_narration: state.creative.narration.enabled, narration_voice: state.creative.narration.voice };
    
    // 寻找现有的助手消息进行状态更新，而不是新增
    const msgId = state.conversation.find((m: any) => m.role === 'assistant' && m.planning)?.id;
    if (msgId) {
        get().updateMessage(msgId, { content: '🚀 收到！正在为您渲染成品视频，请稍候...' });
    }
    
    await videosApi.confirmAndGenerate(taskId, state.script, state.shots, options);
  },

  reset: () => set(getInitialState())
}));
