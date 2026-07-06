import React, { useState } from 'react'
import { Send } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'

const MessageInput = () => {
  const [text, setText] = useState('')
  const { sendMessage, isChatLoading, session } = useAppStore()

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    setText('')
    sendMessage(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="p-3 border-t border-base-300 flex items-center gap-2">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={session ? 'Ask something about this video...' : 'Process a video first'}
        disabled={!session || isChatLoading}
        className="input input-bordered flex-1 rounded-full focus:outline-none"
      />
      <button
        type="submit"
        disabled={!session || !text.trim() || isChatLoading}
        className="btn btn-circle btn-primary"
      >
        <Send size={18} />
      </button>
    </form>
  )
}

export default MessageInput
