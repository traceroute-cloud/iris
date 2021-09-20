import tempfile
from datetime import datetime

import pytest

from iris.api.dependencies import get_storage
from iris.api.targets import verify_probe_target_file, verify_target_file
from iris.commons.schemas.public import Paginated, Target, TargetSummary
from tests.helpers import fake_storage_factory, override

target1 = {
    "key": "test",
    "size": 42,
    "content": "1.1.1.0/24,icmp,2,32\n2.2.2.0/24,udp,5,20",
    "last_modified": "Mon, 20 Sep 2021 13:20:26 GMT",
    "metadata": None,
}

target_probes = {
    "key": "probes.csv",
    "size": 42,
    "content": "8.8.8.8,24000,33434,32,icmp",
    "last_modified": "Mon, 20 Sep 2021 13:20:26 GMT",
    "metadata": {"is_probes_file": "True"},
}

# --- GET /api/targets ---


@pytest.mark.asyncio
async def test_get_targets(api_client):
    override(api_client, get_storage, fake_storage_factory([target1, target_probes]))
    async with api_client as c:
        response = await c.get("/api/targets")
        assert Paginated[TargetSummary](**response.json()) == Paginated(
            count=2,
            results=[
                TargetSummary(
                    key="test",
                    last_modified=datetime(2021, 9, 20, 13, 20, 26),
                ),
                TargetSummary(
                    key="probes.csv",
                    last_modified=datetime(2021, 9, 20, 13, 20, 26),
                ),
            ],
        )


@pytest.mark.asyncio
async def test_get_targets_empty(api_client):
    override(api_client, get_storage, fake_storage_factory([]))
    async with api_client as c:
        response = await c.get("/api/targets")
        assert Paginated[TargetSummary](**response.json()) == Paginated(
            count=0, results=[]
        )


# --- GET /api/targets/{key} ---


@pytest.mark.asyncio
async def test_get_targets_by_key(api_client):
    override(api_client, get_storage, fake_storage_factory([target1]))
    async with api_client as c:
        response = await c.get("/api/targets/test")
        assert Target(**response.json()) == Target(
            key="test",
            size=42,
            content=["1.1.1.0/24,icmp,2,32", "2.2.2.0/24,udp,5,20"],
            last_modified=datetime(2021, 9, 20, 13, 20, 26),
        )


@pytest.mark.asyncio
async def test_get_probes_targets_by_key(api_client):
    override(api_client, get_storage, fake_storage_factory([target_probes]))
    async with api_client as c:
        response = await c.get("/api/targets/test")
        assert Target(**response.json()) == Target(
            key="probes.csv",
            size=42,
            content=["8.8.8.8,24000,33434,32,icmp"],
            last_modified=datetime(2021, 9, 20, 13, 20, 26),
        )


@pytest.mark.asyncio
async def test_get_targets_by_key_not_found(api_client):
    override(api_client, get_storage, fake_storage_factory([]))
    async with api_client as c:
        response = await c.get("/api/targets/test")
        assert response.status_code == 404


# --- POST /api/targets ---


@pytest.mark.asyncio
async def test_verify_prefixes_list_file():
    class FileContainer:
        def __init__(self):
            self.file = tempfile.SpooledTemporaryFile()

        def register(self, content):
            self.file = tempfile.SpooledTemporaryFile()
            self.file.write(content)
            self.file.seek(0)

    file_container = FileContainer()

    # Test with empty file
    file_container.register(b"")
    assert await verify_target_file(file_container) is False

    # Test with adhequate file
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,udp,5,20")
    assert await verify_target_file(file_container) is True

    # Test with inadhequate file
    file_container.register(b"1.1.1.1\ntest\n2.2.2.0/24")
    assert await verify_target_file(file_container) is False

    # Test with bad protocol
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,tcp,5,20")
    assert await verify_target_file(file_container) is False

    # Test with bad ttl
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,icmp,test,20")
    assert await verify_target_file(file_container) is False

    # Test with bad ttl
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,icmp,2,test")
    assert await verify_target_file(file_container) is False

    # Test with invalid ttl
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,icmp,test,500")
    assert await verify_target_file(file_container) is False

    # Test with invalid ttl
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,icmp,0,test")
    assert await verify_target_file(file_container) is False

    # Test with invalid ttl
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,icmp,-5,test")
    assert await verify_target_file(file_container) is False

    # Test with adhequate file with one trailing lines
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,udp,5,20\n")
    assert await verify_target_file(file_container) is True

    # Test with adhequate file with multiple trailing lines
    file_container.register(b"1.1.1.0/24,icmp,2,32\n2.2.2.0/24,udp,5,20\n\n")
    assert await verify_target_file(file_container) is False


# -- POST /api/targets/probes


@pytest.mark.asyncio
async def test_verify_probes_list_file():
    class FileContainer:
        def __init__(self):
            self.file = tempfile.SpooledTemporaryFile()

        def register(self, content):
            self.file = tempfile.SpooledTemporaryFile()
            self.file.write(content)
            self.file.seek(0)

    file_container = FileContainer()

    # Test with adhequate file
    file_container.register(
        b"8.8.8.8,24000,33434,32,icmp\n2001:4860:4860::8888,24000,33434,32,icmp"
    )
    assert await verify_probe_target_file(file_container) is True

    # Test with invalid destination address
    file_container.register(b"8.8.453.8,24000,33434,32,icmp")
    assert await verify_probe_target_file(file_container) is False

    # Test with invalid port
    file_container.register(b"8.8.8.8,24000,0,32,icmp")
    assert await verify_probe_target_file(file_container) is False

    # Test with invalid protocol
    file_container.register(b"8.8.8.8,24000,33434,32,icmt")
    assert await verify_probe_target_file(file_container) is False


# --- DELETE /api/targets/{key} ---


@pytest.mark.asyncio
async def test_delete_targets_by_key(api_client):
    override(api_client, get_storage, fake_storage_factory([target1]))
    async with api_client as c:
        response = await c.delete("/api/targets/test")
        assert response.json() == {"key": "test", "action": "delete"}


@pytest.mark.asyncio
async def test_delete_targets_by_key_not_found(api_client):
    override(api_client, get_storage, fake_storage_factory([]))
    async with api_client as c:
        response = await c.delete("/api/targets/test")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_targets_internal_error(api_client):
    class FakeStorage:
        async def delete_file_check_no_retry(*args, **kwargs):
            return {"ResponseMetadata": {"HTTPStatusCode": 500}}

    override(api_client, get_storage, lambda: FakeStorage())
    async with api_client as c:
        response = await c.delete("/api/targets/test")
        assert response.status_code == 500
