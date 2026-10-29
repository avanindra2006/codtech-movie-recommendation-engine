"""Small, bounded, cached Cinemeta synopsis requests; never used as training features."""

import html
import json
import re
import time
import urllib.request
from collections import OrderedDict
from concurrent.futures import Future, TimeoutError
from http.client import HTTPException
from threading import BoundedSemaphore, Lock


def short_description(payload, imdb_id):
    meta = payload.get("meta") if isinstance(payload, dict) else None
    if not isinstance(meta, dict) or meta.get("id") != imdb_id:
        return None
    text = meta.get("description")
    if not isinstance(text, str):
        return None
    text = " ".join(re.sub(r"<[^>]*>", "", html.unescape(text)).split())
    if not text:
        return None
    return text if len(text) <= 320 else text[:317].rsplit(" ", 1)[0] + "…"


class MovieMetadata:
    def __init__(self, fetcher=None):
        self._fetcher = fetcher or self._fetch
        self._cache = OrderedDict()
        self._pending = {}
        self._guard = Lock()
        self._slots = BoundedSemaphore(4)

    @staticmethod
    def _fetch(imdb_id):
        if not re.fullmatch(r"tt\d{7,10}", imdb_id):
            return None
        url = f"https://v3-cinemeta.strem.io/meta/movie/{imdb_id}.json"
        request = urllib.request.Request(url, headers={"User-Agent": "CineMatch/1.0"})
        with urllib.request.urlopen(request, timeout=6) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            return None
        return short_description(json.loads(data), imdb_id)

    def get(self, imdb_id):
        if not re.fullmatch(r"tt\d{7,10}", imdb_id):
            return None
        with self._guard:
            cached = self._cache.get(imdb_id)
            if cached and cached[0] > time.monotonic():
                self._cache.move_to_end(imdb_id)
                return cached[1]
            future = self._pending.get(imdb_id)
            owner = future is None
            if owner:
                future = Future()
                self._pending[imdb_id] = future
        if not owner:
            try:
                return future.result(timeout=8)
            except TimeoutError:
                return None
        result = None
        acquired = self._slots.acquire(timeout=1)
        try:
            if acquired:
                result = self._fetcher(imdb_id)
        except (OSError, ValueError, TypeError, HTTPException):
            # An optional API outage must not make movie discovery fail.
            result = None
        finally:
            if acquired:
                self._slots.release()
            with self._guard:
                self._cache[imdb_id] = (time.monotonic() + (86400 if result else 120), result)
                self._cache.move_to_end(imdb_id)
                while len(self._cache) > 2048:
                    self._cache.popitem(last=False)
                self._pending.pop(imdb_id, None)
                future.set_result(result)
        return result
