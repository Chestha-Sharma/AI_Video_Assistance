import React, { useEffect, useRef } from 'react'
import { Bot, User, MessageCircle } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import MessageInput from './MessageInput'

const formatTime = (dateStr) => {
  return new Date(dateStr).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

const ChatContainer = () => {
  const { messages, isChatLoading, session } = useAppStore()
  const messageEndRef = useRef(null)

  useEffect(() => {
    if (messageEndRef.current && messages.length) {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages.length])

  return (
    <div className="w-full lg:w-96 shrink-0 border-l border-base-300 flex flex-col bg-base-200/30">
      <div className="p-4 border-b border-base-300 flex items-center gap-2">
        <div className="size-8 rounded-full bg-primary/15 flex items-center justify-center">
          <MessageCircle size={16} className="text-primary" />
        </div>
        <div>
          <p className="font-medium text-sm leading-tight">Chat with this video</p>
          <p className="text-xs opacity-50">Answers are grounded in the transcript</p>
        </div>
      </div>

      {!session ? (
        <div className="flex-1 flex items-center justify-center p-6 text-center opacity-50 text-sm">
          Process a video to start asking questions.
        </div>
      ) : messages.length === 0 && !isChatLoading ? (
        <div className="flex-1 flex items-center justify-center p-6 text-center opacity-50 text-sm">
          Ask anything — e.g. "What did we decide about the launch date?"
        </div>
      ) : (
        <div className="flex-1 flex flex-col overflow-auto p-4 gap-1">
          {messages.map((message) => {
            const isUser = message.role === 'user'
            return (
              <div key={message._id} className={`chat ${isUser ? 'chat-end' : 'chat-start'}`}>
                <div className="chat-image avatar placeholder">
                  <div className="size-8 rounded-full bg-base-300 text-base-content/70 flex items-center justify-center">
                    {isUser ? <User size={14} /> : <Bot size={14} />}
                  </div>
                </div>
                <div
                  className={`chat-bubble flex flex-col text-sm
                    ${isUser
                      ? 'bg-primary text-primary-content rounded-2xl rounded-br-sm'
                      : 'bg-base-200 text-base-content rounded-2xl rounded-bl-sm'}`}
                >
                  <p className="whitespace-pre-wrap">{message.text}</p>
                </div>
                <div className="chat-footer opacity-50 text-xs mt-1">
                  {formatTime(message.createdAt)}
                </div>
              </div>
            )
          })}
          {isChatLoading && (
            <div className="chat chat-start">
              <div className="chat-image avatar placeholder">
                <div className="size-8 rounded-full bg-base-300 text-base-content/70 flex items-center justify-center">
                  <Bot size={14} />
                </div>
              </div>
              <div className="chat-bubble bg-base-200 rounded-2xl rounded-bl-sm">
                <span className="loading loading-dots loading-sm" />
              </div>
            </div>
          )}
          <div ref={messageEndRef} />
        </div>
      )}

      <MessageInput />
    </div>
  )
}

export default ChatContainer
