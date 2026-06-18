# -*- coding: utf-8 -*-
"""
===============================================================================
RATE LIMITER TESTS
===============================================================================
Unit testovi za RateLimitController - sliding window RPM tracking.

Pokretanje:
    pytest tests/unit/test_rate_limiter.py -v
===============================================================================
"""

import time
from threading import Thread
from app.services.translation.rate_limiter import RateLimitController


class TestRateLimitController:
    """Testovi za RateLimitController."""

    def test_init_default_limits(self):
        rl = RateLimitController()
        assert rl.get_limit("groq") == 30
        assert rl.get_limit("ollama") == 100
        assert rl.get_limit("unknown") == 60

    def test_record_and_count(self):
        rl = RateLimitController()
        rl.record_request("groq")
        rl.record_request("groq")
        assert rl.request_count("groq") == 2

    def test_allowed_under_limit(self):
        rl = RateLimitController()
        for _ in range(5):
            rl.record_request("groq")
        assert rl.is_allowed("groq") is True

    def test_blocked_over_limit(self):
        rl = RateLimitController()
        rl.set_limit("test_provider", 3)
        for _ in range(3):
            rl.record_request("test_provider")
        assert rl.is_allowed("test_provider") is False

    def test_window_expires(self):
        rl = RateLimitController()
        rl.set_limit("test_provider", 2)
        rl.record_request("test_provider")
        rl._windows["test_provider"][0] = time.time() - 61
        assert rl.is_allowed("test_provider") is True

    def test_window_expires_clears_old(self):
        rl = RateLimitController()
        rl.set_limit("test_provider", 100)
        rl.record_request("test_provider")
        rl._windows["test_provider"][0] = time.time() - 61
        rl.record_request("test_provider")
        rl.record_request("test_provider")
        assert rl.request_count("test_provider") == 2

    def test_set_limit_updates(self):
        rl = RateLimitController()
        rl.set_limit("groq", 50)
        assert rl.get_limit("groq") == 50

    def test_thread_safety(self):
        rl = RateLimitController()
        rl.set_limit("test_provider", 10000)
        errors = []

        def worker():
            try:
                for _ in range(100):
                    rl.record_request("test_provider")
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert rl.request_count("test_provider") == 1000

    def test_multiple_providers_independent(self):
        rl = RateLimitController()
        rl.set_limit("provider_a", 5)
        rl.set_limit("provider_b", 3)
        for _ in range(5):
            rl.record_request("provider_a")
        for _ in range(3):
            rl.record_request("provider_b")
        assert rl.is_allowed("provider_a") is False
        assert rl.is_allowed("provider_b") is False

    def test_request_count_zero_for_new_provider(self):
        rl = RateLimitController()
        assert rl.request_count("nonexistent") == 0

    def test_is_allowed_for_new_provider(self):
        rl = RateLimitController()
        assert rl.is_allowed("nonexistent") is True

    def test_cleanup_expired(self):
        rl = RateLimitController()
        rl.set_limit("test_provider", 10)
        rl.record_request("test_provider")
        rl.record_request("test_provider")
        rl._windows["test_provider"][0] = time.time() - 61
        rl._cleanup("test_provider")
        assert rl.request_count("test_provider") == 1

    def test_low_limit_blocks_immediately(self):
        rl = RateLimitController()
        rl.set_limit("slow_provider", 1)
        assert rl.is_allowed("slow_provider") is True
        rl.record_request("slow_provider")
        assert rl.is_allowed("slow_provider") is False

    def test_records_across_providers(self):
        rl = RateLimitController()
        rl.record_request("a")
        rl.record_request("b")
        rl.record_request("a")
        assert rl.request_count("a") == 2
        assert rl.request_count("b") == 1
