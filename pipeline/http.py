"""Polite HTTP access: robots.txt check, 1 request per second per domain, ClearTab user agent."""
import time
from urllib.parse import urlsplit

import requests

from pipeline.common import USER_AGENT
from pipeline.robots import Robots


class RobotsDisallowed(Exception):
    pass


class PoliteSession:
    def __init__(self, min_interval: float = 1.0):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.min_interval = min_interval
        self._last: dict[str, float] = {}
        self._robots: dict[str, Robots] = {}
        self._crawl_delay: dict[str, float] = {}
        self.robots_text: dict[str, str] = {}

    def _wait(self, host: str) -> None:
        gap = max(self.min_interval, self._crawl_delay.get(host, 0))
        elapsed = time.monotonic() - self._last.get(host, 0)
        if elapsed < gap:
            time.sleep(gap - elapsed)
        self._last[host] = time.monotonic()

    def robots(self, url: str) -> Robots:
        parts = urlsplit(url)
        host = parts.netloc
        if host not in self._robots:
            self._wait(host)
            try:
                r = self.s.get(f"{parts.scheme}://{host}/robots.txt", timeout=30)
                looks_html = r.text.lstrip()[:15].lower().startswith(("<!doctype", "<html"))
                text = "" if looks_html else r.text
                self.robots_text[host] = f"HTTP {r.status_code}" + (" (HTML page, no rules)" if looks_html else "")
                self.robots_text[host] += "\n" + text[:5000]
                rob = Robots(r.status_code, text)
            except requests.RequestException as e:
                self.robots_text[host] = f"unreachable: {str(e)[:200]}"
                rob = Robots(None)
            if rob.crawl_delay:
                self._crawl_delay[host] = rob.crawl_delay
            self._robots[host] = rob
        return self._robots[host]

    def allowed(self, url: str) -> bool:
        return self.robots(url).can_fetch(url)

    def request(self, method: str, url: str, **kw) -> requests.Response:
        if not self.allowed(url):
            raise RobotsDisallowed(url)
        self._wait(urlsplit(url).netloc)
        kw.setdefault("timeout", 60)
        return self.s.request(method, url, **kw)

    def get(self, url: str, **kw) -> requests.Response:
        return self.request("GET", url, **kw)

    def head(self, url: str, **kw) -> requests.Response:
        kw.setdefault("allow_redirects", True)
        return self.request("HEAD", url, **kw)
