import { create } from 'zustand'
import toast from 'react-hot-toast'
import { axiosInstance } from '../lib/axios'
import { getCookie, setCookie, deleteCookie } from '../lib/cookies'

const CHAT_COOKIE = 'ava_chat_messages'
 
function saveMessagesToCookie(messages) {
  let toStore = messages
  let serialized = JSON.stringify(toStore)
  while (serialized.length > 3800 && toStore.length > 1) {
    toStore = toStore.slice(-Math.max(1, toStore.length - 2))  
    serialized = JSON.stringify(toStore)
  }
  setCookie(CHAT_COOKIE, serialized)
}

function loadMessagesFromCookie() {
  const raw = getCookie(CHAT_COOKIE)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const useAppStore = create((set, get) => ({ 
  session: null,         
  isProcessing: false,
 
  messages: loadMessagesFromCookie(),         
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
      deleteCookie(CHAT_COOKIE) 
      toast.success('Video processed successfully')
      return res.data
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Failed to process source'
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

  deleteCookie(CHAT_COOKIE)
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
    saveMessagesToCookie(get().messages)

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
      const updated = [...get().messages, assistantMsg]
      set({ messages: updated })
      saveMessagesToCookie(updated)
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Failed to get an answer'
      toast.error(msg)
    } finally {
      set({ isChatLoading: false })
    }
  },
}))
