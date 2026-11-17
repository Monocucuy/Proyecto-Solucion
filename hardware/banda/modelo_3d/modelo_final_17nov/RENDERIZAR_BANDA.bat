@echo off
rem Renderiza el modelo 3D de la banda: 6 imagenes PNG 1920x1080 y un video MP4 de 10 s a 1080p y 60 fps.
rem Deja esta carpeta completa (banda_real.py, carpeta tex y este .bat) en el otro PC y haz doble clic.
rem Opciones: RENDERIZAR_BANDA.bat stills  (solo imagenes)   RENDERIZAR_BANDA.bat video  (solo video)
cd /d "%~dp0"
set "MODO=%~1"
if "%MODO%"=="" set "MODO=todo"
set "BL="
for /d %%D in ("%ProgramFiles%\Blender Foundation\Blender *") do if exist "%%D\blender.exe" set "BL=%%D\blender.exe"
if not defined BL if exist "%ProgramFiles(x86)%\Steam\steamapps\common\Blender\blender.exe" set "BL=%ProgramFiles(x86)%\Steam\steamapps\common\Blender\blender.exe"
if not defined BL (
  echo No encontre Blender. Instala Blender 4.2 LTS o mas nuevo desde blender.org,
  echo o abre este archivo con el Bloc de notas y escribe la ruta en la linea: set "BL=C:\ruta\blender.exe"
  pause
  exit /b 1
)
echo Usando: %BL%
echo Modo: %MODO%   (las imagenes tardan unos minutos; el video, 600 fotogramas, bastante mas)
"%BL%" -b -P "%~dp0banda_real.py" -- %MODO%
echo.
echo Listo. Revisa la carpeta "salida": render_01 ... render_06 (PNG) y banda_real_10s_1080p60_0001-0600.mp4
pause
