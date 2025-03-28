from projector import create_projector, Projector
from typing import List
from tkinter import ttk
from tkinter import Tk, IntVar, StringVar
import asyncio

projector_list = [
    ('10.101.10.132', 1024, 'admin1', 'panasonic', 'LEFT'),
    ('10.101.10.131', 1024, 'admin1', 'panasonic', 'RIGHT'),
    ('10.101.10.123', 1024, 'admin1', 'panasonic', 'FRONT'),
    ('10.101.10.121', 1024, 'admin1', 'panasonic', 'BACK'),
]


async def get_on_projectors():
    projectors: List[Projector] = []
    for projector in projector_list:
        try:
            proj = await create_projector(*projector, len(projectors))
            # Проверка на успешное подключение
            if proj.power is not None:
                projectors.append(proj)
        except Exception as e:
            print(f'No connection to projector {projector[0]}: {e}')
    return projectors


class ProjectorFrame:
    def __init__(self, projector: Projector) -> None:
        self.projector = projector
        self.grp = IntVar()
        self.screen_format = StringVar(
            value=projector.screen_format)
        self.input_source = StringVar(
            value=projector.input)
        self.shutter_in_time = StringVar(
            value=str(projector.shutter_in_time))
        self.shutter_out_time = StringVar(
            value=str(projector.shutter_out_time))

        # Содержимое фрейма
        self.frame = ttk.Frame(borderwidth=1, relief='solid', padding=[8, 10])
        self.label = ttk.Label(self.frame, text=projector.label,
                               font=("Helvetica", 16, "bold"))
        self.shutter_on_btn = ttk.Button(self.frame, text='Screen On',
                                         command=self.shutter_open)
        self.shutter_off_btn = ttk.Button(self.frame, text='Screen Off',
                                          command=self.shutter_close)
        self.group = ttk.Checkbutton(self.frame, text="Group",
                                     variable=self.grp, command=self.grpd)

        self.screen_f_label = ttk.Label(self.frame, text="Screen Format:")
        self.screen_f_combo = ttk.Combobox(self.frame,
                                           textvariable=self.screen_format,
                                           values=list(
                                               projector.screen_dict.values()
                                               ))
        self.screen_f_combo.bind("<<ComboboxSelected>>",
                                 self.set_screen_format)

        self.input_s_label = ttk.Label(self.frame, text="Input Source:")
        self.input_s_combo = ttk.Combobox(self.frame,
                                          textvariable=self.input_source,
                                          values=list(
                                              projector.input_dict.values()
                                              ))
        self.input_s_combo.bind("<<ComboboxSelected>>",
                                self.set_input_source)

        self.bg_status_color = 'green' if self.projector.shutter else 'red'
        self.screen_status = ttk.Label(self.frame,
                                       text=self.get_screen_status(),
                                       background=self.bg_status_color)

        self.input_shtr_in_label = ttk.Label(self.frame,
                                             text="Shutter in:")
        self.in_shtr_in_combo = ttk.Combobox(self.frame,
                                             textvariable=self.shutter_in_time,
                                             values=projector.shutter_time_dict
                                             )
        self.in_shtr_in_combo.bind("<<ComboboxSelected>>",
                                   self.set_shutter_in)

        self.input_shtr_out_label = ttk.Label(self.frame,
                                              text="Shutter out:")
        self.in_shtr_ot_comb = ttk.Combobox(self.frame,
                                            textvariable=self.shutter_out_time,
                                            values=projector.shutter_time_dict
                                            )
        self.in_shtr_ot_comb.bind("<<ComboboxSelected>>",
                                  self.set_shutter_out)

        # Расположение
        self.label.grid(row=0, column=0, columnspan=2, pady=5)
        self.group.grid(row=0, column=2, pady=5)
        self.shutter_on_btn.grid(row=1, column=0, pady=5)
        self.shutter_off_btn.grid(row=1, column=1, pady=5)
        self.screen_status.grid(row=1, column=2, pady=5)
        self.input_shtr_in_label.grid(row=2, column=0, pady=5)
        self.in_shtr_in_combo.grid(row=2, column=1, pady=5)
        self.input_shtr_out_label.grid(row=3, column=0, pady=5)
        self.in_shtr_ot_comb.grid(row=3, column=1, pady=5)


    def get_screen_status(self):
        return f'Screen:  {"ON" if self.projector.shutter else "OFF"}'

    def shutter_open(self):
        try:
            asyncio.run(self.projector.shutter_open())
        except TimeoutError:
            self.screen_status['background'] = '#000000'
            self.screen_status['foreground'] = '#ffffff'
            self.screen_status['text'] = 'Connection Error'
        else:
            self.screen_status['text'] = self.get_screen_status()
            self.screen_status['background'] = 'green' if self.projector.shutter else 'red'

    def shutter_close(self):
        try:
            asyncio.run(self.projector.shutter_close())
        except TimeoutError:
            self.screen_status['background'] = '#000000'
            self.screen_status['foreground'] = '#ffffff'
            self.screen_status['text'] = 'Connection Error'
        else:
            self.screen_status['text'] = self.get_screen_status()
            self.screen_status['background'] = 'green' if self.projector.shutter else 'red'

    def grpd(self):
        self.projector.group = self.grp.get()

    def set_screen_format(self, event):
        asyncio.run(self.projector.set_screen_format(self.screen_format.get()))

    def set_input_source(self, event):
        asyncio.run(self.projector.set_input_source(self.input_source.get()))

    def set_shutter_in(self, event):
        asyncio.run(self.projector.shutter_in(self.shutter_in_time.get()))

    def set_shutter_out(self, event):
        asyncio.run(self.projector.shutter_out(self.shutter_out_time.get()))

    def update(self):
        try:
            asyncio.run(self.projector.get_info())
        except TimeoutError:
            self.screen_status['background'] = '#000000'
            self.screen_status['foreground'] = '#ffffff'
            self.screen_status['text'] = 'Connection Error'
        else:
            self.screen_status['text'] = self.get_screen_status()
            self.screen_status['background'] = 'green' if self.projector.shutter else 'red'


