import asyncio

import crear_superadmin


class _DummyConnection:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def run_sync(self, fn):
        fn(None)


class _DummyEngine:
    def begin(self):
        return _DummyConnection()


class _DummyMetadata:
    def __init__(self):
        self.calls = []

    def create_all(self, bind):
        self.calls.append(bind)


def test_ensure_schema_creates_tables(monkeypatch):
    metadata = _DummyMetadata()
    monkeypatch.setattr(crear_superadmin, "engine", _DummyEngine())
    monkeypatch.setattr(crear_superadmin, "metadata", metadata)

    asyncio.run(crear_superadmin._ensure_schema())

    assert metadata.calls == [None]
