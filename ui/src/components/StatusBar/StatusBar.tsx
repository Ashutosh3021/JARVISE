import { useState, useEffect } from 'react'
import { Cpu, HardDrive, MemoryStick, ChevronUp, ChevronDown, Wifi, WifiOff, Bot } from 'lucide-react'

interface SystemStats {
  cpu: { percent: number }
  memory: { percent: number; used_gb: number; total_gb: number }
  vram?: { percent: number; used_gb: number; total_gb: number }
}

export function StatusBar() {
  const [collapsed, setCollapsed] = useState(false)
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const fetchStats = async () => {
      try {
        const res = await fetch('/api/stats/current')
        if (mounted) {
          if (res.ok) {
            const data = await res.json()
            setStats(data)
            setConnected(true)
            setError(null)
          } else {
            setConnected(false)
            // Use placeholder data when backend not available
            setStats({
              cpu: { percent: Math.random() * 30 + 10 },
              memory: { percent: Math.random() * 40 + 30, used_gb: 8.2, total_gb: 32 },
              vram: { percent: Math.random() * 50 + 20, used_gb: 4.1, total_gb: 12 }
            })
          }
        }
      } catch (err) {
        if (mounted) {
          setConnected(false)
          setError('Backend not available')
          // Use placeholder data for development
          setStats({
            cpu: { percent: Math.random() * 30 + 10 },
            memory: { percent: Math.random() * 40 + 30, used_gb: 8.2, total_gb: 32 },
            vram: { percent: Math.random() * 50 + 20, used_gb: 4.1, total_gb: 12 }
          })
        }
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 5000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-slate-dark-hover">
      <button 
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-4 py-1 flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 hover:text-teal-500 dark:hover:text-teal-accent transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          System Status
        </span>
        {collapsed ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>
      
      {!collapsed && (
        <div className="px-4 py-2 flex flex-wrap gap-4 text-xs sm:text-sm">
          {/* CPU */}
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-teal-accent" />
            <span className="text-gray-600 dark:text-gray-300">
              CPU: {stats?.cpu.percent.toFixed(1) ?? '--'}%
            </span>
          </div>

          {/* Memory */}
          <div className="flex items-center gap-2">
            <MemoryStick className="w-4 h-4 text-teal-accent" />
            <span className="text-gray-600 dark:text-gray-300">
              RAM: {stats?.memory.percent.toFixed(1) ?? '--'}%
              {stats && ` (${stats.memory.used_gb.toFixed(1)}/${stats.memory.total_gb}GB)`}
            </span>
          </div>

          {/* VRAM */}
          {stats?.vram && (
            <div className="flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-teal-accent" />
              <span className="text-gray-600 dark:text-gray-300">
                VRAM: {stats.vram.percent.toFixed(1)}% ({stats.vram.used_gb.toFixed(1)}/{stats.vram.total_gb}GB)
              </span>
            </div>
          )}

          {/* Connection status */}
          <div className="flex items-center gap-2 ml-auto">
            {connected ? (
              <>
                <Wifi className="w-4 h-4 text-green-500" />
                <span className="text-green-500">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span className="text-red-500">{error || 'Disconnected'}</span>
              </>
            )}
          </div>

          {/* Model */}
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-teal-accent" />
            <span className="text-gray-600 dark:text-gray-300">qwen2.5</span>
          </div>
        </div>
      )}
    </div>
  )
}
