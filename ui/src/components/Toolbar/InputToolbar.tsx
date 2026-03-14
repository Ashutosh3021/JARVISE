import { useState, FormEvent, useRef } from 'react'
import { 
  Send, 
  Mic, 
  MicOff,
  Paperclip, 
  Smile,
  X
} from 'lucide-react'

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
  isFinal: boolean
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  onstart: (() => void) | null
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: Event) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition
    webkitSpeechRecognition: new () => SpeechRecognition
  }
}

interface InputToolbarProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
}

export function InputToolbar({ onSendMessage, disabled }: InputToolbarProps) {
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    // Auto-resize textarea
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
    }
  }

  const handleVoiceClick = () => {
    if (isRecording) {
      // Stop recording
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      setIsRecording(false)
    } else {
      // Start recording
      const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition
      if (!SpeechRecognition) {
        alert('Speech recognition not supported in this browser')
        return
      }
      
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = true
      recognition.lang = 'en-US'
      
      recognition.onstart = () => {
        setIsRecording(true)
      }
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('')
        setInput(prev => prev + transcript)
      }
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error || event)
        setIsRecording(false)
      }
      
      recognition.onend = () => {
        setIsRecording(false)
      }
      
      recognition.start()
      recognitionRef.current = recognition
    }
  }

  const handleFileClick = () => {
    // Placeholder for file upload
    console.log('File upload clicked - file upload coming soon')
  }

  const handleEmojiClick = () => {
    // Placeholder for emoji picker
    console.log('Emoji picker clicked - emoji picker coming soon')
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-slate-dark-hover p-4">
      <form 
        onSubmit={handleSubmit}
        className="flex items-end gap-2"
      >
        {/* Toolbar buttons */}
        <div className="flex gap-1">
          <button
            type="button"
            onClick={handleVoiceClick}
            disabled={disabled}
            className={`p-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              isRecording 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-dark-active'
            }`}
            title={isRecording ? "Stop recording" : "Voice input"}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          
          <button
            type="button"
            onClick={handleFileClick}
            disabled={disabled}
            className="p-2.5 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-dark-active transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Attach file"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <button
            type="button"
            onClick={handleEmojiClick}
            disabled={disabled}
            className="p-2.5 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-dark-active transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Add emoji"
          >
            <Smile className="w-5 h-5" />
          </button>
        </div>

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'Connecting...' : 'Type a message...'}
            disabled={disabled}
            rows={1}
            className="w-full bg-white dark:bg-slate-dark border border-gray-300 dark:border-gray-600 rounded-xl px-4 py-3 pr-10 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none resize-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          />
          
          {/* Clear button */}
          {input && (
            <button
              type="button"
              onClick={() => {
                setInput('')
                if (textareaRef.current) {
                  textareaRef.current.style.height = 'auto'
                }
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Send button */}
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="p-3 rounded-xl bg-teal-500 hover:bg-teal-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-teal-500"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  )
}
