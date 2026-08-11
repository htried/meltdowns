"""Mitmproxy addon for HTTP errors and content injection."""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Optional

from mitmproxy import ctx, http  # type: ignore[import-not-found]


class NoisyInterceptor:
    def __init__(self) -> None:
        self.blocked_domains: list[str] = []
        self.allowed_domains: list[str] = []
        self.error_mode = "404"
        self.template_dir = "/utils/templates"
        self.failure_rate = 1.0
        self.debug = False
        self.content_rules: list[Any] = []
        self.http_mode = "errors"
        self.blocked_fallback = False
        # "open" = legacy fault-injection only; "allowlist" = hard-deny non-allowed hosts.
        self.egress_mode = "open"
        self._content_init_done = False
        self._load_config()

    def _load_config(self) -> None:
        blocked = os.environ.get("BLOCKED_DOMAINS", "")
        if blocked:
            self.blocked_domains = [
                d.strip() for d in blocked.split(",") if d.strip()
            ]

        allowed = os.environ.get("ALLOWED_DOMAINS", "")
        if allowed:
            self.allowed_domains = [
                d.strip() for d in allowed.split(",") if d.strip()
            ]

        egress = os.environ.get("EGRESS_MODE", "open").strip().lower()
        self.egress_mode = egress if egress in ("allowlist", "open") else "open"

        self.error_mode = os.environ.get("NOISY_ERROR_MODE", "404")
        template_dir = os.environ.get("NOISY_TEMPLATE_DIR", "/utils/templates")
        if os.path.exists(template_dir):
            self.template_dir = template_dir

        try:
            self.failure_rate = float(
                os.environ.get("NETWORK_FAILURE_RATE", "1.0")
            )
        except ValueError:
            self.failure_rate = 1.0

        self.debug = os.environ.get("NOISY_DEBUG", "").lower() in (
            "1",
            "true",
            "yes",
        )
        self.blocked_fallback = os.environ.get("NOISY_BLOCKED_FALLBACK", "").lower() in (
            "1",
            "true",
            "yes",
        )

    def _blocked_fallback_response(self, host: str, path: str) -> http.Response:
        if path.endswith(".txt"):
            body = (
                "Container-hosted fallback response for blocked domain "
                f"{host}{path}."
            ).encode("utf-8")
            return http.Response.make(
                200,
                body,
                {
                    "Content-Type": "text/plain; charset=utf-8",
                    "X-Noisy-Hosted": "1",
                },
            )

        body = (
            "<html><body><h1>Container-hosted fallback</h1>"
            f"<p>Blocked domain: {host}</p>"
            f"<p>Path: {path}</p>"
            "</body></html>"
        ).encode("utf-8")
        return http.Response.make(
            200,
            body,
            {
                "Content-Type": "text/html; charset=utf-8",
                "X-Noisy-Hosted": "1",
            },
        )

    def _ensure_content_rules(self) -> None:
        if self._content_init_done:
            return
        self._content_init_done = True

        manifest_path = os.environ.get("NOISY_CONTENT_MANIFEST", "").strip()
        if manifest_path and os.path.isfile(manifest_path):
            try:
                from content_manifest import load_manifest

                self.content_rules = load_manifest(Path(manifest_path))
            except Exception as e:
                self.content_rules = []
                if self.debug:
                    ctx.log.warn(
                        f"[mitmproxy] NOISY_CONTENT_MANIFEST load failed: {e}"
                    )

        env_mode = os.environ.get("NOISY_HTTP_MODE", "").strip().lower()
        if env_mode in ("errors", "content", "both"):
            self.http_mode = env_mode
        else:
            self.http_mode = "both" if self.content_rules else "errors"

    def _is_allowed_domain(self, host: str) -> bool:
        if not self.allowed_domains:
            return False

        domain = host.split(":")[0]
        for allowed in self.allowed_domains:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True
        return False

    def _is_blocked_domain(self, host: str) -> bool:
        if not self.blocked_domains:
            return False

        domain = host.split(":")[0]
        for blocked in self.blocked_domains:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return True
        return False

    def _is_loopback_host(self, host: str) -> bool:
        domain = host.split(":")[0]
        return domain in ("localhost", "127.0.0.1", "::1")

    def _egress_allowed(self, host: str) -> bool:
        """Return True if the host may leave the container under current EGRESS_MODE."""
        if self._is_loopback_host(host):
            return True
        if self.egress_mode != "allowlist":
            return True
        return self._is_allowed_domain(host)

    def _egress_denied_response(self, host: str) -> http.Response:
        body = (
            "<html><body><h1>403 Forbidden</h1>"
            f"<p>Egress allowlist blocked host: {host}</p>"
            "</body></html>"
        ).encode("utf-8")
        return http.Response.make(
            403,
            body,
            {
                "Content-Type": "text/html; charset=utf-8",
                "X-Noisy-Egress": "denied",
            },
        )

    def _should_inject_host(self, host: str) -> bool:
        domain = host.split(":")[0]
        if domain in ("localhost", "127.0.0.1", "::1"):
            return False

        if self._is_allowed_domain(host):
            return False

        if not self.blocked_domains:
            return True

        return self._is_blocked_domain(host)

    def _status_code(self) -> Optional[int]:
        if self.error_mode == "403":
            return 403
        if self.error_mode == "429":
            return 429
        if self.error_mode == "5xx":
            return 503
        if self.error_mode == "404":
            return 404
        return None

    def _load_template(self, status_code: int) -> Optional[str]:
        if not os.path.exists(self.template_dir):
            return None

        template_path = os.path.join(self.template_dir, f"{status_code}.html")
        if not os.path.exists(template_path):
            return None

        try:
            with open(template_path, "r", encoding="utf-8") as file:
                return file.read()
        except OSError:
            return None

    def _fallback_body(self, status_code: int) -> bytes:
        if status_code == 403:
            title = "403 Forbidden"
            message = "You don't have permission to access this resource."
        elif status_code == 429:
            title = "429 Too Many Requests"
            message = "Rate limit exceeded. Please retry later."
        elif status_code == 404:
            title = "404 Not Found"
            message = "The requested URL was not found on this server."
        else:
            title = "503 Service Unavailable"
            message = "Service is temporarily unavailable."
        html = f"<html><body><h1>{title}</h1><p>{message}</p></body></html>"
        return html.encode("utf-8")

    def request(self, flow: http.HTTPFlow) -> None:
        self._ensure_content_rules()

        host = flow.request.pretty_host
        if not self._egress_allowed(host):
            if self.debug:
                ctx.log.info(f"[mitmproxy] Egress allowlist denied host {host}")
            flow.response = self._egress_denied_response(host)
            return

        if not self._should_inject_host(host):
            return

        path = flow.request.path.split("?", 1)[0]

        if self.http_mode in ("content", "both") and self.content_rules:
            from content_manifest import match_rule, response_bytes

            match = match_rule(self.content_rules, host, path)
            if match is not None:
                status, body, headers = response_bytes(match)
                if self.debug:
                    ctx.log.info(
                        (
                            f"[mitmproxy] Content injection {status} "
                            f"for {host}{path}"
                        )
                    )
                flow.response = http.Response.make(status, body, headers)
                return

        if self.blocked_fallback and self._is_blocked_domain(host):
            if self.debug:
                ctx.log.info(
                    f"[mitmproxy] Blocked-domain fallback response for {host}{path}"
                )
            flow.response = self._blocked_fallback_response(host, path)
            return

        if self.http_mode not in ("errors", "both"):
            return

        if random.random() >= self.failure_rate:
            return

        status_code = self._status_code()
        if status_code is None:
            return

        template = self._load_template(status_code)
        body = (
            template.encode("utf-8")
            if template
            else self._fallback_body(status_code)
        )

        if self.debug:
            ctx.log.info(f"[mitmproxy] Injecting {status_code} for host {host}")

        flow.response = http.Response.make(
            status_code,
            body,
            {"Content-Type": "text/html; charset=utf-8"},
        )


addons = [NoisyInterceptor()]
