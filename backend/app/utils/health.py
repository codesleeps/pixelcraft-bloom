import asyncio
import time
from enum import Enum
from typing import Callable, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger("agentsflowai.health")

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, fast fail
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = 0
        self.last_success_time = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit {self.name} entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
                logger.info(f"Circuit {self.name} recovered and is now CLOSED")
            
            self.last_success_time = time.time()
            return result
            
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            logger.warning(f"Circuit {self.name} failure #{self.failures}: {e}")
            
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit {self.name} opened due to failures")
            
            raise e

class HealthCheckService:
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.critical_services = set()

    def register_check(self, name: str, check_func: Callable, critical: bool = False):
        self.checks[name] = check_func
        self.breakers[name] = CircuitBreaker(name)
        if critical:
            self.critical_services.add(name)

    async def check_service(self, name: str) -> Dict[str, Any]:
        breaker = self.breakers.get(name)
        check_func = self.checks.get(name)
        
        if not breaker or not check_func:
            return {"status": "unknown", "error": "Service not registered"}

        try:
            # We wrap the check in the circuit breaker
            # The check function is expected to return True/False or raise exception
            # If it returns False, we treat it as failure for circuit breaker purposes
            async def wrapped_check():
                res = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                if not res:
                    raise Exception("Check returned False")
                return res

            await breaker.call(wrapped_check)
            return {
                "status": "healthy",
                "latency_ms": int((time.time() - breaker.last_success_time) * 1000) if breaker.last_success_time else 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_state": breaker.state.value
            }

    async def get_health_status(self) -> Dict[str, Any]:
        results = {}
        overall_status = "healthy"
        
        for name in self.checks:
            res = await self.check_service(name)
            results[name] = res
            if res["status"] != "healthy":
                if name in self.critical_services:
                    overall_status = "unhealthy"
                elif overall_status == "healthy":
                    overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": results
        }

    async def is_ready(self) -> bool:
        """Check if all critical services are healthy."""
        for name in self.critical_services:
            res = await self.check_service(name)
            if res["status"] != "healthy":
                return False
        return True

# Global instance
health_service = HealthCheckService()
