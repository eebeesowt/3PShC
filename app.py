from tkinter import (Tk,
                     IntVar, Frame,
                     Toplevel, Button, Checkbutton,
                     Label, Entry, filedialog)
import asyncio
from tkinter import ttk  # Для выпадающих списков
# from typing import List   # create_projector
from lib.projector import Projector


# async def get_on_projectors():
#     projectors: List[Projector] = []
#     for projector in projector_list:
#         try:
#             proj = await create_projector(*projector, len(projectors))
#             if proj.power is not None:
#                 projectors.append(proj)
#         except Exception as e:
#             print(f'No connection to projector {projector[0]}: {e}')
#     return projectors


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
        self.label = Label(
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
        self.screen_status = Label(
            self.frame,
            text=self.get_screen_status(),
            background=self.bg_status_color,
            foreground="white"
        )

        # Выпадающие списки для времени шаттера

        if self.projector.shutter_in_time is not None:
            self.shutter_in_menu = ttk.Combobox(
                self.frame,
                values=self.projector.shutter_time_dict,
                state="readonly",
                width=5
            )
            self.shutter_in_menu.set(self.projector.shutter_in_time)
            self.shutter_in_menu.bind(
                "<<ComboboxSelected>>", self.set_shutter_in
            )
            self.shutter_in_menu.grid(row=2, column=0, pady=2)

        if self.projector.shutter_out_time is not None:
            self.shutter_out_menu = ttk.Combobox(
                self.frame,
                values=self.projector.shutter_time_dict,
                state="readonly",
                width=5
            )
            self.shutter_out_menu.set(self.projector.shutter_out_time)
            self.shutter_out_menu.bind(
                "<<ComboboxSelected>>", self.set_shutter_out
            )
            self.shutter_out_menu.grid(row=2, column=1, pady=2)

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

    def set_shutter_in(self, event):
        selected_time = self.shutter_in_menu.get()
        try:
            asyncio.run(self.projector.set_shutter_in(selected_time))
            print(f"Shutter In Time set to {selected_time}")
        except Exception as e:
            print(f"Error setting Shutter In Time: {e}")

    def set_shutter_out(self, event):
        selected_time = self.shutter_out_menu.get()
        try:
            asyncio.run(self.projector.set_shutter_out(selected_time))
            print(f"Shutter Out Time set to {selected_time}")
        except Exception as e:
            print(f"Error setting Shutter Out Time: {e}")

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
        self.root.geometry("466x400")  # Размер окна по умолчанию
        self.root.configure(background="#363537")

        # Верхняя панель с кнопками
        self.button_frame = Frame(self.root, background="#363537")
        self.button_frame.pack(side='top', fill='x', padx=5, pady=5)

        # Кнопки
        self.all_shutter_on_btn = Button(
            self.button_frame,
            text='Open Group',
            command=self.opn_async_grp_shtr,
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
            bg="#FFDBB5",
            fg="black",
            width=10,
            highlightthickness=0
        )
        self.add_projector_btn = Button(
            self.button_frame,
            text='Add Projector',
            command=self.open_add_projector_window,
            bg="#71A9F7",
            fg="white",
            width=12,
            highlightthickness=0
        )
        self.load_projectors_btn = Button(
            self.button_frame,
            text='Load from File',
            command=self.load_projectors_from_file,
            bg="#729B79",
            fg="white",
            width=15,
            highlightthickness=0
        )
        self.save_projectors_btn = Button(
            self.button_frame,
            text='Save to File',
            command=self.save_projectors_to_file,
            bg="#14453D",
            fg="white",
            width=15,
            highlightthickness=0
        )

        # Расположение кнопок
        self.all_shutter_on_btn.grid(
            row=1, column=0,
            ipadx=7, ipady=7,
            pady=10
        )
        self.all_shutter_off_btn.grid(
            row=1, column=1, ipadx=7, ipady=7, pady=10
        )
        self.update_btn.grid(row=1, column=2, padx=5, pady=10)

        self.add_projector_btn.grid(row=0, column=0, padx=5, pady=2)
        self.load_projectors_btn.grid(row=0, column=1, padx=5, pady=2)
        self.save_projectors_btn.grid(row=0, column=2, padx=5, pady=2)

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

    def load_projectors_from_file(self):
        """
        Загружает проекторы, их координаты и размер окна из файла.
        """
        file_path = filedialog.askopenfilename(
            title="Select Projectors File",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )

        if not file_path:
            print("No file selected.")
            return

        try:
            with open(file_path, "r") as file:
                lines = file.readlines()

                # Загружаем размер окна из первой строки
                if len(lines) > 0:
                    width, height = map(int, lines[0].strip().split(","))
                    self.root.geometry(f"{width}x{height}")

                # Загружаем проекторы из оставшихся строк
                for line in lines[1:]:
                    # Ожидаемый формат строки:
                    # IP,PORT,USERNAME,PASSWORD,LABEL,X,Y
                    parts = line.strip().split(",")
                    if len(parts) != 7:
                        print(f"Invalid line format: {line}")
                        continue

                    ip, port, username, password, label, x, y = parts
                    port = int(port)
                    x = int(x)
                    y = int(y)

                    # Создание нового проектора
                    try:
                        new_projector = Projector(
                            ip=ip,
                            port=port,
                            login=username,
                            password=password,
                            label=label,
                            id=len(self.active_frame) + 1,
                        )
                    except ValueError as e:
                        print("Error creating projector:")
                        print(f"  ip: {ip}")
                        print(f"  Error: {e}")
                        continue
                    # Создание фрейма для нового проектора
                    frame = ProjectorFrame(
                        new_projector, self.canvas, self.remove_frame
                    )

                    # Расположение фрейма на основе координат
                    self.active_frame.append(frame)
                    frame.frame.place(x=x, y=y)

            print("Window size loaded successfully.")
        except Exception as e:
            print(f"Error while loading projectors: {e}")

    def save_projectors_to_file(self):
        """
        Сохраняет активные проекторы, их координаты и размер окна в файл.
        """
        file_path = filedialog.asksaveasfilename(
            title="Save Projectors File",
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )

        if not file_path:
            print("No file selected for saving.")
            return

        try:
            with open(file_path, "w") as file:
                # Сохраняем размер окна
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                file.write(f"{width},{height}\n")

                # Сохраняем данные проекторов
                for frame in self.active_frame:
                    projector = frame.projector
                    x = frame.frame.winfo_x()
                    y = frame.frame.winfo_y()
                    # Сохраняем данные проектора и координаты в формате:
                    # IP,PORT,USERNAME,PASSWORD,LABEL,X,Y
                    file.write(
                        f"{projector.ip},{projector.port},{projector.login},"
                        f"{projector.password},{projector.label},{x},{y}\n"
                    )
            print(
                (
                    f"Projectors, positions, and window size"
                    f"saved successfully to {file_path}."
                )
            )
        except Exception as e:
            print(f"Error while saving projectors: {e}")

    def open_add_projector_window(self):
        # Создание нового окна
        add_window = Toplevel(self.root)
        add_window.title("Add Projector")
        add_window.geometry("300x250")

        # Поля для ввода параметров
        Label(
            add_window, text="IP Address:"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ip_entry = Entry(add_window)
        ip_entry.grid(row=0, column=1, padx=10, pady=5)

        Label(
            add_window, text="Port:"
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        port_entry = Entry(add_window)
        port_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(
            add_window, text="Username:"
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        username_entry = Entry(add_window)
        username_entry.grid(
            row=2, column=1, padx=10, pady=5
        )
        Label(
            add_window, text="Password:"
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        password_entry = Entry(add_window, show="*")
        password_entry.grid(
            row=3, column=1, padx=10, pady=5
        )

        Label(
            add_window, text="Label:"
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        label_entry = Entry(add_window)
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

        add_button = Button(add_window, text="Add", command=add_projector)
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


main = MainFrame()
main.start()
