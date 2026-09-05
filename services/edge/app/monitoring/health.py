import psutil
from typing import Optional
from app.models.status import SystemHealth, VisionHealth
from app.config.settings import Settings
import logging

logger = logging.getLogger("monitoring")

class HealthMonitor:
    def __init__(self, config: Settings):
        self.thresholds = config.monitoring.health

    def get_health(self, vision_health: Optional[VisionHealth] = None) -> SystemHealth:
        cpu_usage = psutil.cpu_percent(interval=None) # Non-blocking
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        health = SystemHealth(
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=mem.percent,
            memory_available_bytes=mem.available,
            disk_usage_percent=disk.percent,
            gpu_usage_percent=None, # Mocked for now unless specific hardware found
            gpu_memory_usage=None,
            gpu_temperature=None,
            vision=vision_health
        )
        
        self._check_thresholds(health)
        
        return health
        
    def _check_thresholds(self, health: SystemHealth):
        if health.cpu_usage_percent >= self.thresholds.cpu_critical_percent:
            logger.error(f"CPU usage CRITICAL: {health.cpu_usage_percent}%")
        elif health.cpu_usage_percent >= self.thresholds.cpu_warning_percent:
            logger.warning(f"CPU usage WARNING: {health.cpu_usage_percent}%")
            
        if health.memory_usage_percent >= self.thresholds.memory_critical_percent:
            logger.error(f"Memory usage CRITICAL: {health.memory_usage_percent}%")
        elif health.memory_usage_percent >= self.thresholds.memory_warning_percent:
            logger.warning(f"Memory usage WARNING: {health.memory_usage_percent}%")
