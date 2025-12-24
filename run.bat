@echo off
for /f "usebackq delims=" %%a in (`type .env.local`) do set %%a
python -u main.py