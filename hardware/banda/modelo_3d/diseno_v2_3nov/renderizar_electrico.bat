@echo off
rem Renderiza electrico.blend a video MP4 (1080p, ~76 s, Eevee). Dejalo en la misma carpeta que el .blend.
rem El .blend esta guardado con Blender 5.1: usa Blender 5.1 o mas nuevo.
cd /d "%~dp0"
set "BL="
for /d %%D in ("%ProgramFiles%\Blender Foundation\Blender *") do if exist "%%D\blender.exe" set "BL=%%D\blender.exe"
if not defined BL (
  echo No encontre Blender. Instala Blender 5.1 o mas nuevo desde blender.org,
  echo o escribe la ruta de blender.exe en la linea: set "BL=C:\ruta\blender.exe"
  pause
  exit /b 1
)
"%BL%" -b "%~dp0electrico.blend" -a
echo.
echo Listo. Busca electrico_0001-1830.mp4 en esta carpeta.
pause
