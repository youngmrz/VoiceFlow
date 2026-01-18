"""
Resource monitoring service for VoiceFlow.

Tracks CPU and memory usage to ensure minimal idle resource usage.
Target: <1% CPU and <100MB memory when idle.

Usage:
    from services.resource_monitor import ResourceMonitor
    monitor = ResourceMonitor()
    cpu = monitor.get_cpu_percent()
    memory = monitor.get_memory_mb()
"""
import psutil
from typing import Optional
from services.logger import get_logger

log = get_logger("model")  # Using 'model' domain as it's related to resource management


class ResourceMonitor:
    """Monitor CPU and memory usage of the application."""

    def __init__(self):
        """Initialize the resource monitor."""
        self._process = psutil.Process()
        log.info("Resource monitor initialized")

    def get_cpu_percent(self, interval: Optional[float] = None) -> float:
        """
        Get current CPU usage percentage.

        Args:
            interval: Time interval in seconds to measure CPU usage.
                     If None, returns instant value based on previous call.
                     First call with None returns 0.0.

        Returns:
            CPU percentage (0-100). Values can exceed 100 on multi-core systems.
        """
        try:
            cpu = self._process.cpu_percent(interval=interval)
            return cpu
        except Exception as e:
            log.error("Failed to get CPU percentage", error=str(e))
            return 0.0

    def get_memory_mb(self) -> float:
        """
        Get current memory usage in megabytes.

        Returns:
            Memory usage in MB (Resident Set Size).
        """
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            return memory_mb
        except Exception as e:
            log.error("Failed to get memory usage", error=str(e))
            return 0.0

    def get_memory_info(self) -> dict:
        """
        Get detailed memory information.

        Returns:
            Dictionary with memory metrics:
            - rss_mb: Resident Set Size in MB (physical memory)
            - vms_mb: Virtual Memory Size in MB
            - percent: Percentage of total system memory used
        """
        try:
            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()
            return {
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024),
                'percent': memory_percent
            }
        except Exception as e:
            log.error("Failed to get memory info", error=str(e))
            return {
                'rss_mb': 0.0,
                'vms_mb': 0.0,
                'percent': 0.0
            }

    def get_snapshot(self) -> dict:
        """
        Get a complete resource usage snapshot.

        Returns:
            Dictionary with current CPU and memory metrics.
        """
        memory_info = self.get_memory_info()
        cpu = self.get_cpu_percent()

        snapshot = {
            'cpu_percent': cpu,
            'memory_mb': memory_info['rss_mb'],
            'memory_percent': memory_info['percent'],
            'vms_mb': memory_info['vms_mb']
        }

        log.debug("Resource snapshot taken", **snapshot)
        return snapshot
