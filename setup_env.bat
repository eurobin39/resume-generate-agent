@echo off
setlocal
python3 -m venv .venv
call .venv\Scripts\activate
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
endlocal
