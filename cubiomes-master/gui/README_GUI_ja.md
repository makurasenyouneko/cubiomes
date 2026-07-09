# Cubiomes GUI（追加した簡易GUI）

このフォルダは、本来GUIを持たない `cubiomes`（Minecraftのバイオーム生成を
再現するCライブラリ）に対して追加した、**Python（Tkinter）製の簡易GUI**です。

Tkinterは多くの環境でPython標準ライブラリに含まれているため、追加インストール
なしで動かしやすいことを優先して選びました。

## できること

- **バイオーム判定**: バージョン・シード・座標を指定して、その地点のバイオームを表示
- **マップ表示**: 指定した中心座標を中心にバイオームマップ画像を生成して表示・保存
- **ストラクチャー探索**: 村・要塞・海底神殿など、原点付近のリージョンにおける
  理論上の生成位置を一覧表示

すべて日本語UIです。

## 必要なもの

- Python 3.8以降（標準の `tkinter` を含むもの。多くのLinuxディストリでは
  `python3-tk` パッケージが必要な場合があります）
- Cコンパイラ（`gcc` など）— 共有ライブラリのビルド用

## セットアップ手順

### 1. 共有ライブラリをビルドする

**Linux / macOS**
```sh
cd gui
sh build.sh
```

**Windows（MinGW-w64のgccが必要）**
```bat
cd gui
build.bat
```

うまくいくと `gui/libcubiomes.so`（Linux）、`gui/libcubiomes.dylib`（macOS）、
`gui/libcubiomes.dll`（Windows）が生成されます。

手動でビルドする場合は以下と同等です：

```sh
gcc -O2 -fPIC -fwrapv -shared -o libcubiomes.so \
    generator.c layers.c biomenoise.c biomes.c noise.c \
    quadbase.c util.c finders.c guiapi.c -lpthread -lm
```

`guiapi.c` は、このGUIのために追加した薄いラッパー（cubiomesの構造体を
Python側から直接扱わずに済むよう、単純な関数として再公開したもの）です。
cubiomes本体のロジックは一切変更していません。

### 2. GUIを起動する

```sh
cd gui
python3 cubiomes_gui.py
```

`tkinter` が入っていないと言われた場合:
- Ubuntu/Debian: `sudo apt install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- macOS (Homebrew Python): `brew install python-tk`
- Windows公式インストーラ: 通常は標準で同梱されています

## ファイル構成

| ファイル | 内容 |
|---|---|
| `guiapi.c`（親フォルダ）| cubiomesを簡単な関数として呼び出せるようにするCラッパー |
| `cubiomes_api.py` | `guiapi.c` をビルドした共有ライブラリをPythonの`ctypes`から呼び出すラッパー |
| `cubiomes_gui.py` | Tkinter製のGUI本体（日本語UI） |
| `build.sh` / `build.bat` | 共有ライブラリのビルドスクリプト |

## 注意事項

- ストラクチャー探索は公式READMEのサンプルと同じ考え方の簡易的な近似計算です。
  1.18以降の一部の構造物（砂漠ピラミッドなど）は地形都合で実際には生成されない
  ことがありますが、この簡易探索ではそこまで判定していません。
- マップ画像はPPM形式で生成されます。TkinterはPPMをそのまま表示できるため
  追加ライブラリ（Pillow等）は不要ですが、他の形式に変換したい場合は
  Pillowなどで開き直して再保存してください。
