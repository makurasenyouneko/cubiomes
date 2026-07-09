#!/bin/sh
# libcubiomes.so (Linux) / libcubiomes.dylib (macOS) をビルドします。
# GUIフォルダの中から実行してください: sh build.sh
set -e
cd "$(dirname "$0")/.."

OUT="gui/libcubiomes.so"
case "$(uname -s)" in
    Darwin) OUT="gui/libcubiomes.dylib" ;;
esac

gcc -O2 -fPIC -fwrapv -shared -o "$OUT" \
    generator.c layers.c biomenoise.c biomes.c noise.c \
    quadbase.c util.c finders.c guiapi.c -lpthread -lm

echo "ビルド完了: $OUT"
