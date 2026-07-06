import { create } from 'zustand'
import toast from 'react-hot-toast'
import { axiosInstance } from '../lib/axios'

export const useAppStore = create((set, get) => ({
  // pipeline / session state
  session: null,          // { session_id, title, transcript, summary, action_items, key_decisions, questions }
  isProcessing: false,

  // chat (RAG) state
  messages: [],           // [{ _id, role: 'user' | 'assistant', text, createdAt }]
  isChatLoading: false,

  processSource: async ({ source, translate, file }) => {
    set({ isProcessing: true, messages: [] })
    try {
      let res
      if (file) {
        const form = new FormData()
        form.append('file', file)
        form.append('translate', translate ? 'true' : 'false')
        res = await axiosInstance.post('/process', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      } else {
        res = await axiosInstance.post('/process', { source, translate })
      }
      set({ session: res.data })
      toast.success('Video processed successfully')
      return res.data
    } catch (err) {
      const msg = err?.response?.data?.error || 'Failed to process source'
      toast.error(msg)
      throw err
    } finally {
      set({ isProcessing: false })
    }
  },

clearSession: async () => {
  const currentSession = get().session

  try {
    if (currentSession?.session_id) {
      await axiosInstance.post('/clear', { session_id: currentSession.session_id })
    }
  } catch (err) {
    console.error("Backend cleanup failed:", err)
  }

  set({ session: null, messages: [] })
},

  sendMessage: async (question) => {
    const { session, messages } = get()
    if (!session?.session_id) {
      toast.error('Process a video first')
      return
    }

    const userMsg = {
      _id: crypto.randomUUID(),
      role: 'user',
      text: question,
      createdAt: new Date().toISOString(),
    }
    set({ messages: [...messages, userMsg], isChatLoading: true })

    try {
      const res = await axiosInstance.post('/chat', {
        session_id: session.session_id,
        question,
      })
      const assistantMsg = {
        _id: crypto.randomUUID(),
        role: 'assistant',
        text: res.data.answer,
        createdAt: res.data.created_at || new Date().toISOString(),
      }
      set({ messages: [...get().messages, assistantMsg] })
    } catch (err) {
      const msg = err?.response?.data?.error || 'Failed to get an answer'
      toast.error(msg)
    } finally {
      set({ isChatLoading: false })
    }
  },
}))
