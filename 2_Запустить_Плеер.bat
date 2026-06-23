@echo off
chcp 65001 > nul
title Music App Client
echo [СИСТЕМА] Проверка и подготовка библиотек окружения...
echo.
py -m pip install customtkinter requests python-vlc keyring --quiet

echo [СИСТЕМА] Запуск музыкального плеера...
py client.py
if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Не удалось запустить плеер.
    pause
)
