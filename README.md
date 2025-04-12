# Simple Panasonic Projector Shutter Controll via LAN Control Commands

Тестировалось на проекторах panasonic pt-rz970, pt-rz120

в папке doc, документация команд


Сохраняет данные проекторов и координаты в формате:
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
