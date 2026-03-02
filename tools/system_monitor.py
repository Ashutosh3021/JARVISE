"""
JARVIS Tools - System Monitor

Provides system diagnostics using psutil.
Returns CPU, memory, disk, and network statistics.
"""

import os
import asyncio
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from tools.base import BaseTool, ToolError


try:
    import psutil
except ImportError:
    logger.warning("psutil not installed. Install with: pip install psutil")
    psutil = None


@dataclass
class CPUStats:
    """CPU usage statistics."""
    percent: float
    per_cpu: list[float]
    count: int
    frequency: Optional[float] = None
    ctx_switches: Optional[int] = None
    interrupts: Optional[int] = None


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total: int
    available: int
    used: int
    percent: float
    total_gb: float
    available_gb: float
    used_gb: float


@dataclass
class DiskStats:
    """Disk usage statistics."""
    total: int
    used: int
    free: int
    percent: float
    total_gb: float
    used_gb: float
    free_gb: float


@dataclass  
class NetworkStats:
    """Network I/O statistics."""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    bytes_sent_mb: float
    bytes_recv_mb: float


class SystemMonitorTool(BaseTool):
    """System monitor tool using psutil.
    
    Provides comprehensive system diagnostics:
    - CPU usage (overall and per-core)
    - Memory usage (total, available, used)
    - Disk usage (per partition)
    - Network I/O statistics
    
    All methods support streaming callbacks and async operation.
    
    Example:
        >>> monitor = SystemMonitorTool()
        >>> cpu = monitor.get_cpu_usage()
        >>> print(f"CPU: {cpu.percent}%")
        >>> stats = monitor.get_all()
        >>> print(f"Memory: {stats['memory']['percent']}%")
    """
    
    def __init__(
        self,
        callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize system monitor tool.
        
        Args:
            callback: Optional callback for streaming status updates
        """
        super().__init__(name="SystemMonitor")
        
        if psutil is None:
            raise ToolError(
                "system_monitor",
                "psutil not installed",
                "Install with: pip install psutil"
            )
        
        self.callback = callback
        self.logger.info("SystemMonitorTool initialized")
    
    def _log(self, message: str) -> None:
        """Log message and optionally send to callback."""
        self.logger.debug(message)
        if self.callback:
            self.callback(message)
    
    def get_cpu_usage(
        self,
        interval: float = 0.1,
        percpu: bool = False,
    ) -> CPUStats:
        """Get CPU usage statistics.
        
        Args:
            interval: Measurement interval in seconds (for accuracy)
            percpu: If True, return per-CPU statistics
            
        Returns:
            CPUStats dataclass with usage information
            
        Raises:
            ToolError: If retrieval fails
        """
        try:
            self._log("Getting CPU statistics...")
            
            # Get per-CPU usage
            per_cpu = psutil.cpu_percent(interval=interval, percpu=True)
            
            # Get overall CPU usage
            percent = psutil.cpu_percent(interval=None)
            
            # Get CPU count
            count = psutil.cpu_count()
            
            # Try to get frequency (may not be available on all systems)
            frequency = None
            try:
                freq = psutil.cpu_freq()
                if freq:
                    frequency = freq.current
            except Exception:
                pass
            
            # Try to get ctx switches
            ctx_switches = None
            interrupts = None
            try:
                ctx_info = psutil.cpu_stats()
                ctx_switches = ctx_info.ctx_switches
                interrupts = ctx_info.interrupts
            except Exception:
                pass
            
            stats = CPUStats(
                percent=percent,
                per_cpu=per_cpu,
                count=count,
                frequency=frequency,
                ctx_switches=ctx_switches,
                interrupts=interrupts,
            )
            
            self._log(f"CPU usage: {percent}%")
            return stats
            
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get CPU stats: {str(e)}",
                "Check system permissions"
            )
    
    def get_memory_usage(self) -> MemoryStats:
        """Get memory usage statistics.
        
        Returns:
            MemoryStats dataclass with memory information
            
        Raises:
            ToolError: If retrieval fails
        """
        try:
            self._log("Getting memory statistics...")
            
            virtual = psutil.virtual_memory()
            
            stats = MemoryStats(
                total=virtual.total,
                available=virtual.available,
                used=virtual.used,
                percent=virtual.percent,
                total_gb=virtual.total / (1024**3),
                available_gb=virtual.available / (1024**3),
                used_gb=virtual.used / (1024**3),
            )
            
            self._log(f"Memory: {stats.used_gb:.1f}GB / {stats.total_gb:.1f}GB ({stats.percent}%)")
            return stats
            
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get memory stats: {str(e)}",
                "Check system permissions"
            )
    
    def get_disk_usage(
        self,
        path: str = "C:\\",
        mount_point: Optional[str] = None,
    ) -> DiskStats:
        """Get disk usage for a path or mount point.
        
        Args:
            path: Path to check (Windows: "C:\\", Unix: "/")
            mount_point: Alternative mount point to check
            
        Returns:
            DiskStats dataclass with disk information
            
        Raises:
            ToolError: If retrieval fails
        """
        try:
            target = mount_point or path
            self._log(f"Getting disk statistics for {target}...")
            
            usage = psutil.disk_usage(target)
            
            stats = DiskStats(
                total=usage.total,
                used=usage.used,
                free=usage.free,
                percent=usage.percent,
                total_gb=usage.total / (1024**3),
                used_gb=usage.used / (1024**3),
                free_gb=usage.free / (1024**3),
            )
            
            self._log(f"Disk {target}: {stats.used_gb:.1f}GB / {stats.total_gb:.1f}GB ({stats.percent}%)")
            return stats
            
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get disk stats for {target}: {str(e)}",
                "Verify path exists and is accessible"
            )
    
    def get_disk_partitions(self) -> list[dict]:
        """Get list of disk partitions.
        
        Returns:
            List of partition information dicts
            
        Raises:
            ToolError: If retrieval fails
        """
        try:
            self._log("Getting disk partitions...")
            
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent,
                    })
                except PermissionError:
                    # Skip partitions we can't access
                    continue
            
            self._log(f"Found {len(partitions)} partitions")
            return partitions
            
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get partitions: {str(e)}",
                "Check system permissions"
            )
    
    def get_network_stats(self) -> NetworkStats:
        """Get network I/O statistics.
        
        Returns:
            NetworkStats dataclass with network information
            
        Raises:
            ToolError: If retrieval fails
        """
        try:
            self._log("Getting network statistics...")
            
            net_io = psutil.net_io_counters()
            
            stats = NetworkStats(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                bytes_sent_mb=net_io.bytes_sent / (1024**2),
                bytes_recv_mb=net_io.bytes_recv / (1024**2),
            )
            
            self._log(f"Network: {stats.bytes_sent_mb:.2f}MB sent, {stats.bytes_recv_mb:.2f}MB received")
            return stats
            
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get network stats: {str(e)}",
                "Check system permissions"
            )
    
    def get_network_connections(self) -> list[dict]:
        """Get network connections (active sockets).
        
        Returns:
            List of connection information dicts
            
        Raises:
            ToolError: If retrieval fails
        """
        try:
            self._log("Getting network connections...")
            
            connections = []
            # Get all connections (may require elevated privileges)
            try:
                net_connections = psutil.net_connections(kind="inet")
                
                # Group by status
                for conn in net_connections[:50]:  # Limit to 50
                    if conn.laddr:
                        connections.append({
                            "family": "IPv4" if conn.family == 2 else "IPv6",
                            "type": "TCP" if conn.type == 1 else "UDP",
                            "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}",
                            "status": conn.status,
                            "pid": conn.pid,
                        })
            except PermissionError:
                # Fall back to basic info
                connections.append({
                    "error": "Permission denied - need elevated privileges for full connection info"
                })
            
            self._log(f"Found {len(connections)} connections")
            return connections
            
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get connections: {str(e)}",
                "Check system permissions"
            )
    
    def get_all(
        self,
        disk_path: str = "C:\\",
    ) -> dict:
        """Get all system statistics.
        
        Args:
            disk_path: Path to check for disk usage
            
        Returns:
            Dict with all system metrics
            
        Raises:
            ToolError: If any retrieval fails
        """
        self._log("Getting all system statistics...")
        
        try:
            # Get all stats
            cpu = self.get_cpu_usage()
            memory = self.get_memory_usage()
            disk = self.get_disk_usage(path=disk_path)
            network = self.get_network_stats()
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu.percent,
                    "per_cpu": cpu.per_cpu,
                    "count": cpu.count,
                    "frequency_mhz": cpu.frequency,
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "total_gb": round(memory.total_gb, 2),
                    "available_gb": round(memory.available_gb, 2),
                    "used_gb": round(memory.used_gb, 2),
                },
                "disk": {
                    "path": disk_path,
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                    "total_gb": round(disk.total_gb, 2),
                    "used_gb": round(disk.used_gb, 2),
                    "free_gb": round(disk.free_gb, 2),
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                    "bytes_sent_mb": round(network.bytes_sent_mb, 2),
                    "bytes_recv_mb": round(network.bytes_recv_mb, 2),
                },
            }
            
            self._log("All system statistics collected")
            return result
            
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                "system_monitor",
                f"Failed to get all stats: {str(e)}",
                "Check system permissions"
            )
    
    async def get_all_async(
        self,
        disk_path: str = "C:\\",
        callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """Get all system statistics asynchronously.
        
        Args:
            disk_path: Path to check for disk usage
            callback: Optional callback for streaming updates
            
        Returns:
            Dict with all system metrics
        """
        callback = callback or self._log
        
        def run_in_executor(func, *args):
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, func, *args)
        
        # Run all stats gathering concurrently
        callback("Gathering CPU stats...")
        cpu_task = asyncio.create_task(
            asyncio.to_thread(self.get_cpu_usage)
        )
        
        callback("Gathering memory stats...")
        memory_task = asyncio.create_task(
            asyncio.to_thread(self.get_memory_usage)
        )
        
        callback("Gathering disk stats...")
        disk_task = asyncio.create_task(
            asyncio.to_thread(self.get_disk_usage, disk_path)
        )
        
        callback("Gathering network stats...")
        network_task = asyncio.create_task(
            asyncio.to_thread(self.get_network_stats)
        )
        
        # Wait for all tasks
        cpu, memory, disk, network = await asyncio.gather(
            cpu_task, memory_task, disk_task, network_task
        )
        
        # Build result
        result = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu.percent,
                "per_cpu": cpu.per_cpu,
                "count": cpu.count,
            },
            "memory": {
                "total_gb": round(memory.total_gb, 2),
                "available_gb": round(memory.available_gb, 2),
                "used_gb": round(memory.used_gb, 2),
                "percent": memory.percent,
            },
            "disk": {
                "path": disk_path,
                "total_gb": round(disk.total_gb, 2),
                "used_gb": round(disk.used_gb, 2),
                "free_gb": round(disk.free_gb, 2),
                "percent": disk.percent,
            },
            "network": {
                "bytes_sent_mb": round(network.bytes_sent_mb, 2),
                "bytes_recv_mb": round(network.bytes_recv_mb, 2),
            },
        }
        
        callback("All system statistics collected")
        return result
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute a system monitor action.
        
        Args:
            action: Action to perform (cpu, memory, disk, network, all)
            **kwargs: Arguments for the action
            
        Returns:
            Result of the action
        """
        actions = {
            "cpu": lambda: self.get_cpu_usage(
                interval=kwargs.get("interval", 0.1),
                percpu=kwargs.get("percpu", False),
            ),
            "memory": lambda: self.get_memory_usage(),
            "disk": lambda: self.get_disk_usage(
                path=kwargs.get("path", "C:\\"),
            ),
            "partitions": lambda: self.get_disk_partitions(),
            "network": lambda: self.get_network_stats(),
            "connections": lambda: self.get_network_connections(),
            "all": lambda: self.get_all(
                disk_path=kwargs.get("disk_path", "C:\\"),
            ),
        }
        
        if action not in actions:
            raise ToolError(
                "system_monitor",
                f"Unknown action: {action}",
                f"Valid actions: {', '.join(actions.keys())}"
            )
        
        return actions[action]()


__all__ = ["SystemMonitorTool", "CPUStats", "MemoryStats", "DiskStats", "NetworkStats"]
