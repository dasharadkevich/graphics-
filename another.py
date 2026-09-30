import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import numpy as np
from PIL import Image, ImageTk


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} КБ"
    else:
        return f"{size_bytes / (1024 ** 2):.2f} МБ"


def load_image(path):
    return Image.open(path).convert("RGB")


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота №2 — Обробка зображень")
        self.root.geometry("1150x760")

        self.current_image = None
        self.current_path = None
        self.preview_photo = None

        self.target_color = (255, 0, 0)
        self.new_color = (0, 0, 255)

        # Для кадрування
        self.crop_rect = None          
        self.canvas_rect_id = None
        self.start_x = None
        self.start_y = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Відкрити зображення",
                   command=self.open_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Відкрити кілька (пакетно)",
                   command=self.open_multiple).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Зберегти результат",
                   command=self.save_result).pack(side=tk.LEFT, padx=5)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.Frame(main_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self._build_tab_format()
        self._build_tab_resize()
        self._build_tab_recolor()
        self._build_tab_balance()
        self._build_tab_opacity()
        self._build_tab_crop()
        self._build_tab_contrast()

        right_frame = ttk.LabelFrame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(right_frame, text="Тут буде зображення",
                                       anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Прив'язка подій миші для кадрування
        self.preview_label.bind("<ButtonPress-1>", self.on_mouse_down)
        self.preview_label.bind("<B1-Motion>", self.on_mouse_drag)
        self.preview_label.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.preview_label.bind("<Configure>", self.on_label_resize)

    def _build_tab_format(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="1. Формат")

        self.format_var = tk.StringVar(value="JPEG")
        fmt_combo = ttk.Combobox(tab, textvariable=self.format_var,
                                 values=["JPEG", "PNG", "BMP", "GIF", "TIFF", "WEBP"],
                                 state="readonly")
        fmt_combo.pack(fill=tk.X, pady=5)

        ttk.Button(tab, text="Конвертувати та зберегти",
                   command=self.do_convert_format).pack(fill=tk.X, pady=10)

        self.format_info = ttk.Label(tab, text="", justify=tk.LEFT,
                                     foreground="#444")
        self.format_info.pack(fill=tk.X, pady=(10, 0))

    def _build_tab_resize(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="2. Розмір")

        self.keep_aspect = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Зберігати пропорції",
                        variable=self.keep_aspect).pack(anchor=tk.W, pady=5)

        wf = ttk.Frame(tab)
        wf.pack(fill=tk.X, pady=3)
        ttk.Label(wf, text="Ширина (px):").pack(side=tk.LEFT)
        self.width_var = tk.StringVar()
        ttk.Entry(wf, textvariable=self.width_var, width=14).pack(side=tk.LEFT)

        hf = ttk.Frame(tab)
        hf.pack(fill=tk.X, pady=3)
        ttk.Label(hf, text="Висота (px):", width=14).pack(side=tk.LEFT)
        self.height_var = tk.StringVar()
        ttk.Entry(hf, textvariable=self.height_var, width=14).pack(side=tk.LEFT)

        ttk.Button(tab, text="Змінити розмір",
                   command=self.do_resize).pack(fill=tk.X, pady=10)

        self.resize_info = ttk.Label(tab, text="", justify=tk.LEFT,
                                     foreground="#444")
        self.resize_info.pack(fill=tk.X, pady=(10, 0))

    def _build_tab_recolor(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="3. Колір")

        tf = ttk.Frame(tab)
        tf.pack(fill=tk.X, pady=5)
        ttk.Label(tf, text="Цільовий колір:", width=16).pack(side=tk.LEFT)
        self.target_preview = tk.Label(tf, width=4, bg="#ff0000", relief=tk.SUNKEN)
        self.target_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(tf, text="Вибрати...",
                   command=self.choose_target_color).pack(side=tk.LEFT)

        nf = ttk.Frame(tab)
        nf.pack(fill=tk.X, pady=5)
        ttk.Label(nf, text="Новий колір:", width=16).pack(side=tk.LEFT)
        self.new_preview = tk.Label(nf, width=4, bg="#0000ff", relief=tk.SUNKEN)
        self.new_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(nf, text="Вибрати...",
                   command=self.choose_new_color).pack(side=tk.LEFT)

        ttk.Button(tab, text="Замінити колір",
                   command=self.do_recolor).pack(fill=tk.X, pady=10)

    def _build_tab_balance(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="4. Баланс")

        ttk.Label(tab, text="Корекція колірного балансу").pack(anchor=tk.W, pady=(0, 10))

        self.r_shift = tk.IntVar(value=0)
        self.g_shift = tk.IntVar(value=0)
        self.b_shift = tk.IntVar(value=0)

        for var, name in [(self.r_shift, "Червоний"),
                          (self.g_shift, "Зелений"),
                          (self.b_shift, "Синій")]:
            frame = ttk.Frame(tab)
            frame.pack(fill=tk.X, pady=4)
            ttk.Label(frame, text=f"{name}:", width=10).pack(side=tk.LEFT)
            ttk.Scale(frame, from_=-100, to=100, variable=var,
                      orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
            lbl = ttk.Label(frame, text="0", width=5)
            lbl.pack(side=tk.LEFT)
            var.trace_add("write",
                          lambda *a, v=var, l=lbl: l.config(text=str(v.get())))

        ttk.Button(tab, text="Застосувати корекцію",
                   command=self.do_balance).pack(fill=tk.X, pady=10)


    def _build_tab_opacity(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="5. Прозорість")

        ttk.Label(tab, text="Зміна прозорості шару",
                  font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        self.opacity_var = tk.IntVar(value=100)
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text="Прозорість (%):", width=16).pack(side=tk.LEFT)
        ttk.Scale(frame, from_=0, to=100, variable=self.opacity_var,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        lbl = ttk.Label(frame, text="100", width=5)
        lbl.pack(side=tk.LEFT)
        self.opacity_var.trace_add("write",
                                   lambda *a: lbl.config(text=str(self.opacity_var.get())))

        ttk.Button(tab, text="Застосувати прозорість",
                   command=self.do_opacity).pack(fill=tk.X, pady=10)

    def _build_tab_crop(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="6. Кадрування")

        ttk.Label(tab, text="Розбиття на частини",
                  font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        pf = ttk.Frame(tab)
        pf.pack(fill=tk.X, pady=3)
        ttk.Label(pf, text="Кількість частин:", width=16).pack(side=tk.LEFT)
        self.parts_var = tk.IntVar(value=4)
        ttk.Spinbox(pf, from_=2, to=100, textvariable=self.parts_var,
                    width=6).pack(side=tk.LEFT)

        ttk.Button(tab, text="Розбити та зберегти частини",
                   command=self.do_split).pack(fill=tk.X, pady=5)

        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(tab, text="Виділення області",
                  font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(tab, text="Виділіть область мишею на зображенні,\n"
                            "потім виберіть дію:",
                  justify=tk.LEFT, foreground="#666").pack(anchor=tk.W)

        ttk.Button(tab, text="Вилучити виділену область",
                   command=self.do_crop_remove).pack(fill=tk.X, pady=5)
        ttk.Button(tab, text="Обрізати (залишити тільки виділене)",
                   command=self.do_crop_keep).pack(fill=tk.X, pady=5)
        ttk.Button(tab, text="Скинути виділення",
                   command=self.reset_crop).pack(fill=tk.X, pady=5)

        self.crop_info = ttk.Label(tab, text="", justify=tk.LEFT, foreground="#444")
        self.crop_info.pack(fill=tk.X, pady=(10, 0))

    def _build_tab_contrast(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="7. Контраст")

        ttk.Label(tab, text="Збільшення контрастності",
                  font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        frame = ttk.Frame(tab)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text="Коефіцієнт:", width=12).pack(side=tk.LEFT)
        self.contrast_var = tk.DoubleVar(value=1.5)
        ttk.Scale(frame, from_=0.5, to=3.0, variable=self.contrast_var,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        lbl = ttk.Label(frame, text="1.5", width=5)
        lbl.pack(side=tk.LEFT)
        self.contrast_var.trace_add(
            "write",
            lambda *a: lbl.config(text=f"{self.contrast_var.get():.2f}")
        )

        ttk.Button(tab, text="Застосувати контраст",
                   command=self.do_contrast).pack(fill=tk.X, pady=10)

        ttk.Label(tab, text="Коефіцієнт > 1 — підвищення контрасту,\n"
                            "< 1 — зниження контрасту.",
                  justify=tk.LEFT, foreground="#666").pack(anchor=tk.W, pady=(10, 0))
 
 
    def do_opacity(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        alpha = int(self.opacity_var.get() * 255 / 100)
        img = self.current_image.convert("RGBA")
        data = np.array(img)
        data[:, :, 3] = alpha # all image uniformly 
        self.current_image = Image.fromarray(data, mode="RGBA")
        self.update_preview()

    def do_split(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        n = self.parts_var.get()
        if n < 2:
            messagebox.showerror("Помилка", "Кількість частин має бути >= 2")
            return

        out_dir = filedialog.askdirectory(title="Папка для збереження частин")
        if not out_dir:
            return

        w, h = self.current_image.size
        cols = int(np.ceil(np.sqrt(n)))
        rows = int(np.ceil(n / cols))

        part_w = w // cols
        part_h = h // rows
        count = 0
        for r in range(rows):
            for c in range(cols):
                if count >= n:
                    break
                left = c * part_w
                upper = r * part_h
                right = w if c == cols - 1 else left + part_w
                lower = h if r == rows - 1 else upper + part_h
                piece = self.current_image.crop((left, upper, right, lower))
                piece.save(os.path.join(out_dir, f"part_{count + 1}.png"))
                count += 1

        messagebox.showinfo("Готово",
                            f"Зображення розбито на {count} частин\n"
                            f"Папка: {out_dir}")

    def do_crop_remove(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return
        if self.crop_rect is None:
            messagebox.showwarning("Увага", "Спочатку виділіть область")
            return

        x1, y1, x2, y2 = self.crop_rect

   
        img = self.current_image.convert("RGBA")

        data = np.array(img)


        data[y1:y2, x1:x2, 3] = 0

        self.current_image = Image.fromarray(data, mode="RGBA")

        self.reset_crop()
        self.update_preview()

    def do_crop_keep(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return
        if self.crop_rect is None:
            messagebox.showwarning("Увага", "Спочатку виділіть область")
            return

        x1, y1, x2, y2 = self.crop_rect
        self.current_image = self.current_image.crop((x1, y1, x2, y2))
        self.reset_crop()
        self.update_preview()
        self.crop_info.config(text="Зображення обрізано до виділеної області")

    def reset_crop(self):
        self.crop_rect = None
        self.start_x = None
        self.start_y = None
        if self.canvas_rect_id is not None:
            try:
                self.preview_label.delete("crop_rect")
            except Exception:
                pass
            self.canvas_rect_id = None



    def do_contrast(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        factor = float(self.contrast_var.get())
        data = np.array(self.current_image).astype(np.float32)
        data = (data - 128) * factor + 128

        data = np.clip(data, 0, 255)
        
        data = data.astype(np.uint8)

        self.current_image = Image.fromarray(data)

        self.update_preview()


    def open_image(self):
        path = filedialog.askopenfilename(
            title="Виберіть зображення",
            filetypes=[("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                       ("Усі файли", "*.*")]
        )
        if not path:
            return
        try:
            self.current_image = load_image(path)
            self.current_path = path
            self.reset_crop()
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося відкрити файл:\n{e}")

    def open_multiple(self):
        paths = filedialog.askopenfilenames(
            title="Виберіть кілька зображень",
            filetypes=[("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp")]
        )
        if not paths:
            return

        fmt = self.format_var.get()
        out_dir = filedialog.askdirectory(title="Папка для збереження")
        if not out_dir:
            return

        count = 0
        for p in paths:
            try:
                img = load_image(p)
                base = os.path.splitext(os.path.basename(p))[0]
                ext = fmt.lower()
                if ext == "jpeg":
                    ext = "jpg"
                out = os.path.join(out_dir, f"{base}.{ext}")
                img.save(out, format=fmt.upper())
                count += 1
            except Exception as e:
                print(f"Помилка з {p}: {e}")

        messagebox.showinfo("Готово",
                            f"Конвертовано {count} з {len(paths)} файлів\n"
                            f"Формат: {fmt}\nПапка: {out_dir}")

    def save_result(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return
        path = filedialog.asksaveasfilename(
            title="Зберегти результат",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"),
                       ("BMP", "*.bmp"), ("TIFF", "*.tiff"),
                       ("WEBP", "*.webp")]
        )
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            fmt = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",
                   ".bmp": "BMP", ".tiff": "TIFF", ".webp": "WEBP"}.get(ext, "PNG")
            img = self.current_image
            if fmt in ("JPEG", "BMP") and img.mode == "RGBA":
                img = img.convert("RGB")
            img.save(path, format=fmt)
            size = os.path.getsize(path)
            messagebox.showinfo("Збережено",
                                f"Файл збережено:\n{path}\nРозмір: {format_size(size)}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти:\n{e}")

    def update_preview(self):
        if self.current_image is None:
            return
        max_w, max_h = 650, 620
        img = self.current_image.copy()
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.preview_photo, text="")
        # Запам'ятовуємо масштаб та зсув для перетворення координат
        orig_w, orig_h = self.current_image.size
        prev_w, prev_h = img.size
        self.scale_factor = orig_w / prev_w if prev_w else 1.0
        self.offset_x = 0
        self.offset_y = 0

    # ---------- Обробка миші для кадрування ----------
    def on_label_resize(self, event):
        self.update_preview()

    def on_mouse_down(self, event):
        if self.current_image is None:
            return
        self.start_x = event.x
        self.start_y = event.y
        if self.canvas_rect_id is not None:
            self.preview_label.delete("crop_rect")
        self.canvas_rect_id = self.preview_label.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2, tags="crop_rect"
        )

    def on_mouse_drag(self, event):
        if self.start_x is None or self.canvas_rect_id is None:
            return
        self.preview_label.coords(self.canvas_rect_id,
                                  self.start_x, self.start_y,
                                  event.x, event.y)

    def on_mouse_up(self, event):
        if self.start_x is None or self.current_image is None:
            return

        x1_canvas = min(self.start_x, event.x)
        y1_canvas = min(self.start_y, event.y)
        x2_canvas = max(self.start_x, event.x)
        y2_canvas = max(self.start_y, event.y)

        if x2_canvas - x1_canvas < 3 or y2_canvas - y1_canvas < 3:
            self.reset_crop()
            return

        label_w = self.preview_label.winfo_width()
        label_h = self.preview_label.winfo_height()
        if self.preview_photo is None:
            return
        prev_w = self.preview_photo.width()
        prev_h = self.preview_photo.height()
        offset_x = (label_w - prev_w) // 2
        offset_y = (label_h - prev_h) // 2

        x1 = int((x1_canvas - offset_x) * self.scale_factor)
        y1 = int((y1_canvas - offset_y) * self.scale_factor)
        x2 = int((x2_canvas - offset_x) * self.scale_factor)
        y2 = int((y2_canvas - offset_y) * self.scale_factor)

        w, h = self.current_image.size
        x1 = max(0, min(w, x1))
        y1 = max(0, min(h, y1))
        x2 = max(0, min(w, x2))
        y2 = max(0, min(h, y2))

        if x2 - x1 < 2 or y2 - y1 < 2:
            self.reset_crop()
            return

        self.crop_rect = (x1, y1, x2, y2)
        self.crop_info.config(
            text=f"Виділено: ({x1}, {y1}) — ({x2}, {y2})\n"
                 f"Розмір: {x2 - x1} x {y2 - y1} px"
        )

    # ---------- Інші обробники ----------
    def do_convert_format(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return
        fmt = self.format_var.get()
        ext = fmt.lower()
        if ext == "jpeg":
            ext = "jpg"

        path = filedialog.asksaveasfilename(
            title="Зберегти як",
            defaultextension=f".{ext}",
            initialfile=f"converted.{ext}"
        )
        if not path:
            return
        try:
            img = self.current_image
            if fmt in ("JPEG", "BMP") and img.mode == "RGBA":
                img = img.convert("RGB")
            img.save(path, format=fmt.upper())

            new_size = os.path.getsize(path)
            old_size = os.path.getsize(self.current_path) if self.current_path else 0
            info = (f"Формат: {fmt}\n"
                    f"Оригінал: {format_size(old_size)}\n"
                    f"Результат: {format_size(new_size)}\n")
            self.format_info.config(text=info)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти:\n{e}")

    def do_resize(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        try:
            w = int(self.width_var.get()) if self.width_var.get().strip() else None
            h = int(self.height_var.get()) if self.height_var.get().strip() else None
        except ValueError:
            messagebox.showerror("Помилка", "Ширина та висота мають бути числами")
            return

        if w is None and h is None:
            messagebox.showwarning("Увага", "Введіть ширину або висоту")
            return

        orig_w, orig_h = self.current_image.size
        ratio = orig_w / orig_h

        if self.keep_aspect.get():
            if w and not h:
                h = int(w / ratio)
            elif h and not w:
                w = int(h * ratio)
            elif w and h:
                h = int(w / ratio)
        else:
            w = w or orig_w
            h = h or orig_h

        self.current_image = self.current_image.resize((w, h), Image.LANCZOS)
        self.reset_crop()
        self.update_preview()
        self.resize_info.config(
            text=f"Було: {orig_w}x{orig_h}\nСтало: {w}x{h}\n"
                 f"Пропорції: {'збережено' if self.keep_aspect.get() else 'змінено'}"
        )

    def choose_target_color(self):
        color = colorchooser.askcolor(color=self._rgb_to_hex(self.target_color),
                                      title="Цільовий колір")[0]
        if color:
            self.target_color = tuple(int(c) for c in color)
            self.target_preview.config(bg=self._rgb_to_hex(self.target_color))

    def choose_new_color(self):
        color = colorchooser.askcolor(color=self._rgb_to_hex(self.new_color),
                                      title="Новий колір")[0]
        if color:
            self.new_color = tuple(int(c) for c in color)
            self.new_preview.config(bg=self._rgb_to_hex(self.new_color))

    @staticmethod
    def _rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def do_recolor(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        data = np.array(self.current_image.convert("RGB")).astype(np.int32)
        target = np.array(self.target_color, dtype=np.int32)
        new = np.array(self.new_color, dtype=np.int32)
        tol = 30

        diff = np.sqrt(np.sum((data - target) ** 2, axis=2))
        mask = diff <= tol

        data[mask] = new
        data = np.clip(data, 0, 255).astype(np.uint8)
        self.current_image = Image.fromarray(data)
        self.update_preview()

    def do_balance(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        data = np.array(self.current_image.convert("RGB")).astype(np.int16)
        data[:, :, 0] += self.r_shift.get()
        data[:, :, 1] += self.g_shift.get()
        data[:, :, 2] += self.b_shift.get()
        data = np.clip(data, 0, 255).astype(np.uint8)

        self.current_image = Image.fromarray(data)
        self.update_preview()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()