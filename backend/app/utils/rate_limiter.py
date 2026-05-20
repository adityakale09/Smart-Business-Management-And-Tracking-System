"""
IP-based rate limiter for authentication endpoints.

Implements sliding-window rate limiting for failed login attempts
to prevent brute-force attacks. Uses in-memory storage with
automatic cleanup of expired entries.

PCI-DSS 8.3.3: Lockout after no more than 6 failed attempts (configurable).
ISO 27001 A.9.4.2: Rate limiting for authentication.
SOC 2 CC6.1: Brute-force protection.
"""

import time
import threading
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from fastapi import HTTPException, Request, status


@dataclass
class RateLimitEntry:
    """Stores timestamps of recent failed attempts for a given IP."""
    attempts: List[float] = field(default_factory=list)


class IPRateLimiter:
    """
    Sliding-window rate limiter keyed by IP address.
    
    Tracks failed attempts within a configurable time window.
    When the maximum attempts are exceeded, the IP is blocked
    until the oldest attempt in the window expires.
    
    Thread-safe for concurrent API requests.
    """
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        """
        Initialize the rate limiter.
        
        Args:
            max_attempts: Maximum failed attempts before lockout (default: 5)
            window_seconds: Time window in seconds (default: 900 = 15 minutes)
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._entries: Dict[str, RateLimitEntry] = {}
        self._lock = threading.Lock()
    
    def _cleanup_expired(self, entry: RateLimitEntry) -> None:
        """Remove expired attempt timestamps from an entry."""
        now = time.time()
        cutoff = now - self.window_seconds
        entry.attempts = [t for t in entry.attempts if t > cutoff]
    
    def _cleanup_all(self) -> None:
        """Remove all expired entries from the store."""
        now = time.time()
        cutoff = now - self.window_seconds
        expired_ips = [
            ip for ip, entry in self._entries.items()
            if not entry.attempts or max(entry.attempts) < cutoff
        ]
        for ip in expired_ips:
            del self._entries[ip]
    
    def record_failure(self, ip_address: str) -> None:
        """
        Record a failed authentication attempt for an IP.
        
        Args:
            ip_address: The client IP address
        """
        with self._lock:
            if ip_address not in self._entries:
                self._entries[ip_address] = RateLimitEntry()
            entry = self._entries[ip_address]
            entry.attempts.append(time.time())
            # Cleanup old entries for this IP
            self._cleanup_expired(entry)
    
    def is_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP is currently blocked due to too many failed attempts.
        
        Args:
            ip_address: The client IP address
            
        Returns:
            True if the IP is blocked, False otherwise
        """
        with self._lock:
            entry = self._entries.get(ip_address)
            if not entry:
                return False
            self._cleanup_expired(entry)
            return len(entry.attempts) >= self.max_attempts
    
    def check_rate_limit(self, request: Request) -> None:
        """
        Check if the requesting IP is rate-limited and raise 429 if blocked.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException 429 if rate limit exceeded
        """
        ip_address = request.client.host if request.client else "unknown"
        if self.is_blocked(ip_address):
            # Calculate retry-after time
            with self._lock:
                entry = self._entries.get(ip_address)
                retry_after = 0
                if entry and len(entry.attempts) > 0:
                    oldest = min(entry.attempts)
                    retry_after = int((oldest + self.window_seconds) - time.time())
                    if retry_after < 0:
                        retry_after = 0
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many failed login attempts",
                    "message": f"Your IP has been temporarily blocked due to {self.max_attempts} failed attempts. Please try again later.",
                    "retry_after_seconds": max(retry_after, 30),
                    "code": "RATE_LIMIT_EXCEEDED"
                },
                headers={"Retry-After": str(max(retry_after, 30))}
            )
    
    def reset_ip(self, ip_address: str) -> None:
        """
        Reset the rate limit counter for a successful login.
        
        Args:
            ip_address: The client IP address
        """
        with self._lock:
            self._entries.pop(ip_address, None)
    
    def get_remaining_attempts(self, ip_address: str) -> Tuple[int, int]:
        """
        Get remaining attempts and retry-after for an IP.
        
        Args:
            ip_address: The client IP address
            
        Returns:
            Tuple of (remaining_attempts, retry_after_seconds)
        """
        with self._lock:
            entry = self._entries.get(ip_address)
            if not entry:
                return (self.max_attempts, 0)
            self._cleanup_expired(entry)
            remaining = max(0, self.max_attempts - len(entry.attempts))
            retry_after = 0
            if len(entry.attempts) >= self.max_attempts:
                oldest = min(entry.attempts)
                retry_after = int((oldest + self.window_seconds) - time.time())
                if retry_after < 0:
                    retry_after = 0
            return (remaining, retry_after)


# Global rate limiter instance for login attempts
# 5 failed attempts within 15 minutes triggers lockout (PCI-DSS 8.3.3)
login_rate_limiter = IPRateLimiter(max_attempts=5, window_seconds=900)

# Global rate limiter instance for receipt upload operations
# 20 uploads per minute (60 seconds) to prevent OCR processing abuse
upload_rate_limiter = IPRateLimiter(max_attempts=20, window_seconds=60)
