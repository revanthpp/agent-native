from __future__ import annotations

import unittest
from unittest.mock import patch

from agentnative.acquisition.fetcher import AcquisitionError, Response, SafeFetcher
from agentnative.security.policy import NetworkPolicy, UnsafeTargetError, validate_network_url


class _FakeSocket:
    def __init__(self, chunks: list[bytes], error: BaseException | None = None) -> None:
        self.chunks = iter(chunks)
        self.error = error

    def settimeout(self, value: float) -> None:
        return

    def sendall(self, request: bytes) -> None:
        return

    def recv(self, size: int) -> bytes:
        if self.error is not None:
            raise self.error
        return next(self.chunks, b"")

    def close(self) -> None:
        return


class NetworkBoundaryTests(unittest.TestCase):
    def test_loopback_fixture_requires_explicit_policy(self) -> None:
        with self.assertRaises(UnsafeTargetError):
            validate_network_url("http://127.0.0.1:8000", NetworkPolicy())
        with patch("agentnative.security.policy.socket.getaddrinfo", return_value=[(0, 0, 0, "", ("127.0.0.1", 8000))]):
            self.assertEqual(
                validate_network_url("http://127.0.0.1:8000", NetworkPolicy(allow_local_http=True)),
                "http://127.0.0.1:8000",
            )

    def test_response_size_is_bounded(self) -> None:
        wire = b"HTTP/1.1 200 OK\r\nContent-Length: 128\r\n\r\n" + (b"x" * 128)
        with patch("agentnative.acquisition.fetcher.validate_network_url", side_effect=lambda value, policy: value), patch(
            "agentnative.acquisition.fetcher.resolve_public_addresses", return_value=["93.184.216.34"]
        ), patch(
            "agentnative.acquisition.fetcher.socket.create_connection", return_value=_FakeSocket([wire])
        ), patch(
            "agentnative.acquisition.fetcher.ssl.create_default_context"
        ) as context:
            context.return_value.wrap_socket.side_effect = lambda sock, server_hostname: sock
            with self.assertRaises(AcquisitionError):
                SafeFetcher(NetworkPolicy(max_response_bytes=32)).fetch("https://example.test/")

    def test_socket_timeout_is_an_acquisition_failure(self) -> None:
        with patch("agentnative.acquisition.fetcher.validate_network_url", side_effect=lambda value, policy: value), patch(
            "agentnative.acquisition.fetcher.resolve_public_addresses", return_value=["93.184.216.34"]
        ), patch(
            "agentnative.acquisition.fetcher.socket.create_connection",
            return_value=_FakeSocket([], TimeoutError("timed out")),
        ), patch(
            "agentnative.acquisition.fetcher.ssl.create_default_context"
        ) as context:
            context.return_value.wrap_socket.side_effect = lambda sock, server_hostname: sock
            with self.assertRaises(AcquisitionError):
                SafeFetcher(NetworkPolicy(timeout_seconds=0.01)).fetch("https://example.test/")

    def test_redirect_budget_is_bounded(self) -> None:
        fetcher = SafeFetcher(NetworkPolicy(max_redirects=1))
        with patch("agentnative.acquisition.fetcher.validate_network_url", side_effect=lambda value, policy: value), patch(
            "agentnative.acquisition.fetcher.SafeFetcher._request_once",
            return_value=Response("https://example.test/loop", 302, {"location": "/loop"}, b""),
        ):
            with self.assertRaises(AcquisitionError):
                fetcher.fetch("https://example.test/loop")

    def test_redirect_is_revalidated_before_private_request(self) -> None:
        fetcher = SafeFetcher()
        with patch(
            "agentnative.acquisition.fetcher.validate_network_url",
            side_effect=["https://example.test/", UnsafeTargetError("private redirect")],
        ) as validate, patch(
            "agentnative.acquisition.fetcher.SafeFetcher._request_once",
            return_value=Response("https://example.test/", 302, {"location": "http://10.0.0.1/private"}, b""),
        ) as request:
            with self.assertRaises(UnsafeTargetError):
                fetcher.fetch("https://example.test/")
        self.assertEqual(validate.call_count, 2)
        request.assert_called_once()

    def test_dns_rebinding_rechecks_resolution_before_connect(self) -> None:
        with patch(
            "agentnative.acquisition.fetcher.resolve_public_addresses",
            side_effect=[["93.184.216.34"], ["10.0.0.1"]],
        ), patch("agentnative.acquisition.fetcher.socket.create_connection") as connect:
            with self.assertRaises(UnsafeTargetError):
                SafeFetcher().fetch("https://example.test/")
        connect.assert_not_called()

    def test_mapped_ipv6_private_address_is_not_public(self) -> None:
        with patch("agentnative.security.policy.socket.getaddrinfo", return_value=[(0, 0, 0, "", ("::ffff:10.0.0.1", 443, 0, 0))]):
            with self.assertRaises(UnsafeTargetError):
                SafeFetcher().fetch("https://mapped.test/")


if __name__ == "__main__":
    unittest.main()
