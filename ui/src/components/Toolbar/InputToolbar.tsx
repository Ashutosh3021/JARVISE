import { useState, FormEvent, useRef } from 'react'
import { 
  Send, 
  Mic, 
  Paperclip, 
  Smile,
  X
} from 'lucide-react'

interface InputToolbarProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
}

export function InputToolbar({ onSendMessage, disabled }: InputToolbarProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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
    // Placeholder for voice integration
    console.log('Voice button clicked - voice integration coming soon')
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
            className="p-2.5 rounded-lg text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-dark-active transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Voice input"
          >
            <Mic className="w-5 h-5" />
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
