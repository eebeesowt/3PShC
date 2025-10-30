import hashlib
import asyncio
from lib.constants import (
    ProjectorCommands,
    ProjectorResponses,
    ProjectorProtocol,
    ProjectorStates
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Projector:
    def __init__(self, ip, port, login, password, label, id) -> None:
        self.ip = ip
        self.ip_room_nomber = ip.split('.')[-1]
        self.port = port
        self.login = login
        self.password = password
        self.label = label if label else ip
        self.id = id

        self.power = None
        self.group = False
        self.shutter = None
        self.shutter_in_time = None
        self.shutter_out_time = None
        self.shutter_time_dict = ProjectorStates.SHUTTER_TIME_OPTIONS
        self.SHUTTER_OPEN = ProjectorStates.SHUTTER_OPEN
        self.SHUTER_CLOSED = ProjectorStates.SHUTTER_CLOSED

    async def send_cmd(self, cmd, timeout=ProjectorProtocol.DEFAULT_TIMEOUT):
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout
            )
        except Exception as e:
            logger.warning(f"Connection attempt failed for {self.ip}:{self.port}: {e}")
            raise asyncio.TimeoutError(
                f"Connection to {self.ip}:{self.port} timed out") from e
        try:
            serv_answer = await asyncio.wait_for(
                reader.read(ProjectorProtocol.INITIAL_BUFFER_SIZE), timeout
            )
            decode_answer = serv_answer.decode()
            rand_num = decode_answer.split(' ')[-1][0:-1]
            auth_data = f'{self.login}:{self.password}:{rand_num}'
            md5hash = hashlib.md5(auth_data.encode())
            command = (
                md5hash.hexdigest() +
                ProjectorProtocol.PADDING_CHAR +
                ProjectorProtocol.PADDING_CHAR +
                cmd +
                ProjectorProtocol.TERMINATOR
            )
            writer.write(command.encode())
            await writer.drain()
            answ = await asyncio.wait_for(
                reader.read(ProjectorProtocol.RESPONSE_BUFFER_SIZE), timeout
            )
            decode_answer = answ.decode()[2:-1]
        except asyncio.TimeoutError:
            logger.warning(f'Connection timed out for {self.ip}')
            decode_answer = ProjectorResponses.TIMEOUT
        except Exception as exc:
            logger.error(f'Connection error for {self.ip}: {exc}')
            raise exc
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
        return decode_answer

    async def get_info(self):
        try:
            power = await self.send_cmd(ProjectorCommands.QUERY_POWER)
        except Exception as e:
            logger.error(f"Error getting power state for {self.label}: {e}")
            return
        else:
            if power == ProjectorResponses.POWER_ON:
                self.power = True
                shutter = await self.send_cmd(ProjectorCommands.QUERY_SHUTTER)
                if shutter == ProjectorResponses.SHUTTER_OPEN:
                    self.shutter = self.SHUTTER_OPEN
                elif shutter == ProjectorResponses.SHUTTER_CLOSED:
                    self.shutter = self.SHUTER_CLOSED
            elif power == ProjectorResponses.POWER_OFF:
                self.power = False
            else:
                raise ValueError(f'Unknown power state: {power}')

        get_shutter_in = await self.send_cmd(ProjectorCommands.QUERY_SHUTTER_IN)
        answer_shutter_in_time = get_shutter_in.split('=')
        self.shutter_in_time = answer_shutter_in_time[1] if (
            len(answer_shutter_in_time) > 1) else 'None'

        get_shutter_out = await self.send_cmd(ProjectorCommands.QUERY_SHUTTER_OUT)
        answer_shutter_out_time = get_shutter_out.split('=')
        self.shutter_out_time = answer_shutter_out_time[1] if (
            len(answer_shutter_out_time) > 1) else 'None'

    async def power_on(self):
        await self.send_cmd(ProjectorCommands.POWER_ON)
        self.power = True

    async def power_off(self):
        await self.send_cmd(ProjectorCommands.POWER_OFF)
        self.power = False

    async def shutter_open(self):
        await self.send_cmd(ProjectorCommands.SHUTTER_OPEN)
        self.shutter = self.SHUTTER_OPEN

    async def shutter_close(self):
        await self.send_cmd(ProjectorCommands.SHUTTER_CLOSE)
        self.shutter = self.SHUTER_CLOSED

    async def set_shutter_in(self, shutter_time):
        await self.send_cmd(ProjectorCommands.SET_SHUTTER_IN.format(shutter_time))

    async def set_shutter_out(self, shutter_time):
        await self.send_cmd(ProjectorCommands.SET_SHUTTER_OUT.format(shutter_time))

    def debug_info(self):
        """Вывести отладочную информацию о проекторе"""
        info = f"""
    IP--------{self.ip}
    PORT------{self.port}
    LOGIN-----{self.login}
    PASSWORD--{self.password}
    LABEL-----{self.label}
    ID--------{self.id}
    POWER-----{self.power}
    GROUP-----{self.group}
    SHUTTER---{self.shutter}
    SHUTTER_IN---{self.shutter_in_time}
    SHUTTER_OUT---{self.shutter_out_time}
        """
        logger.debug(info)
