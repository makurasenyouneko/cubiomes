# -*- coding: utf-8 -*-
"""
cubiomes_gui.py
----------------
cubiomes ライブラリのための簡易GUI（日本語UI）。

このリポジトリ本来の cubiomes は C言語のライブラリのみでGUIを
持っていなかったため、Python (Tkinter, 標準ライブラリのみ) で
シード探索・バイオーム確認ができる簡単なGUIを追加したものです。

起動方法:
    python3 cubiomes_gui.py

事前に libcubiomes.so (または .dll / .dylib) を同じフォルダに
配置しておく必要があります。ビルド方法は README_GUI_ja.md を
参照してください。
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import cubiomes_api as api


APP_TITLE = "Cubiomes GUI (日本語版)"


def parse_seed(text):
    """テキストをMinecraftのシード値(符号なし64bit整数)に変換する。
    数値でなければ、文字列のJavaのhashCode相当の値に変換する。"""
    text = text.strip()
    if text == "":
        raise ValueError("シードを入力してください。")
    try:
        val = int(text)
        return val & 0xFFFFFFFFFFFFFFFF
    except ValueError:
        pass
    # 文字列シード -> Javaのhashcode相当 (Minecraftの挙動に合わせる)
    h = 0
    for ch in text:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return h & 0xFFFFFFFFFFFFFFFF


class CubiomesGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("880x640")
        self.minsize(760, 560)

        self._build_common_frame()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.biome_tab = self._build_biome_tab(notebook)
        self.map_tab = self._build_map_tab(notebook)
        self.struct_tab = self._build_struct_tab(notebook)

        notebook.add(self.biome_tab, text="バイオーム判定")
        notebook.add(self.map_tab, text="マップ表示")
        notebook.add(self.struct_tab, text="ストラクチャー探索")

        self.status_var = tk.StringVar(value="準備完了")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w",
                            relief="sunken")
        status.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # 共通設定 (バージョン・ディメンション・シード)
    # ------------------------------------------------------------------
    def _build_common_frame(self):
        frame = ttk.LabelFrame(self, text="共通設定")
        frame.pack(fill="x", padx=8, pady=(8, 0))

        ttk.Label(frame, text="Minecraftバージョン:").grid(
            row=0, column=0, sticky="w", padx=4, pady=4)
        self.mc_var = tk.StringVar(value=api.MC_VERSIONS[0][0])
        mc_combo = ttk.Combobox(
            frame, textvariable=self.mc_var, state="readonly", width=14,
            values=[v[0] for v in api.MC_VERSIONS])
        mc_combo.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(frame, text="ディメンション:").grid(
            row=0, column=2, sticky="w", padx=4, pady=4)
        self.dim_var = tk.StringVar(value=api.DIMENSIONS[0][0])
        dim_combo = ttk.Combobox(
            frame, textvariable=self.dim_var, state="readonly", width=14,
            values=[d[0] for d in api.DIMENSIONS])
        dim_combo.grid(row=0, column=3, sticky="w", padx=4, pady=4)

        ttk.Label(frame, text="シード値:").grid(
            row=0, column=4, sticky="w", padx=4, pady=4)
        self.seed_var = tk.StringVar(value="0")
        seed_entry = ttk.Entry(frame, textvariable=self.seed_var, width=20)
        seed_entry.grid(row=0, column=5, sticky="w", padx=4, pady=4)

        self.large_biomes_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="広大なバイオーム (Large Biomes)",
                         variable=self.large_biomes_var).grid(
            row=0, column=6, sticky="w", padx=8, pady=4)

    def _current_mc(self):
        name = self.mc_var.get()
        for n, v in api.MC_VERSIONS:
            if n == name:
                return v
        return api.MC_VERSIONS[0][1]

    def _current_dim(self):
        name = self.dim_var.get()
        for n, v in api.DIMENSIONS:
            if n == name:
                return v
        return 0

    def _current_seed(self):
        return parse_seed(self.seed_var.get())

    def _set_status(self, text):
        self.status_var.set(text)
        self.update_idletasks()

    # ------------------------------------------------------------------
    # タブ1: バイオーム判定
    # ------------------------------------------------------------------
    def _build_biome_tab(self, parent):
        tab = ttk.Frame(parent)

        form = ttk.Frame(tab)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="X座標:").grid(row=0, column=0, sticky="w")
        self.biome_x_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.biome_x_var, width=10).grid(
            row=0, column=1, padx=4)

        ttk.Label(form, text="Y座標:").grid(row=0, column=2, sticky="w")
        self.biome_y_var = tk.StringVar(value="63")
        ttk.Entry(form, textvariable=self.biome_y_var, width=10).grid(
            row=0, column=3, padx=4)

        ttk.Label(form, text="Z座標:").grid(row=0, column=4, sticky="w")
        self.biome_z_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.biome_z_var, width=10).grid(
            row=0, column=5, padx=4)

        ttk.Button(form, text="バイオームを調べる",
                   command=self._on_check_biome).grid(
            row=0, column=6, padx=10)

        self.biome_result_var = tk.StringVar(value="")
        result_label = ttk.Label(tab, textvariable=self.biome_result_var,
                                  font=("TkDefaultFont", 14, "bold"))
        result_label.pack(padx=10, pady=20, anchor="w")

        help_text = (
            "指定したワールド座標のバイオームを判定します。\n"
            "Y座標は主に1.18以降で結果に影響します（それ以前のバージョンでは\n"
            "地表付近の値を使うのがおすすめです）。"
        )
        ttk.Label(tab, text=help_text, foreground="#555").pack(
            padx=10, pady=(0, 10), anchor="w")

        return tab

    def _on_check_biome(self):
        try:
            mc = self._current_mc()
            dim = self._current_dim()
            seed = self._current_seed()
            x = int(self.biome_x_var.get())
            y = int(self.biome_y_var.get())
            z = int(self.biome_z_var.get())
        except ValueError as e:
            messagebox.showerror("入力エラー", f"入力値を確認してください。\n{e}")
            return

        try:
            bid, name = api.biome_at(
                mc, seed, dim, x, z, y=y,
                large_biomes=self.large_biomes_var.get())
        except Exception as e:
            messagebox.showerror("エラー", str(e))
            return

        self.biome_result_var.set(
            f"座標 ({x}, {y}, {z}) のバイオーム: {name}  (ID={bid})"
        )
        self._set_status("バイオーム判定が完了しました。")

    # ------------------------------------------------------------------
    # タブ2: マップ表示
    # ------------------------------------------------------------------
    def _build_map_tab(self, parent):
        tab = ttk.Frame(parent)

        form = ttk.Frame(tab)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="中心X:").grid(row=0, column=0, sticky="w")
        self.map_cx_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.map_cx_var, width=8).grid(
            row=0, column=1, padx=4)

        ttk.Label(form, text="中心Z:").grid(row=0, column=2, sticky="w")
        self.map_cz_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.map_cz_var, width=8).grid(
            row=0, column=3, padx=4)

        ttk.Label(form, text="範囲(バイオーム格子):").grid(
            row=0, column=4, sticky="w")
        self.map_size_var = tk.StringVar(value="128")
        ttk.Entry(form, textvariable=self.map_size_var, width=8).grid(
            row=0, column=5, padx=4)

        ttk.Label(form, text="拡大率(px/マス):").grid(
            row=0, column=6, sticky="w")
        self.map_pix_var = tk.StringVar(value="3")
        ttk.Entry(form, textvariable=self.map_pix_var, width=5).grid(
            row=0, column=7, padx=4)

        ttk.Button(form, text="マップ生成",
                   command=self._on_generate_map).grid(
            row=0, column=8, padx=10)
        ttk.Button(form, text="画像として保存...",
                   command=self._on_save_map).grid(
            row=0, column=9, padx=4)

        canvas_frame = ttk.Frame(tab, relief="sunken", borderwidth=1)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.map_canvas = tk.Canvas(canvas_frame, background="#222222")
        self.map_canvas.pack(fill="both", expand=True)

        self._map_photo = None  # PhotoImage参照保持用
        self._map_ppm_path = None

        return tab

    def _on_generate_map(self):
        try:
            mc = self._current_mc()
            dim = self._current_dim()
            seed = self._current_seed()
            cx = int(self.map_cx_var.get())
            cz = int(self.map_cz_var.get())
            size = int(self.map_size_var.get())
            pix = int(self.map_pix_var.get())
        except ValueError as e:
            messagebox.showerror("入力エラー", f"入力値を確認してください。\n{e}")
            return

        if size <= 0 or size > 1024:
            messagebox.showerror("入力エラー", "範囲は 1〜1024 の間で指定してください。")
            return
        if pix <= 0 or pix > 16:
            messagebox.showerror("入力エラー", "拡大率は 1〜16 の間で指定してください。")
            return

        self._set_status("マップを生成しています...")

        def worker():
            out_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "_map_preview.ppm")
            try:
                ok = api.generate_map(
                    mc, seed, dim, cx, cz, size, size, pix, out_path,
                    large_biomes=self.large_biomes_var.get())
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("エラー", str(e)))
                self.after(0, lambda: self._set_status("マップ生成に失敗しました。"))
                return

            def apply_result():
                if not ok:
                    messagebox.showerror("エラー", "マップの生成に失敗しました。")
                    self._set_status("マップ生成に失敗しました。")
                    return
                self._map_ppm_path = out_path
                photo = tk.PhotoImage(file=out_path)
                self._map_photo = photo  # 参照を保持（GC対策）
                self.map_canvas.delete("all")
                self.map_canvas.config(
                    scrollregion=(0, 0, photo.width(), photo.height()))
                self.map_canvas.create_image(0, 0, anchor="nw", image=photo)
                self._set_status(
                    f"マップ生成が完了しました。({photo.width()}x{photo.height()}px)")

            self.after(0, apply_result)

        threading.Thread(target=worker, daemon=True).start()

    def _on_save_map(self):
        if not self._map_ppm_path or not os.path.isfile(self._map_ppm_path):
            messagebox.showinfo("情報", "先に「マップ生成」を実行してください。")
            return
        dest = filedialog.asksaveasfilename(
            defaultextension=".ppm",
            filetypes=[("PPM画像", "*.ppm"), ("すべてのファイル", "*.*")],
            initialfile="cubiomes_map.ppm")
        if not dest:
            return
        try:
            with open(self._map_ppm_path, "rb") as src, open(dest, "wb") as dst:
                dst.write(src.read())
            self._set_status(f"保存しました: {dest}")
        except Exception as e:
            messagebox.showerror("保存エラー", str(e))

    # ------------------------------------------------------------------
    # タブ3: ストラクチャー探索
    # ------------------------------------------------------------------
    def _build_struct_tab(self, parent):
        tab = ttk.Frame(parent)

        form = ttk.Frame(tab)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="ストラクチャー:").grid(row=0, column=0, sticky="w")
        self.struct_var = tk.StringVar(value=api.STRUCTURES[0][0])
        ttk.Combobox(
            form, textvariable=self.struct_var, state="readonly", width=26,
            values=[s[0] for s in api.STRUCTURES]).grid(
            row=0, column=1, padx=4)

        ttk.Label(form, text="探索半径(リージョン数):").grid(
            row=0, column=2, sticky="w")
        self.struct_radius_var = tk.StringVar(value="5")
        ttk.Entry(form, textvariable=self.struct_radius_var, width=6).grid(
            row=0, column=3, padx=4)

        ttk.Button(form, text="原点付近を探索",
                   command=self._on_find_structures).grid(
            row=0, column=4, padx=10)

        note = (
            "※ これは公式サンプルと同様の簡易探索です。リージョンごとの理論上の\n"
            "生成位置を計算するだけで、1.18以降の一部の構造物（砂漠ピラミッド等）\n"
            "で起こりうる地形都合による生成失敗までは判定していません。"
        )
        ttk.Label(tab, text=note, foreground="#555").pack(
            padx=10, anchor="w")

        columns = ("no", "x", "z", "dist")
        self.struct_tree = ttk.Treeview(
            tab, columns=columns, show="headings", height=16)
        self.struct_tree.heading("no", text="#")
        self.struct_tree.heading("x", text="X座標")
        self.struct_tree.heading("z", text="Z座標")
        self.struct_tree.heading("dist", text="原点からの距離(ブロック)")
        self.struct_tree.column("no", width=50, anchor="center")
        self.struct_tree.column("x", width=140, anchor="center")
        self.struct_tree.column("z", width=140, anchor="center")
        self.struct_tree.column("dist", width=200, anchor="center")
        self.struct_tree.pack(fill="both", expand=True, padx=10, pady=10)

        return tab

    def _on_find_structures(self):
        struct_name = self.struct_var.get()
        struct_type = None
        for n, v in api.STRUCTURES:
            if n == struct_name:
                struct_type = v
                break

        try:
            mc = self._current_mc()
            seed = self._current_seed()
            radius = int(self.struct_radius_var.get())
        except ValueError as e:
            messagebox.showerror("入力エラー", f"入力値を確認してください。\n{e}")
            return

        if radius <= 0 or radius > 30:
            messagebox.showerror("入力エラー", "探索半径は 1〜30 の間で指定してください。")
            return

        self._set_status("ストラクチャーを探索しています...")
        for item in self.struct_tree.get_children():
            self.struct_tree.delete(item)

        def worker():
            try:
                results = api.find_structures(
                    struct_type, mc, seed, radius, max_results=400)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("エラー", str(e)))
                self.after(0, lambda: self._set_status("探索に失敗しました。"))
                return

            results.sort(key=lambda p: p[0] ** 2 + p[1] ** 2)

            def apply_result():
                for i, (x, z) in enumerate(results, start=1):
                    dist = int((x ** 2 + z ** 2) ** 0.5)
                    self.struct_tree.insert(
                        "", "end", values=(i, x, z, dist))
                self._set_status(f"{len(results)} 件見つかりました。")

            self.after(0, apply_result)

        threading.Thread(target=worker, daemon=True).start()


def main():
    try:
        app = CubiomesGUI()
    except FileNotFoundError as e:
        # tkinterだけは起動してエラーダイアログを出す
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ライブラリが見つかりません", str(e))
        sys.exit(1)
    app.mainloop()


if __name__ == "__main__":
    main()
