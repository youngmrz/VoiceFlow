"""
Tests for the resource monitoring service.

Design requirements:
- Track CPU and memory usage
- Target: <1% CPU and <100MB memory when idle
- Provide snapshot functionality
"""
import pytest
from services.resource_monitor import ResourceMonitor


class TestResourceMonitor:
    """Test ResourceMonitor functionality."""

    def test_init(self):
        """Test ResourceMonitor initialization."""
        monitor = ResourceMonitor()
        assert monitor is not None

    def test_get_cpu_percent(self):
        """Test CPU percentage retrieval."""
        monitor = ResourceMonitor()
        cpu = monitor.get_cpu_percent()
        assert isinstance(cpu, float)
        assert cpu >= 0.0

    def test_get_memory_mb(self):
        """Test memory usage retrieval."""
        monitor = ResourceMonitor()
        memory = monitor.get_memory_mb()
        assert isinstance(memory, float)
        assert memory > 0.0  # Should always use some memory

    def test_get_memory_info(self):
        """Test detailed memory info retrieval."""
        monitor = ResourceMonitor()
        info = monitor.get_memory_info()
        assert isinstance(info, dict)
        assert 'rss_mb' in info
        assert 'vms_mb' in info
        assert 'percent' in info
        assert info['rss_mb'] > 0.0
        assert info['vms_mb'] > 0.0
        assert info['percent'] >= 0.0

    def test_get_snapshot(self):
        """Test resource snapshot functionality."""
        monitor = ResourceMonitor()
        snapshot = monitor.get_snapshot()
        assert isinstance(snapshot, dict)
        assert 'cpu_percent' in snapshot
        assert 'memory_mb' in snapshot
        assert 'memory_percent' in snapshot
        assert 'vms_mb' in snapshot
        assert snapshot['cpu_percent'] >= 0.0
        assert snapshot['memory_mb'] > 0.0

    def test_cpu_with_interval(self):
        """Test CPU measurement with interval."""
        monitor = ResourceMonitor()
        cpu = monitor.get_cpu_percent(interval=0.1)
        assert isinstance(cpu, float)
        assert cpu >= 0.0
