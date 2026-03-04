import { useEffect, useRef } from 'react'
import { Message as MessageType } from '../../hooks/useChatWebSocket'
import { Message } from './Message'

interface ChatWindowProps {
  messages: MessageType[]
  isStreaming: boolean
  isThinking: boolean
}

export function ChatWindow({ messages, isStreaming, isThinking }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Welcome message when empty */}
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center mb-4">
            <span className="text-4xl">🤖</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Welcome to JARVIS
          </h2>
          <p className="text-gray-500 dark:text-gray-400 max-w-md">
            I'm ready to assist you. Type a message below to start a conversation.
          </p>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}

      {/* Thinking indicator (animated dots) */}
      {isThinking && !messages.some(m => m.isStreaming) && (
        <div className="flex gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
            <span className="text-lg">🤖</span>
          </div>
          <div className="bg-slate-700 rounded-2xl rounded-bl-sm px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2.5 h-2.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}

      {/* Invisible element to scroll to */}
      <div ref={messagesEndRef} />
    </div>
  )
}
