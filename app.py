from tkinter import ttk
from tkinter import Tk, IntVar, Frame, Toplevel, Button, Checkbutton
import asyncio
from typing import List
from projector import create_projector, Projector

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
            if proj.power is not None:
                projectors.append(proj)
        except Exception as e:
            print(f'No connection to projector {projector[0]}: {e}')
    return projectors


class ProjectorFrame:
    def __init__(self, projector: Projector, parent, remove_callback) -> None:
        self.projector = projector
        self.grp = IntVar()
        self.remove_callback = remove_callback

        # Содержимое фрейма
        self.frame = Frame(
            parent,
            borderwidth=1,
            relief='solid',
            background="#363537"
        )
        self.label = ttk.Label(
            self.frame,
            text=projector.label,
            font=("Helvetica", 12, "bold"),
            foreground="white",
            background="#363537"
        )
        self.shutter_on_btn = Button(
            self.frame,
            text='On',
            command=self.shutter_open,
            bg="#04A777",
            fg="white", width=5, highlightthickness=0
        )
        self.shutter_off_btn = Button(
            self.frame, text='Off', command=self.shutter_close,
            bg="#DC758F", fg="white", width=5, highlightthickness=0
        )
        self.group = Checkbutton(
            self.frame,
            text="Grp",
            variable=self.grp,
            background="#363537",
            highlightthickness=0
        )
        self.close_btn = Button(
            self.frame, text='x', command=self.close_frame, bg="#F24333",
            fg="white", width=1, height=1, highlightthickness=0
        )
        self.bg_status_color = 'green' if self.projector.shutter else 'red'
        self.screen_status = ttk.Label(
            self.frame,
            text=self.get_screen_status(),
            background=self.bg_status_color,
            foreground="white"
        )

        # Расположение
        self.label.grid(row=0, column=0, columnspan=2, pady=2)
        self.group.grid(row=0, column=2, pady=2)
        self.close_btn.grid(row=0, column=3, pady=2, padx=2)
        self.shutter_on_btn.grid(row=1, column=0, pady=2)
        self.shutter_off_btn.grid(row=1, column=1, pady=2)
        self.screen_status.grid(row=1, column=2, pady=2)

        # Перетаскивание
        self.frame.bind("<Button-1>", self.start_drag)
        self.frame.bind("<B1-Motion>", self.do_drag)

        self._drag_data = {"x": 0, "y": 0}

    def get_screen_status(self):
        return f'{"ON" if self.projector.shutter else "OFF"}'

    def shutter_open(self):
        try:
            asyncio.run(self.projector.shutter_open())
        except TimeoutError:
            print(
                "Error: Timeout while opening shutter"
            )
            self.screen_status['background'] = '#000000'
            self.screen_status['foreground'] = '#ffffff'
            self.screen_status['text'] = 'Error'
        else:
            self.screen_status['text'] = self.get_screen_status()
            self.screen_status['background'] = (
                'green' if self.projector.shutter else 'red'
            )

    def shutter_close(self):
        try:
            asyncio.run(self.projector.shutter_close())
        except TimeoutError:
            print("Error: Timeout while closing shutter")
            self.screen_status['background'] = '#000000'
            self.screen_status['foreground'] = '#ffffff'
            self.screen_status['text'] = 'Error'
        else:
            self.screen_status['text'] = self.get_screen_status()
            self.screen_status['background'] = (
                'green' if self.projector.shutter else 'red'
            )

    def close_frame(self):
        self.frame.destroy()
        self.remove_callback(self)

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        x = self.frame.winfo_x() - self._drag_data["x"] + event.x
        y = self.frame.winfo_y() - self._drag_data["y"] + event.y
        self.frame.place(x=x, y=y)


