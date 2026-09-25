@echo off
cd /d "%~dp0"
echo [%date% %time%] Iniciando >> output\run_log.txt
python main.py --niche todos >> output\run_log.txt 2>&1
echo [%date% %time%] Fin codigo %errorlevel% >> output\run_log.txt
