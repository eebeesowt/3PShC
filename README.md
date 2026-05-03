# Simple Panasonic Projector Shutter Controll via LAN Control Commands

Тестировалось на проекторах panasonic pt-rz970, pt-rz120

в папке doc, документация команд


Для запуска необходим [python](https://www.python.org/) и [виртуальное окружение](https://skillbox.ru/media/code/python-venv-chto-takoe-virtualnoe-okruzhenie-i-kak-im-polzovatsya/)


Установка зависимостей
```
pip install -r req.txt

```
после чего можно запустить приложение
```
python src/app.py
```


## Форматы файлов конфигурации

### JSON формат (рекомендуется)
Сохраняет данные проекторов с их настройками в JSON формате:
```json
{
  "window_size": {
    "width": 1200,
    "height": 800
  },
  "projectors": [
    {
      "ip": "10.101.10.126",
      "port": 1024,
      "username": "admin1",
      "password": "panasonic",
      "label": "Projector 1",
      "position": {
        "x": 50,
        "y": 50
      },
      "settings": {
        "lens_settings": {
          "h_position": "+00200",
          "v_position": "+00100"
        },
        "display_settings": {
          "aspect_ratio": "16:10",
          "installation_mode": "Front/Desk"
        }
      }
    }
  ]
}
```

При загрузке JSON файла настройки проектора (lens position, aspect ratio, installation mode) автоматически применяются!

### TXT формат (legacy)
```
width,height
IP,PORT,USERNAME,PASSWORD,LABEL,X,Y
IP,PORT,USERNAME,PASSWORD,LABEL,X,Y
...
```

Добавлена возможность управления программой из Resolume Arena

OSC

Настроено все под localhost port 7001 

роуты: 

```
    "/shutter/open*",
    "/shutter/close*",
    "/shutter/group/open",
    "/shutter/group/close",
```

пример сообщения:
```
    /shutter/open/13
```
открыть шаттер на проекторе с 13 на конце ip addr 
(например 10.101.10.13, конечно такой проектор должен быть добавлен в программе на поле)
