import { useState, useEffect, useRef, useCallback } from 'react'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

interface UseChatWebSocketReturn {
  messages: ChatMessage[]
  isStreaming: boolean
  isThinking: boolean
  sendMessage: (text: string) => void
  clearMessages: () => void
  connectionStatus: 'connecting' | 'connected' | 'disconnected'
}

export function useChatWebSocket(url: string): UseChatWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setConnectionStatus('connecting')
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionStatus('connected')
      reconnectAttempts.current = 0
    }

    ws.onclose = () => {
      setConnectionStatus('disconnected')
      // Attempt reconnection with exponential backoff
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, delay)
      }
    }

    ws.onerror = () => {
      setConnectionStatus('disconnected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'chat.stream' || data.type === 'token') {
          // Token streaming - append to last assistant message
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.role === 'assistant' && last.isStreaming) {
              return [
                ...prev.slice(0, -1),
                { ...last, content: last.content + (data.content || data.token || '') }
              ]
            }
            // Create new assistant message if none exists
            return [...prev, {
              id: `assistant_${Date.now()}_streaming`,
              role: 'assistant',
              content: data.content || data.token || '',
              timestamp: new Date(),
              isStreaming: true
            }]
          })
          setIsStreaming(true)
          setIsThinking(false)
        } else if (data.type === 'done' || data.type === 'chat.done') {
          // Streaming complete
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.isStreaming) {
              return [...prev.slice(0, -1), { ...last, isStreaming: false }]
            }
            return prev
          })
          setIsStreaming(false)
          setIsThinking(false)
        } else if (data.type === 'thinking') {
          setIsThinking(true)
        } else if (data.type === 'voice.state') {
          // Handle voice state events - can be used for waveform
          console.log('Voice state:', data.state)
        } else if (data.type === 'system.stats') {
          // Handle system stats events - already handled by useSystemStats
          console.log('System stats received via WebSocket')
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }
  }, [url])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  const sendMessage = useCallback((text: string) => {
    if (!text.trim()) return

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Add user message
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        role: 'user',
        content: text,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, userMessage])

      // Add placeholder for assistant response
      const assistantPlaceholder: ChatMessage = {
        id: `assistant_${Date.now()}_streaming`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true
      }
      setMessages(prev => [...prev, assistantPlaceholder])

      // Set thinking state
      setIsThinking(true)
      setIsStreaming(true)

      // Send to WebSocket
      wsRef.current.send(JSON.stringify({ message: text }))
    } else {
      console.warn('WebSocket not connected')
      // Add user message anyway for offline mode
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        role: 'user',
        content: text,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, userMessage])

      // Simulate response for offline development
      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: 'WebSocket not connected. Please ensure the backend is running.',
        timestamp: new Date(),
        isStreaming: false
      }
      setMessages(prev => [...prev, assistantMessage])
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isStreaming,
    isThinking,
    sendMessage,
    clearMessages,
    connectionStatus
  }
}
