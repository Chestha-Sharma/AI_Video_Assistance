import React from 'react'

const MessagesSkeleton = () => {
  const placeholders = Array(4).fill(null)

  return (
    <div className="flex-1 flex flex-col overflow-auto p-4 space-y-4">
      {placeholders.map((_, i) => (
        <div key={i} className={`chat ${i % 2 === 0 ? 'chat-start' : 'chat-end'}`}>
          <div className="chat-image avatar">
            <div className="size-9 rounded-full bg-base-300 animate-pulse" />
          </div>
          <div className="chat-bubble bg-base-200 animate-pulse w-40 h-10" />
        </div>
      ))}
    </div>
  )
}

export default MessagesSkeleton
