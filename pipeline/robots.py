"""robots.txt matching per RFC 9309 (wildcards * and $, longest match wins, allow wins ties).

Python's urllib.robotparser ignores wildcards (so "Disallow: /Uploads/*" never matched) and treats a
403 on robots.txt as "disallow all", which RFC 9309 section 2.3.1.3 does not. This module replaces it.
"""
import contextlib
import re
from urllib.parse import unquote, urlsplit

TOKEN = "clearTab-capstone".lower()


def _pattern(path: str) -> re.Pattern:
    anchored = path.endswith("$")
    body = re.escape(path.rstrip("$")).replace(r"\*", ".*")
    return re.compile(body + ("$" if anchored else ""))


class Robots:
    def __init__(self, status: int | None, text: str = ""):
        self.status = status
        self.rules: list[tuple[bool, str, re.Pattern]] = []
        self.crawl_delay: float | None = None
        # 5xx or unreachable: RFC 9309 says assume complete disallow. 4xx: no restrictions.
        self.disallow_all = status is None or status >= 500
        if status is not None and 200 <= status < 300:
            self._parse(text)

    def _parse(self, text: str) -> None:
        groups: list[tuple[set[str], list[tuple[str, str]]]] = []
        agents: set[str] = set()
        rules: list[tuple[str, str]] = []
        last_was_agent = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (p.strip() for p in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if not last_was_agent and (agents or rules):
                    groups.append((agents, rules))
                    agents, rules = set(), []
                agents.add(value.lower())
                last_was_agent = True
            elif key in ("allow", "disallow", "crawl-delay"):
                rules.append((key, value))
                last_was_agent = False
        if agents or rules:
            groups.append((agents, rules))
        chosen = [r for a, r in groups if any(x and x != "*" and x in TOKEN for x in a)]
        if not chosen:
            chosen = [r for a, r in groups if "*" in a]
        for rules in chosen:
            for key, value in rules:
                if key == "crawl-delay":
                    with contextlib.suppress(ValueError):
                        self.crawl_delay = float(value)
                elif value:  # an empty Disallow allows everything
                    self.rules.append((key == "allow", value, _pattern(value)))

    def can_fetch(self, url: str) -> bool:
        if self.disallow_all:
            return False
        parts = urlsplit(url)
        path = unquote(parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        best_len, allowed = -1, True
        for allow, raw, pat in self.rules:
            if pat.match(path):
                n = len(raw)
                if n > best_len or (n == best_len and allow):
                    best_len, allowed = n, allow
        return allowed