class MainFrame:
    def __init__(self) -> None:
        # Создание окна
        self.root = Tk()
        self.root.title("3P Shutter Control")
        self.root.geometry("600x400")
        self.root.configure(background="#363537")

        # Верхняя панель с кнопками
        self.button_frame = Frame(self.root, background="#363537")
        self.button_frame.pack(side='top', fill='x', padx=5, pady=5)

        # Кнопки
        self.all_shutter_on_btn = Button(
            self.button_frame,
            text='Open Group',
            command=self.opn_async_grp_shtr,  # noqa: E501
            bg="#04A777",
            fg="white",
            highlightthickness=0
        )
        self.all_shutter_off_btn = Button(
            self.button_frame,
            text='Close Group',
            command=self.cls_async_grp_shtr,
            bg="#DC758F",
            fg="white",
            highlightthickness=0
        )
        self.update_btn = Button(
            self.button_frame,
            text='Update',
            command=self.update,
            bg="#83B5D1",
            fg="white",
            width=10,
            highlightthickness=0
        )
        self.add_projector_btn = Button(
            self.button_frame,
            text='Add Projector',
            command=self.open_add_projector_window,
            bg="#D9CAB3",
            fg="white",
            width=12,
            highlightthickness=0
        )

        # Расположение кнопок
        self.all_shutter_on_btn.grid(row=0, column=0, ipadx=7, ipady=7)
        self.all_shutter_off_btn.grid(row=0, column=1, ipadx=7, ipady=7)
        self.update_btn.grid(row=0, column=2, padx=5, pady=2)
        self.add_projector_btn.grid(row=0, column=3, padx=5, pady=2)

        # Область для перемещения фреймов проекторов
        self.canvas = Frame(
            self.root,
            borderwidth=2,
            relief='sunken',
            background="#938BA1"
        )
        self.canvas.pack(side='top', fill='both', expand=True, padx=5, pady=5)

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
            frame.screen_status['background'] = (
                'green' if frame.projector.shutter else 'red'
            )
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
            frame.screen_status['background'] = (
                'green' if frame.projector.shutter else 'red'
            )
            frame.screen_status['text'] = frame.get_screen_status()

    def update(self):
        print("Update clicked")

    def open_add_projector_window(self):
        # Создание нового окна
        add_window = Toplevel(self.root)
        add_window.title("Add Projector")
        add_window.geometry("300x250")

        # Поля для ввода параметров
        ttk.Label(
            add_window, text="IP Address:"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ip_entry = ttk.Entry(add_window)
        ip_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(
            add_window, text="Port:"
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        port_entry = ttk.Entry(add_window)
        port_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(
            add_window, text="Username:"
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        username_entry = ttk.Entry(add_window)
        username_entry.grid(
            row=2, column=1, padx=10, pady=5
        )
        ttk.Label(
            add_window, text="Password:"
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        password_entry = ttk.Entry(add_window, show="*")
        password_entry.grid(
            row=3, column=1, padx=10, pady=5
        )

        ttk.Label(
            add_window, text="Label:"
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        label_entry = ttk.Entry(add_window)
        label_entry.grid(row=4, column=1, padx=10, pady=5)

        # Кнопка для добавления проектора
        def add_projector():
            ip = ip_entry.get()
            port = int(port_entry.get())
            username = username_entry.get()
            password = password_entry.get()
            label = label_entry.get()

            # Создание нового проектора
            new_projector = Projector(
                ip=ip,
                port=port,
                login=username,
                password=password,
                label=label,
                id=len(self.active_frame) + 1,
            )
            frame = ProjectorFrame(
                new_projector, self.canvas, self.remove_frame
            )

            # Расположение нового фрейма
            x_offset = 10 + (len(self.active_frame) % 2) * 250
            y_offset = 10 + (len(self.active_frame) // 2) * 100

            self.active_frame.append(frame)
            frame.frame.place(x=x_offset, y=y_offset)

            # Закрытие окна после добавления
            add_window.destroy()

        add_button = ttk.Button(add_window, text="Add", command=add_projector)
        add_button.grid(row=5, column=0, columnspan=2, pady=10)

    def add_frames(self, projectors):
        x_offset = 10  # Начальный отступ по X
        y_offset = 10  # Начальный отступ по Y
        step_x = 250   # Шаг между фреймами по X
        step_y = 100   # Шаг между фреймами по Y
        max_columns = 2  # Максимальное количество фреймов в строке
        for index, projector in enumerate(projectors):
            x = x_offset + (index % max_columns) * step_x
            y = y_offset + (index // max_columns) * step_y

            frame = ProjectorFrame(projector, self.canvas, self.remove_frame)
            self.active_frame.append(frame)
            frame.frame.place(x=x, y=y)

    def remove_frame(self, frame):
        if frame in self.active_frame:
            self.active_frame.remove(frame)

    def start(self):
        self.root.mainloop()


projectors = asyncio.run(get_on_projectors())

main = MainFrame()
if len(projectors) > 0:
    main.add_frames(projectors)
main.start()
