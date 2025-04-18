import hashlib
import asyncio


class Projector:
    def __init__(self, ip, port, login, password, label, id) -> None:
        self.ip = ip
        self.ip_room_nomber = ip.split('.')[-1]
        self.port = port
        self.login = login
        self.password = password
        self.label = label
        self.id = id
        if label == '':
            self.label = ip

        self.power = None
        self.group = False
        self.shutter = None
        self.shutter_in_time = None
        self.shutter_out_time = None
        self.shutter_time_dict = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5,
                                  3.0, 3.5, 4.0, 5.0, 7.0, 10.0]
        self.SHUTTER_OPEN = False
        self.SHUTER_CLOSED = True

    async def send_cmd(self, cmd, timeout=2):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout
            )
        except Exception as e:
            raise asyncio.TimeoutError(
                f"Connection to {self.ip}:{self.port} timed out") from e
        try:
            serv_answer = await asyncio.wait_for(reader.read(1024), timeout)
            decode_answer = serv_answer.decode()
            rand_num = decode_answer.split(' ')[-1][0:-1]
            auth_data = f'{self.login}:{self.password}:{rand_num}'
            md5hash = hashlib.md5(auth_data.encode())
            command = md5hash.hexdigest() + chr(48) + chr(48) + cmd + chr(13)
            writer.write(command.encode())
            await writer.drain()
            answ = await asyncio.wait_for(reader.read(21), timeout)
            decode_answer = answ.decode()[2:-1]
        except asyncio.TimeoutError:
            print('Connection timed out')
            decode_answer = 'Timeout'
        except Exception as exc:
            print('Connection error:', exc)
            raise exc
        finally:
            writer.close()
            await writer.wait_closed()
        return decode_answer

    async def get_info(self):
        try:
            power = await self.send_cmd('QPW')
        except Exception as e:
            print(f"Error getting power state: {e}")
            return
        else:
            if power == '001':
                self.power = True
                shutter = await self.send_cmd('QSH')
                if shutter == '0':
                    self.shutter = self.SHUTTER_OPEN
                elif shutter == '1':
                    self.shutter = self.SHUTER_CLOSED
            elif power == '000':
                self.power = False
            else:
                raise ValueError('Unknown power state')

        get_shutter_in = await self.send_cmd('QVX:SEFS1')
        answer_shutter_in_time = get_shutter_in.split('=')
        self.shutter_in_time = answer_shutter_in_time[1] if (
            len(answer_shutter_in_time) > 1) else 'None'

        get_shutter_out = await self.send_cmd('QVX:SEFS2')
        answer_shutter_out_time = get_shutter_out.split('=')
        self.shutter_out_time = answer_shutter_out_time[1] if (
            len(answer_shutter_out_time) > 1) else 'None'

    async def power_on(self):
        await self.send_cmd('PON')
        self.power = True

    async def power_off(self):
        await self.send_cmd('POF')
        self.power = False

    async def shutter_open(self):
        await self.send_cmd('OSH:0')
        self.shutter = self.SHUTTER_OPEN

    async def shutter_close(self):
        await self.send_cmd('OSH:1')
        self.shutter = self.SHUTER_CLOSED

    async def set_shutter_in(self, shutter_time):
        await self.send_cmd(f'VXX:SEFS1={shutter_time}')

    async def set_shutter_out(self, shutter_time):
        await self.send_cmd(f'VXX:SEFS2={shutter_time}')

    def debug_info(self):
        print(
            f'''
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
        '''
        )
