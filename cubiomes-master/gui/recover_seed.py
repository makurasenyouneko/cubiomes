#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""構造物の観測位置からシードを逆算するコマンドラインツール。"""

import argparse
import sys
import os

import cubiomes_api as api


def parse_seed(text):
    text = text.strip()
    if text == "":
        raise ValueError("シードを入力してください。")
    try:
        val = int(text)
        return val & 0xFFFFFFFFFFFFFFFF
    except ValueError:
        pass
    h = 0
    for ch in text:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return h & 0xFFFFFFFFFFFFFFFF


def parse_positions(lines):
    positions = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            parts = [p.strip() for p in line.split(",")]
        else:
            parts = line.split()
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(
                f"座標は 'X,Z' または 'X Z' の形式で指定してください: {line}")
        positions.append((int(parts[0]), int(parts[1])))
    if not positions:
        raise argparse.ArgumentTypeError("少なくとも1つの座標を入力してください。")
    return positions


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="構造物の観測位置からシードを逆算します。"
    )
    parser.add_argument("--version", dest="mc_version", default="1.21",
                        help="Minecraftバージョン (例: 1.21, 1.20, 1.19)")
    parser.add_argument("--structure", dest="structure", required=True,
                        help="構造物タイプ名 (例: '村 (Village)' または 'Village')")
    parser.add_argument("--start-seed", dest="start_seed", default="0",
                        help="探索開始シード (デフォルト: 0)")
    parser.add_argument("--end-seed", dest="end_seed", default="10000",
                        help="探索終了シード (デフォルト: 10000)")
    parser.add_argument("--tolerance", dest="tolerance", type=int, default=0,
                        help="許容誤差(ブロック) (デフォルト: 0)")
    parser.add_argument("--position", dest="positions", action="append",
                        help="観測位置を X,Z 形式で複数指定。例: --position 0,0 --position 32,0")
    parser.add_argument("--position-file", dest="position_file",
                        help="観測座標を行ごとに X,Z または X Z で並べたファイル")
    parser.add_argument("--list-structures", action="store_true",
                        help="対応する構造物タイプの一覧を表示する")
    args = parser.parse_args(argv)

    if args.list_structures:
        for name, _ in api.STRUCTURES:
            print(name)
        return 0

    if not args.positions and not args.position_file:
        parser.error("--position または --position-file を指定してください。")

    positions = []
    if args.positions:
        positions.extend(parse_positions(args.positions))
    if args.position_file:
        if not os.path.isfile(args.position_file):
            parser.error(f"position file not found: {args.position_file}")
        with open(args.position_file, encoding="utf-8") as f:
            positions.extend(parse_positions(f.readlines()))

    struct_type = None
    for name, value in api.STRUCTURES:
        if args.structure == name or args.structure.lower() == name.lower():
            struct_type = value
            break
    if struct_type is None:
        parser.error(f"不明な構造物タイプです: {args.structure}")

    mc = None
    for name, value in api.MC_VERSIONS:
        if args.mc_version == name or args.mc_version == str(name):
            mc = value
            break
        if args.mc_version.replace(".", "") == name.replace(".", ""):
            mc = value
            break
    if mc is None:
        try:
            mc = int(args.mc_version)
        except ValueError:
            parser.error(f"不明なMinecraftバージョンです: {args.mc_version}")

    start_seed = parse_seed(args.start_seed)
    end_seed = parse_seed(args.end_seed)
    if start_seed > end_seed:
        parser.error("開始シードは終了シード以下にしてください。")

    print("構造物タイプ:", args.structure)
    print("バージョン:", args.mc_version)
    print("探索シード範囲:", start_seed, "〜", end_seed)
    print("許容誤差:", args.tolerance)
    print("観測位置:")
    for x, z in positions:
        print("  ", x, z)

    try:
        found = api.find_seed_for_structure(
            struct_type, mc, positions,
            start_seed, end_seed, args.tolerance)
    except Exception as e:
        print("エラー: ", e, file=sys.stderr)
        return 1

    print(f"一致するシード: {found}")
    print(f"一致するシード (decimal): {found}")
    print(f"一致するシード (hex): 0x{found:016x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