class MainFrame:
    def __init__(self) -> None:
        # Создание окна
        self.root = Tk()
        self.root.title("Projector Control")
        self.root.geometry("350x800")

        # Кнопки
        self.all_shutter_on_btn = ttk.Button(text='Group Open',
                                             command=self.opn_async_grp_shtr)
        self.all_shutter_off_btn = ttk.Button(text='Group Close',
                                              command=self.cls_async_grp_shtr)
        self.update_btn = ttk.Button(text='Update', command=self.update)

        # Расположение
        self.all_shutter_on_btn.pack(side='top', fill='x', padx=6, pady=4)
        self.all_shutter_off_btn.pack(side='top', fill='x', padx=6, pady=4)
        self.update_btn.pack(side='top', fill='x', padx=6, pady=4)

        # Вспомогательные переменные
        self.active_frame = []

    async def close_group_shutter(self):
        tasks = []
        for frame in self.active_frame:
            if frame.grp.get() == 1:
                task = asyncio.create_task(frame.projector.shutter_close())
                tasks.append(task)
        await asyncio.gather(*tasks)

    def cls_async_grp_shtr(self):
        asyncio.run(self.close_group_shutter())
        for frame in self.active_frame:
            frame.screen_status['background'] = 'green' if frame.projector.shutter else 'red'
            frame.screen_status['text'] = frame.get_screen_status()

    async def open_group_shutter(self):
        tasks = []
        for frame in self.active_frame:
            if frame.grp.get() == 1:
                task = asyncio.create_task(frame.projector.shutter_open())
                tasks.append(task)
        await asyncio.gather(*tasks)

    def opn_async_grp_shtr(self):
        asyncio.run(self.open_group_shutter())
        for frame in self.active_frame:
            frame.screen_status['background'] = 'green' if frame.projector.shutter else 'red'
            frame.screen_status['text'] = frame.get_screen_status()

    def update(self):
        for frame in self.active_frame:
            frame.update()

    def add_frames(self, projectors):
        for projector in projectors:
            frame = ProjectorFrame(projector)
            self.active_frame.append(frame)
            frame.frame.pack(side='top', fill='both', expand=True, padx=5,
                             pady=5)

    def start(self):
        self.root.mainloop()


projectors = asyncio.run(get_on_projectors())

main = MainFrame()
if len(projectors) > 0:
    main.add_frames(projectors)
main.start()
