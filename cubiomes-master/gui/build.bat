@echo off
REM libcubiomes.dll をビルドします (MinGW-w64のgccが必要です)
REM gui フォルダの中から実行してください: build.bat
cd /d "%~dp0\.."

gcc -O2 -fwrapv -shared -o gui\libcubiomes.dll ^
    generator.c layers.c biomenoise.c biomes.c noise.c ^
    quadbase.c util.c finders.c guiapi.c

echo ビルド完了: gui\libcubiomes.dll
