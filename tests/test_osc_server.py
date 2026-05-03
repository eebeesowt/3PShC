"""
Smoke-тест нового OSCController на oscpy. Поднимает сервер на свободном
порту и шлёт OSC-сообщения через локальный клиент, проверяет что
обработчики вызываются с правильными аргументами через asyncio-loop.
"""
import asyncio
import socket

from oscpy.client import OSCClient

from infra.osc_server import OSCController, OSCEvent


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


async def _scenario(send_addr: str, expected_event: str, expected_args: tuple):
    port = _free_port()
    osc = OSCController(host="127.0.0.1", port=port)
    received: list = []
    done = asyncio.Event()

    def handler(*args):
        received.append(args)
        done.set()

    osc.on(expected_event, handler)
    await osc.start()
    try:
        client = OSCClient("127.0.0.1", port)
        client.send_message(send_addr.encode(), [3])  # button press
        try:
            await asyncio.wait_for(done.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pass
        assert received, f"handler for {expected_event} was not called"
        assert received[0] == expected_args, received
    finally:
        osc.stop()


def test_osc_shutter_open_routes_room_number():
    asyncio.run(_scenario("/shutter/open/42", OSCEvent.SHUTTER_OPEN, ("42",)))


def test_osc_shutter_close_routes_room_number():
    asyncio.run(_scenario("/shutter/close/13", OSCEvent.SHUTTER_CLOSE, ("13",)))


def test_osc_group_open_no_args():
    asyncio.run(_scenario("/shutter/group/open", OSCEvent.GROUP_OPEN, ()))


def test_osc_group_close_no_args():
    asyncio.run(_scenario("/shutter/group/close", OSCEvent.GROUP_CLOSE, ()))
