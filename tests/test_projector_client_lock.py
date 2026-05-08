"""Тест на сериализацию: ProjectorClient.send_raw НЕ должен иметь две
параллельные транзакции к одному IP. Фикс бага A из ревью.
"""
import asyncio
from unittest.mock import patch, AsyncMock

from core.models import ProjectorConfig
from infra.projector_client import ProjectorClient


def test_send_raw_serializes_concurrent_calls():
    """Десять параллельных send_raw на одном клиенте должны выполниться
    строго последовательно (как требует Panasonic NTCONTROL)."""
    config = ProjectorConfig(
        ip='10.0.0.10', port=1024, login='admin', password='pwd', label='X',
    )
    client = ProjectorClient(config)

    in_flight = 0
    max_in_flight = 0

    async def fake_unlocked(cmd, timeout):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.01)  # имитируем TCP-задержку
        in_flight -= 1
        return '0'

    async def run():
        with patch.object(client, '_send_unlocked', side_effect=fake_unlocked):
            await asyncio.gather(*[client.send_raw('QPW') for _ in range(10)])

    asyncio.run(run())
    # Если лок работает — никогда больше одной транзакции одновременно.
    assert max_in_flight == 1, f"expected 1 concurrent send, got {max_in_flight}"


def test_send_raw_locks_are_per_instance():
    """Лок должен быть на инстанс — два разных проектора параллельны."""
    cfg_a = ProjectorConfig(ip='10.0.0.10', port=1024, login='a', password='b', label='A')
    cfg_b = ProjectorConfig(ip='10.0.0.20', port=1024, login='a', password='b', label='B')
    client_a = ProjectorClient(cfg_a)
    client_b = ProjectorClient(cfg_b)

    in_flight = 0
    max_in_flight = 0

    async def fake_unlocked(cmd, timeout):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.02)
        in_flight -= 1
        return '0'

    async def run():
        with patch.object(client_a, '_send_unlocked', side_effect=fake_unlocked), \
             patch.object(client_b, '_send_unlocked', side_effect=fake_unlocked):
            await asyncio.gather(
                client_a.send_raw('QPW'),
                client_b.send_raw('QPW'),
            )

    asyncio.run(run())
    assert max_in_flight == 2, "different projectors must run in parallel"
