# Panasonic Projector for Isadora Pythoner

Управление проекторами Panasonic из Isadora (через встроенный Pythoner-актор):
power on/off, shutter open/close и **fade-in / fade-out time** — то, чего нет
в PJLink.

Тестировалось на Panasonic PT-RZ970, PT-RZ120. Команды протокола — в папке `doc/`.

Зависимости: только stdlib (`socket`, `hashlib`, `threading`).
Один файл — `panasonic_projector.py`.

## Подключение в Isadora

1. Положи `panasonic_projector.py` рядом с `.izz`-файлом (или в любом месте,
   доступном по абсолютному пути).
2. В патче поставь актор **Pythoner**, в его входе `ext file` укажи путь
   к `panasonic_projector.py`.
3. В коде актора импортируй классы:

```python
from panasonic_projector import Projector, ProjectorGroup
```

## API

### `Projector(ip, login, password, port=1024, timeout=2.0, label=None)`

```python
p = Projector("10.101.10.13", "admin1", "panasonic")

p.power_on()              # PON
p.power_off()             # POF
p.power_is_on()           # -> bool

p.shutter_open()          # OSH:0
p.shutter_close()         # OSH:1
p.shutter_is_open()       # -> bool

p.set_fade_in(1.5)        # VXX:SEFS1=1.5  (округление до FADE_TIME_OPTIONS)
p.set_fade_out(2.0)       # VXX:SEFS2=2.0
p.get_fade_in()           # -> 1.5
p.get_fade_out()          # -> 2.0

p.send_raw("QPW")         # любая Panasonic-команда
```

Допустимые значения fade-time (секунды):
`0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 7.0, 10.0`

При сетевых ошибках бросается `ProjectorError`.

### `ProjectorGroup([Projector, Projector, ...])`

Параллельные операции через ThreadPoolExecutor. Каждый метод возвращает
`dict {label: result_or_exception}` — упавший проектор не валит остальных.

```python
group = ProjectorGroup([p1, p2, p3])

group.shutter_close()         # все одновременно
group.set_fade_out(2.0)       # тоже параллельно
results = group.shutter_open()
# results == {"p1": None, "p2": None, "p3": ProjectorError(...)}
```

## Паттерны использования в Pythoner

### Вариант A: один актор на один проектор (визуально удобно)

Каждый Pythoner-актор владеет своим проектором. Общий триггер от Isadora
разлетается по всем акторам почти одновременно. Чтобы убрать sequential-
джиттер от обработки графа на главном потоке Isadora — стартуем команду
в фоновом потоке и сразу возвращаемся:

```python
import threading
from panasonic_projector import Projector

# module-level state живёт между вызовами актора
if "proj" not in globals():
    proj = Projector(ip, login, password)

if trigger:
    threading.Thread(target=proj.shutter_close, daemon=True).start()

return "fired"
```

Реальный джиттер до байта `OSH:1` на проводе — 10–30 мс (сеть + auth).
При fade-time 1–3 с это визуально незаметно.

### Вариант B: один актор управляет всеми (компактно)

Удобно, когда проекторов 5+ и не хочется городить много нод.
Inputs Pythoner-актора — `ip_list` (через запятую), `action`:

```python
from panasonic_projector import Projector, ProjectorGroup

if "group" not in globals():
    group = ProjectorGroup([
        Projector(ip.strip(), login, password)
        for ip in ip_list.split(",")
    ])

if action == "close":
    group.shutter_close()
elif action == "open":
    group.shutter_open()
elif action == "fade_out":
    group.set_fade_out(fade_seconds)

return "ok"
```

## Быстрый smoke-test без Isadora

```bash
python3 -c "
from panasonic_projector import Projector
p = Projector('10.101.10.13', 'admin1', 'panasonic')
print('power:', p.power_is_on())
print('fade_out:', p.get_fade_out())
"
```

## Документация Panasonic

См. `doc/` — там оригинальные таблицы команд PT-RZ-серии.
