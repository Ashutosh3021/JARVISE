import { useState } from 'react'
import { useTheme } from './context/ThemeContext'
import { StatusBar } from './components/StatusBar/StatusBar'
import { ChatWindow } from './components/Chat/ChatWindow'
import { InputToolbar } from './components/Toolbar/InputToolbar'
import { useChatWebSocket } from './hooks/useChatWebSocket'
import { 
  MessageSquare, 
  Settings, 
  Database, 
  Cpu, 
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Headphones,
  Wifi,
  WifiOff
} from 'lucide-react'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const { theme, toggleTheme } = useTheme()
  
  // Connect to WebSocket for chat
  const { 
    messages, 
    isStreaming, 
    isThinking, 
    sendMessage, 
    connectionStatus 
  } = useChatWebSocket('ws://localhost:8000/ws/chat')

  const navItems = [
    { icon: MessageSquare, label: 'Chat', active: true },
    { icon: Database, label: 'Memory', active: false },
    { icon: Cpu, label: 'System', active: false },
    { icon: Headphones, label: 'Voice', active: false },
    { icon: Settings, label: 'Settings', active: false },
  ]

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-slate-dark">
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-slate-dark-hover">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            JARVIS
          </h1>
        </div>
        
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-dark-active transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5 text-gray-400" />
          ) : (
            <Moon className="w-5 h-5 text-gray-600" />
          )}
        </button>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside 
          className={`${
            sidebarCollapsed ? 'w-16' : 'w-56'
          } border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-slate-dark-hover transition-all duration-300 flex flex-col`}
        >
          <nav className="flex-1 py-4">
            {navItems.map((item) => (
              <button
                key={item.label}
                className={`w-full flex items-center gap-3 px-4 py-3 transition-colors ${
                  item.active 
                    ? 'text-teal-500 bg-teal-500/10 border-r-2 border-teal-500' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-dark-active'
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </button>
            ))}
          </nav>

          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-3 border-t border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-5 h-5 mx-auto" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </button>
        </aside>

        {/* Main content area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Connection status indicator */}
          <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
            {connectionStatus === 'connected' ? (
              <>
                <Wifi className="w-4 h-4 text-green-500" />
                <span className="text-xs text-green-500">Connected</span>
              </>
            ) : connectionStatus === 'connecting' ? (
              <>
                <Wifi className="w-4 h-4 text-yellow-500 animate-pulse" />
                <span className="text-xs text-yellow-500">Connecting...</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span className="text-xs text-red-500">Disconnected</span>
              </>
            )}
          </div>
          
          {/* Chat window */}
          <ChatWindow 
            messages={messages}
            isStreaming={isStreaming}
            isThinking={isThinking}
          />
          
          {/* Input toolbar */}
          <InputToolbar 
            onSendMessage={sendMessage}
            disabled={connectionStatus === 'connecting'}
          />
        </main>
      </div>

      {/* Status bar */}
      <StatusBar />
    </div>
  )
}

export default App
