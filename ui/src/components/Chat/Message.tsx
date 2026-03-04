import { Bot, User } from 'lucide-react'
import type { ChatMessage } from '../../hooks/useChatWebSocket'

interface MessageProps {
  message: ChatMessage
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'
  const isStreaming = message.isStreaming

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} animate-fade-in`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser 
          ? 'bg-teal-500' 
          : 'bg-slate-700'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-teal-400" />
        )}
      </div>

      {/* Message bubble */}
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? 'bg-teal-500 text-white rounded-br-sm'
            : 'bg-slate-700 text-gray-100 rounded-bl-sm'
        }`}
      >
        <p className="whitespace-pre-wrap break-words leading-relaxed">
          {message.content}
          {isStreaming && (
            <span className="inline-block w-0.5 h-4 ml-0.5 bg-teal-300 animate-pulse" />
          )}
        </p>
        
        {/* Timestamp */}
        <div className={`text-xs mt-1 opacity-60 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  )
}
