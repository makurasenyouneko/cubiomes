# -*- coding: utf-8 -*-
"""
cubiomes_api.py
----------------
cubiomesライブラリ(libcubiomes.so / .dll / .dylib)をPythonから
ctypes経由で呼び出すための薄いラッパーモジュール。

事前に共有ライブラリをビルドしておく必要があります:

    Linux/macOS:
        gcc -O2 -fPIC -fwrapv -shared -o libcubiomes.so \\
            generator.c layers.c biomenoise.c biomes.c noise.c \\
            quadbase.c util.c finders.c guiapi.c -lpthread -lm

    Windows (MinGW):
        gcc -O2 -fwrapv -shared -o libcubiomes.dll ^
            generator.c layers.c biomenoise.c biomes.c noise.c ^
            quadbase.c util.c finders.c guiapi.c

詳しくは README_GUI_ja.md を参照してください。
"""

import ctypes
import os
import platform
import sys

# ---------------------------------------------------------------------------
# ライブラリの読み込み
# ---------------------------------------------------------------------------

def _default_lib_name():
    system = platform.system()
    if system == "Windows":
        return "libcubiomes.dll"
    if system == "Darwin":
        return "libcubiomes.dylib"
    return "libcubiomes.so"


def _find_library():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, _default_lib_name()),
        os.path.join(here, "..", _default_lib_name()),
        os.path.join(os.getcwd(), _default_lib_name()),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(
        "libcubiomes(.so/.dll/.dylib) が見つかりません。\n"
        "先にビルドしてから gui フォルダ、またはリポジトリ直下に配置してください。\n"
        "(README_GUI_ja.md のビルド手順を参照)"
    )


_lib = ctypes.CDLL(_find_library())

# --- 関数シグネチャの定義 --------------------------------------------------

_lib.gc_biome_at.argtypes = [
    ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint64,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
]
_lib.gc_biome_at.restype = ctypes.c_int

_lib.gc_biome_name.argtypes = [ctypes.c_int, ctypes.c_int]
_lib.gc_biome_name.restype = ctypes.c_char_p

_lib.gc_mc_name.argtypes = [ctypes.c_int]
_lib.gc_mc_name.restype = ctypes.c_char_p

_lib.gc_generate_map_ppm.argtypes = [
    ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint64,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_char_p,
]
_lib.gc_generate_map_ppm.restype = ctypes.c_int

_lib.gc_find_structures_near_origin.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_int,
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int,
]
_lib.gc_find_structures_near_origin.restype = ctypes.c_int

_lib.gc_find_seed_for_structure.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.c_uint64, ctypes.c_uint64,
    ctypes.c_int, ctypes.POINTER(ctypes.c_uint64),
]
_lib.gc_find_seed_for_structure.restype = ctypes.c_int

_lib.gc_struct_name.argtypes = [ctypes.c_int]
_lib.gc_struct_name.restype = ctypes.c_char_p


# ---------------------------------------------------------------------------
# バージョン / 構造物 定義 (biomes.h / finders.h と対応)
# ---------------------------------------------------------------------------

MC_VERSIONS = [
    ("1.21 (最新)", 28),   # MC_1_21_WD / MC_NEWEST
    ("1.20", 25),          # MC_1_20_6
    ("1.19", 24),          # MC_1_19_4
    ("1.18", 22),          # MC_1_18_2
    ("1.17", 21),          # MC_1_17_1
    ("1.16", 20),          # MC_1_16_5
    ("1.15", 18),          # MC_1_15_2
    ("1.14", 17),          # MC_1_14_4
    ("1.13", 16),          # MC_1_13_2
    ("1.12", 15),          # MC_1_12_2
    ("1.9",  12),          # MC_1_9_4
    ("1.8",  11),          # MC_1_8_9
    ("1.7",  10),          # MC_1_7_10
]

DIMENSIONS = [
    ("オーバーワールド", 0),
    ("ネザー", -1),
    ("ジ・エンド", 1),
]

STRUCTURES = [
    ("村 (Village)", 5),
    ("海底神殿 (Monument)", 8),
    ("森の洋館 (Mansion)", 9),
    ("前哨基地 (Outpost)", 10),
    ("砂漠の寺院 (Desert Pyramid)", 1),
    ("ジャングルの寺院 (Jungle Temple)", 2),
    ("魔女の小屋 (Swamp Hut)", 3),
    ("イグルー (Igloo)", 4),
    ("難破船 (Shipwreck)", 7),
    ("ネザー要塞 (Fortress)", 18),
    ("エンドシティ (End City)", 20),
]

LARGE_BIOMES = 0x1


def biome_at(mc, seed, dim, x, z, y=63, scale=1, large_biomes=False):
    flags = LARGE_BIOMES if large_biomes else 0
    bid = _lib.gc_biome_at(mc, flags, dim, ctypes.c_uint64(seed), scale, x, y, z)
    name = _lib.gc_biome_name(mc, bid).decode("utf-8", "replace")
    return bid, name


def mc_name(mc):
    return _lib.gc_mc_name(mc).decode("utf-8", "replace")


def generate_map(mc, seed, dim, cx, cz, width, height, pix_per_cell, out_path,
                  large_biomes=False):
    flags = LARGE_BIOMES if large_biomes else 0
    ret = _lib.gc_generate_map_ppm(
        mc, flags, dim, ctypes.c_uint64(seed),
        cx, cz, width, height, pix_per_cell,
        out_path.encode("utf-8"),
    )
    return ret == 0


def find_structures(struct_type, mc, seed, region_radius, max_results=64):
    xs = (ctypes.c_int * max_results)()
    zs = (ctypes.c_int * max_results)()
    n = _lib.gc_find_structures_near_origin(
        struct_type, mc, ctypes.c_uint64(seed), region_radius, xs, zs, max_results
    )
    return [(xs[i], zs[i]) for i in range(n)]


def find_seed_for_structure(struct_type, mc, positions,
                            start_seed, end_seed, tolerance=0):
    if not positions:
        raise ValueError("positions must contain at least one (x, z) coordinate")
    pos_count = len(positions)
    xs = (ctypes.c_int * pos_count)()
    zs = (ctypes.c_int * pos_count)()
    for i, pos in enumerate(positions):
        xs[i] = int(pos[0])
        zs[i] = int(pos[1])
    seed_out = ctypes.c_uint64(0)
    ret = _lib.gc_find_seed_for_structure(
        struct_type, mc, pos_count, xs, zs,
        ctypes.c_uint64(start_seed), ctypes.c_uint64(end_seed),
        tolerance, ctypes.byref(seed_out)
    )
    if ret != 0:
        raise ValueError("seed not found in the given range and tolerance")
    return seed_out.value


def struct_name(struct_type):
    return _lib.gc_struct_name(struct_type).decode("utf-8", "replace")


if __name__ == "__main__":
    # 簡易セルフテスト (self test)
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print("MC name:", mc_name(41))
    bid, name = biome_at(41, seed, 0, 0, 0)
    print(f"Seed {seed} biome at (0,63,0): id={bid} name={name}")
