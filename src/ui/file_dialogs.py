"""
Файловые диалоги. DearPyGui имеет встроенный file_dialog, но он рисуется
поверх viewport'а и не выглядит нативно. На macOS/Windows предпочтительнее
показать стандартный системный диалог через tkinter.filedialog.

tkinter здесь используется только как одноразовая ad-hoc Tk-сессия; мы не
запускаем mainloop, окно скрываем сразу. Это безопасно сосуществует с DPG.
"""
import asyncio
from typing import Optional


def _open_save_dialog() -> Optional[str]:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.asksaveasfilename(
            title="Save Scene",
            defaultextension=".json",
            filetypes=(("JSON Files", "*.json"), ("All Files", "*.*")),
        )
    finally:
        root.destroy()
    return path or None


def _open_load_dialog() -> Optional[str]:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.askopenfilename(
            title="Load Scene",
            filetypes=(
                ("JSON Files", "*.json"),
                ("Text Files (legacy)", "*.txt"),
                ("All Files", "*.*"),
            ),
        )
    finally:
        root.destroy()
    return path or None


async def save_scene_dialog() -> Optional[str]:
    """Системный Save диалог. Не блокирует render-loop надолго."""
    return await asyncio.to_thread(_open_save_dialog)


async def load_scene_dialog() -> Optional[str]:
    """Системный Open диалог."""
    return await asyncio.to_thread(_open_load_dialog)
