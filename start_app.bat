@echo off
echo Starte YouTube Downloader...
echo Bitte warten, bis der Server gestartet ist.
echo Das Fenster nicht schliessen, solange du die App nutzen willst.

:: Aktiviere die virtuelle Umgebung
call venv\Scripts\activate

:: Öffne den Browser automatisch nach kurzer Wartezeit
timeout /t 3 >nul
start http://127.0.0.1:5000

:: Starte die Python App
python app.py

pause
