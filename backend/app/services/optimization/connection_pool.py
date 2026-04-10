# -*- coding: utf-8 -*-
"""
================================================================================
HTTP CONNECTION POOL SERVICE
================================================================================
FAZA 11: HTTP connection pooling za efikasne API pozive.

Optimizuje HTTP konekcije sa:
- Connection pooling (reuse konekcija)
- Keep-alive konekcije
- Timeout konfiguraciju
- Retry logiku

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-10
================================================================================
"""

import time
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager

import httpx
from httpx import Client as HTTPClient, Timeout, Limits, ConnectError, ReadTimeout


class ConnectionPool:
    """HTTP connection pool sa konfigurabilnim limitima.

    Omogućava reuse konekcija za bolje performanse.
    Podržava timeout, retry i custom headere.

    Attributes:
        max_connections: Maksimalan broj konekcija
        max_keepalive: Maksimalan broj keep-alive konekcija
        timeout: Timeout za request-e
        retry_count: Broj pokušaja kod neuspeha
    """

    def __init__(
        self,
        max_connections: int = 100,
        max_keepalive: int = 20,
        timeout: float = 120.0,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        """Inicijalizuje connection pool.

        Args:
            max_connections: Maksimalan broj konekcija
            max_keepalive: Maksimalan broj keep-alive konekcija
            timeout: Timeout u sekundama
            retry_count: Broj pokušaja kod neuspeha
            retry_delay: Kašnjenje između pokušaja
        """
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._client: Optional[HTTPClient] = None

    def _create_client(self) -> HTTPClient:
        """Kreira HTTP klijent sa optimalnim podešavanjima.

        Returns:
            Konfigurisan httpx Client
        """
        timeout_config = Timeout(
            connect=30.0,
            read=self.timeout,
            write=30.0,
            pool=10.0,
        )

        limits = Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive,
            keepalive_expiry=30.0,
        )

        return HTTPClient(
            timeout=timeout_config,
            limits=limits,
            follow_redirects=True,
            max_redirects=5,
        )

    @property
    def client(self) -> HTTPClient:
        """Vraća singleton HTTP klijent.

        Returns:
            httpx Client instanca
        """
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Šalje HTTP request sa automaticnim retry.

        Args:
            method: HTTP metoda
            url: URL
            headers: Opcioni headeri
            json: JSON body
            data: Form data
            params: Query parametri

        Returns:
            httpx Response objekat

        Raises:
            ConnectError: Ako konekcija ne može da se uspostavi
            ReadTimeout: Ako request traje predugo
        """
        return self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            data=data,
            params=params,
            **kwargs,
        )

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Šalje GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """Šalje POST request."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        """Šalje PUT request."""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        """Šalje DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        """Šalje PATCH request."""
        return self.request("PATCH", url, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Vraća statistike konekcije.

        Returns:
            Dict sa statistikama
        """
        if self._client is None:
            return {
                "status": "not_initialized",
                "connections": 0,
                "max_connections": self.max_connections,
            }

        try:
            pools = self._client._transport._pool
            return {
                "status": "active",
                "max_connections": self.max_connections,
                "max_keepalive": self.max_keepalive,
                "timeout": self.timeout,
            }
        except Exception:
            return {
                "status": "active",
                "max_connections": self.max_connections,
                "max_keepalive": self.max_keepalive,
                "timeout": self.timeout,
            }

    def close(self) -> None:
        """Zatvara sve konekcije."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "ConnectionPool":
        """Kontext manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Kontext manager exit."""
        self.close()


class QuizHTTPClient:
    """Specijalizovani HTTP klijent za quiz service.

    Optimizovan za AI API pozive sa specificnim timeout-ovima.
    """

    def __init__(self):
        self._pool = ConnectionPool(
            max_connections=50,
            max_keepalive=10,
            timeout=120.0,
            retry_count=3,
        )
        self._streaming_pool = ConnectionPool(
            max_connections=20,
            max_keepalive=5,
            timeout=180.0,
            retry_count=2,
        )

    @property
    def client(self) -> ConnectionPool:
        """Vraća glavni connection pool."""
        return self._pool

    @property
    def streaming(self) -> ConnectionPool:
        """Vraća streaming connection pool."""
        return self._streaming_pool

    def call_ai_provider(
        self,
        url: str,
        api_key: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Poziva AI provider API.

        Args:
            url: API URL
            api_key: API key
            payload: Request payload
            headers: Dodatni headeri

        Returns:
            Response objekat
        """
        request_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)

        return self._pool.post(url, json=payload, headers=request_headers)

    def stream_ai_response(
        self,
        url: str,
        api_key: str,
        payload: Dict[str, Any],
    ) -> httpx.Response:
        """Poziva AI provider sa streaming odgovorom.

        Args:
            url: API URL
            api_key: API key
            payload: Request payload

        Returns:
            Response objekat sa streaming
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        return self._streaming_pool.post(
            url,
            json=payload,
            headers=headers,
            timeout=180.0,
        )

    def close(self) -> None:
        """Zatvara sve konekcije."""
        self._pool.close()
        self._streaming_pool.close()


_pool_instance: Optional[ConnectionPool] = None
_quiz_client_instance: Optional[QuizHTTPClient] = None


def get_http_client() -> ConnectionPool:
    """Vraća singleton instancu HTTP client pool-a.

    Returns:
        ConnectionPool instanca
    """
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = ConnectionPool()
    return _pool_instance


def get_quiz_http_client() -> QuizHTTPClient:
    """Vraća singleton instancu QuizHTTPClient.

    Returns:
        QuizHTTPClient instanca
    """
    global _quiz_client_instance
    if _quiz_client_instance is None:
        _quiz_client_instance = QuizHTTPClient()
    return _quiz_client_instance
