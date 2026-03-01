"""LMDB read layer for Reqable's ObjectBox database."""

from __future__ import annotations

import base64
import gzip
import json
import os
import re
import struct
from typing import Any, Generator

import lmdb

# ObjectBox key prefixes (first 4 bytes of 8-byte keys)
PREFIX_CAPTURE = b"\x18\x00\x00\x2c"   # Proxy capture records
PREFIX_API_TEST = b"\x18\x00\x00\x3c"  # API test records
PREFIX_COOKIE = b"\x18\x00\x00\x40"    # Cookie storage
PREFIX_API_COLLECTION = b"\x18\x00\x00\x7c"  # API collection

_GZIP_B64_RE = re.compile(r"H4sI[A-Za-z0-9+/=]{20,}")


def _default_db_path() -> str:
    return os.path.join(os.environ.get("APPDATA", ""), "Reqable", "box")


def _default_capture_dir() -> str:
    return os.path.join(os.environ.get("APPDATA", ""), "Reqable", "capture")


class ReqableDB:
    """Read-only accessor for Reqable's ObjectBox LMDB database."""

    def __init__(
        self,
        db_path: str | None = None,
        capture_dir: str | None = None,
    ) -> None:
        self.db_path = db_path or _default_db_path()
        self.capture_dir = capture_dir or _default_capture_dir()
        self._env: lmdb.Environment | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> None:
        if self._env is not None:
            return
        self._env = lmdb.open(
            self.db_path,
            readonly=True,
            lock=False,
            max_dbs=128,
            map_size=2 * 1024 * 1024 * 1024,  # 2 GB map
        )

    def close(self) -> None:
        if self._env is not None:
            self._env.close()
            self._env = None

    @property
    def env(self) -> lmdb.Environment:
        if self._env is None:
            self.open()
        assert self._env is not None
        return self._env

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_gzip_b64(raw: bytes) -> dict[str, Any] | None:
        """Extract gzip+base64 JSON embedded in a FlatBuffers value."""
        text = raw.decode("utf-8", errors="replace")
        for match in _GZIP_B64_RE.finditer(text):
            try:
                decoded = base64.b64decode(match.group())
                decompressed = gzip.decompress(decoded)
                return json.loads(decompressed)
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_json_objects(raw: bytes) -> list[dict[str, Any]]:
        """Extract top-level JSON objects embedded in binary data."""
        results: list[dict[str, Any]] = []
        i = 0
        length = len(raw)
        while i < length:
            if raw[i : i + 1] != b"{":
                i += 1
                continue
            depth = 0
            start = i
            for j in range(i, length):
                if raw[j : j + 1] == b"{":
                    depth += 1
                elif raw[j : j + 1] == b"}":
                    depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(raw[start : j + 1])
                            results.append(obj)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass
                        i = j + 1
                        break
            else:
                break
        return results

    @staticmethod
    def _entity_id(key: bytes) -> int:
        """Extract the entity ID (last 4 bytes, big-endian) from an 8-byte key."""
        return struct.unpack(">I", key[4:8])[0]

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def _iter_prefix(self, prefix: bytes) -> Generator[tuple[int, bytes], None, None]:
        """Yield (entity_id, raw_value) for all records matching *prefix*."""
        with self.env.begin() as txn:
            cursor = txn.cursor()
            for key, value in cursor:
                if key[:4] == prefix:
                    yield self._entity_id(key), value

    def iter_captures(self) -> Generator[tuple[int, dict[str, Any]], None, None]:
        """Yield (entity_id, parsed_dict) for proxy capture records."""
        for eid, raw in self._iter_prefix(PREFIX_CAPTURE):
            parsed = self._decode_gzip_b64(raw)
            if parsed is not None:
                yield eid, parsed

    def iter_api_tests(self) -> Generator[tuple[int, dict[str, Any]], None, None]:
        """Yield (entity_id, parsed_dict) for API test records."""
        for eid, raw in self._iter_prefix(PREFIX_API_TEST):
            objects = self._extract_json_objects(raw)
            for obj in objects:
                if "request" in obj or "api" in obj:
                    yield eid, obj
                    break

    # ------------------------------------------------------------------
    # Single-record lookups
    # ------------------------------------------------------------------

    def get_capture(self, record_id: int) -> dict[str, Any] | None:
        """Return parsed capture record by its ``id`` field, or *None*."""
        for _, parsed in self.iter_captures():
            if parsed.get("id") == record_id:
                return parsed
        return None

    def get_api_test(self, entity_id: int) -> dict[str, Any] | None:
        """Return parsed API test record by entity ID, or *None*."""
        for eid, parsed in self.iter_api_tests():
            if eid == entity_id:
                return parsed
        return None
