import hashlib
import asyncio


class Projector:
    def __init__(self, ip, port, login, password, label, id) -> None:
        self.ip = ip
        self.port = port
        self.login = login
        self.password = password
        self.label = label
        self.id = id
        if label == '':
            self.label = ip

        self.power = None
        self.screen_format = None
        self.input = None
        self.group = False
        self.shutter = None
        self.shutter_in_time = None
        self.shutter_out_time = None

        self.screen_dict = {
            '0': '16:10',
            '1': '16:9',
            '2': '4:3'
        }
        self.input_dict = {
            'RG1': 'COMPUTER1',
            'RG2': 'COMPUTER2',
            'VID': 'VIDEO',
            'SVD': 'Y/C',
            'DVI': 'DVI',
            'HD1': 'HDMI',
            'SD1': 'SDI',
            'DL1:HD1': 'Digital Link HD1',
            'DL1:HD2': 'Digital Link HD2',
        }

        self.shutter_time_dict = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5,
                                  3.0, 3.5, 4.0, 5.0, 7.0, 10.0]

    async def send_cmd(self, cmd, timeout=5):
        reader, writer = await asyncio.open_connection(self.ip,
                                                       self.port)
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
        power = await self.send_cmd('QPW')
        if power == '001':
            self.power = True
            shutter = await self.send_cmd('QSH')
            self.shutter = shutter == '0'
        else:
            self.power = False
        self.input = self.input_dict[await self.send_cmd('QIN')]
        get_shutter_in = await self.send_cmd('QVX:SEFS1')
        answer_shutter_in_time = get_shutter_in.split('=')
        self.shutter_in_time = answer_shutter_in_time[1] if (
            len(answer_shutter_in_time) > 1) else 'None'
        get_shutter_out = await self.send_cmd('QVX:SEFS2')
        answer_shutter_out_time = get_shutter_out.split('=')
        self.shutter_out_time = answer_shutter_out_time[1] if (
            len(answer_shutter_out_time) > 1) else 'None'
            
        srn_frmt_answr = await self.send_cmd('QSF')
        if srn_frmt_answr in self.screen_dict.keys():
            self.screen_format = self.screen_dict[srn_frmt_answr]
        else:
            self.screen_format = 'None'

    async def power_on(self):
        await self.send_cmd('PON')

    async def power_off(self):
        await self.send_cmd('POF')

    async def shutter_open(self):
        await self.send_cmd('OSH:0')
        self.shutter = True

    async def shutter_close(self):
        await self.send_cmd('OSH:1')
        self.shutter = False

    async def shutter_in(self, shutter_time):
        await self.send_cmd(f'VXX:SEFS1={shutter_time}')

    async def shutter_out(self, shutter_time):
        await self.send_cmd(f'VXX:SEFS2={shutter_time}')

    async def set_screen_format(self, screen_format):
        for key, val in self.screen_dict.items():
            if val == screen_format:
                await self.send_cmd(f'VSF:{key}')

    async def set_input_source(self, input_source):
        for key, val in self.input_dict.items():
            if val == input_source:
                await self.send_cmd(f'IIS:{key}')

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
    SCREEN_F__{self.screen_format}
    INPUR SRC-{self.input}
    GROUP-----{self.group}
    SHUTTER---{self.shutter}
    SHUTTER_IN---{self.shutter_in_time}
    SHUTTER_OUT---{self.shutter_out_time}
        '''
        )


async def create_projector(ip, port, login, password, label, id):
    projector = Projector(ip, port, login, password, label, id)
    try:
        await projector.get_info()
    except Exception as e:
        print(f'Error getting info for projector {ip}: {e}')
        return None
    return projector
