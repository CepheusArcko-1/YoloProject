@echo off
cd /d "%~dp0"
echo === Installation de YOLO26 Object Detection ===

if not exist .venv\Scripts\python.exe (
    echo Creation de l'environnement Python...
    py -3 -m venv .venv 2>nul || python -m venv .venv || (echo Python est introuvable. Installez-le depuis https://www.python.org & pause & exit /b 1)
)

echo Installation des dependances (quelques minutes la premiere fois)...
.venv\Scripts\python -m pip install -q --disable-pip-version-check -r requirements.txt || (echo Echec de l'installation. & pause & exit /b 1)

echo Creation des raccourcis...
powershell -NoProfile -Command ^
  "$s = New-Object -ComObject WScript.Shell;" ^
  "foreach ($dir in @('%~dp0', [Environment]::GetFolderPath('Desktop'))) {" ^
  "  $l = $s.CreateShortcut((Join-Path $dir 'YOLO Detection.lnk'));" ^
  "  $l.TargetPath = '%~dp0.venv\Scripts\pythonw.exe';" ^
  "  $l.Arguments = '\"%~dp0application.pyw\"';" ^
  "  $l.WorkingDirectory = '%~dp0';" ^
  "  $l.Save() }"

echo.
echo Installation terminee. Double-cliquez sur "YOLO Detection" (sur le Bureau ou dans ce dossier).
pause
