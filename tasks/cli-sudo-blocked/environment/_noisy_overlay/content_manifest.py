"""Load and match NOISY_CONTENT_MANIFEST rules for MITM content injection."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

ALLOWED_RULE_KEYS = frozenset(
    {
        "host",
        "host_suffix",
        "path_prefix",
        "file",
        "body",
        "content_type",
        "status",
        "headers",
    }
)


@dataclass
class ContentMatch:
    """A matched rule: either a file path or inline body to return."""

    body_path: Optional[Path] = None
    body_text: Optional[str] = None
    content_type: str = "text/html; charset=utf-8"
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ContentRule:
    """Internal normalized rule for matching."""

    host_exact: Optional[str]
    host_suffix: Optional[str]
    path_prefix: str
    match: ContentMatch


def _validate_rule_keys(rule: dict[str, Any], index: int) -> None:
    extra = set(rule.keys()) - ALLOWED_RULE_KEYS
    if extra:
        raise ValueError(
            f"Rule {index}: unknown keys {sorted(extra)}; allowed: {sorted(ALLOWED_RULE_KEYS)}"
        )


def _normalize_path_prefix(prefix: str) -> str:
    if not prefix.startswith("/"):
        return "/" + prefix
    return prefix


def load_manifest(manifest_path: Path) -> list[ContentRule]:
    """Load JSON manifest from disk. Raises ValueError on invalid schema."""
    path = manifest_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Manifest root must be a JSON object")

    rules_raw = raw.get("rules")
    if rules_raw is None:
        raise ValueError("Manifest must contain a 'rules' array")
    if not isinstance(rules_raw, list):
        raise ValueError("'rules' must be an array")

    base_dir = path.parent
    out: list[ContentRule] = []

    for i, item in enumerate(rules_raw):
        if not isinstance(item, dict):
            raise ValueError(f"Rule {i}: must be an object")
        _validate_rule_keys(item, i)

        host_exact = item.get("host")
        host_suffix = item.get("host_suffix")
        if host_exact is not None and host_suffix is not None:
            raise ValueError(f"Rule {i}: use only one of 'host' or 'host_suffix'")
        if host_exact is None and host_suffix is None:
            raise ValueError(f"Rule {i}: need 'host' or 'host_suffix'")

        if host_exact is not None and not isinstance(host_exact, str):
            raise ValueError(f"Rule {i}: 'host' must be a string")
        if host_suffix is not None and not isinstance(host_suffix, str):
            raise ValueError(f"Rule {i}: 'host_suffix' must be a string")

        path_prefix = item.get("path_prefix")
        if path_prefix is None:
            raise ValueError(f"Rule {i}: 'path_prefix' is required")
        if not isinstance(path_prefix, str):
            raise ValueError(f"Rule {i}: 'path_prefix' must be a string")
        path_prefix = _normalize_path_prefix(path_prefix)

        file_ref = item.get("file")
        body_inline = item.get("body")
        if (file_ref is None) == (body_inline is None):
            raise ValueError(f"Rule {i}: exactly one of 'file' or 'body' is required")

        content_type = item.get("content_type", "text/html; charset=utf-8")
        if not isinstance(content_type, str):
            raise ValueError(f"Rule {i}: 'content_type' must be a string")

        status = item.get("status", 200)
        if not isinstance(status, int) or status < 100 or status > 599:
            raise ValueError(f"Rule {i}: 'status' must be an int HTTP status")

        headers: dict[str, str] = {}
        if "headers" in item:
            h = item["headers"]
            if not isinstance(h, dict):
                raise ValueError(f"Rule {i}: 'headers' must be an object")
            for hk, hv in h.items():
                if not isinstance(hk, str) or not isinstance(hv, str):
                    raise ValueError(f"Rule {i}: header names and values must be strings")
                headers[hk] = hv

        if file_ref is not None:
            if not isinstance(file_ref, str):
                raise ValueError(f"Rule {i}: 'file' must be a string")
            if Path(file_ref).is_absolute():
                raise ValueError(f"Rule {i}: 'file' must be relative to the manifest directory")
            body_path = (base_dir / file_ref).resolve()
            try:
                body_path.relative_to(base_dir.resolve())
            except ValueError as e:
                raise ValueError(f"Rule {i}: 'file' must stay under manifest directory") from e
            match = ContentMatch(
                body_path=body_path,
                content_type=content_type,
                status_code=status,
                headers=headers,
            )
        else:
            assert body_inline is not None
            if not isinstance(body_inline, str):
                raise ValueError(f"Rule {i}: 'body' must be a string")
            match = ContentMatch(
                body_text=body_inline,
                content_type=content_type,
                status_code=status,
                headers=headers,
            )

        out.append(
            ContentRule(
                host_exact=host_exact.lower() if host_exact else None,
                host_suffix=host_suffix.lower() if host_suffix else None,
                path_prefix=path_prefix,
                match=match,
            )
        )

    return out


def _host_matches(rule: ContentRule, host: str) -> bool:
    h = host.split(":")[0].lower()
    if rule.host_exact is not None:
        return h == rule.host_exact
    assert rule.host_suffix is not None
    suf = rule.host_suffix
    return h == suf or h.endswith("." + suf)


def _path_matches(path_prefix: str, request_path: str) -> bool:
    p = request_path if request_path.startswith("/") else "/" + request_path
    pre = path_prefix.rstrip("/") or "/"
    if pre == "/":
        return True
    return p == pre or p.startswith(pre + "/")


def match_rule(rules: list[ContentRule], host: str, path: str) -> Optional[ContentMatch]:
    """First matching rule wins. Returns None if no rule matches."""
    for rule in rules:
        if not _host_matches(rule, host):
            continue
        if not _path_matches(rule.path_prefix, path):
            continue
        return rule.match
    return None


def response_bytes(match: ContentMatch) -> tuple[int, bytes, dict[str, str]]:
    """HTTP status, body, headers (including Content-Type) for mitmproxy."""
    if match.body_path is not None:
        body = match.body_path.read_bytes()
    elif match.body_text is not None:
        body = match.body_text.encode("utf-8")
    else:
        body = b""
    headers: dict[str, str] = {"Content-Type": match.content_type}
    headers.update(match.headers)
    return match.status_code, body, headers
