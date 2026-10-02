import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont


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
        self.root.geometry("1150x760")

        self.current_image = None
        self.current_path = None
        self.preview_photo = None

        self.target_color = (255, 0, 0)
        self.new_color = (0, 0, 255)

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
        self._build_tab_merge()
        self._build_tab_watermark()
        self._build_tab_slideshow()

        right_frame = ttk.LabelFrame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(right_frame, text="Тут буде зображення",
                                       anchor="center")
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        ttk.Button(tab, text="Вилучити виділену область",
                   command=self.do_crop_remove).pack(fill=tk.X, pady=5)
        ttk.Button(tab, text="Обрізати (залишити тільки виділене)",
                   command=self.do_crop_keep).pack(fill=tk.X, pady=5)


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

    def _build_tab_merge(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="8. Об'єднання")

        self.merge_second_path = tk.StringVar(value="")
        pf = ttk.Frame(tab)
        pf.pack(fill=tk.X, pady=5)
        ttk.Button(pf, text="Вибрати друге зображення...",
                   command=self.choose_merge_second).pack(side=tk.LEFT)

        self.merge_dir = tk.StringVar(value="horizontal")
        df = ttk.Frame(tab)
        df.pack(fill=tk.X, pady=5)
        ttk.Label(df, text="Напрямок:", width=12).pack(side=tk.LEFT)
        ttk.Radiobutton(df, text="Горизонтально",
                        variable=self.merge_dir,
                        value="horizontal").pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(df, text="Вертикально",
                        variable=self.merge_dir,
                        value="vertical").pack(side=tk.LEFT, padx=3)

        ttk.Button(tab, text="Об'єднати",
                   command=self.do_merge).pack(fill=tk.X, pady=10)

        
        

 
    def _build_tab_watermark(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="9. Водяний знак")

        ttk.Label(tab, text="Додавання текстового водяного знаку",
                font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        tf = ttk.Frame(tab)
        tf.pack(fill=tk.X, pady=3)
        ttk.Label(tf, text="Текст:", width=12).pack(side=tk.LEFT)
        self.wm_text = tk.StringVar(value="Лабораторна робота")
        ttk.Entry(tf, textvariable=self.wm_text).pack(side=tk.LEFT, fill=tk.X, expand=True)


        pf = ttk.Frame(tab)
        pf.pack(fill=tk.X, pady=3)
        ttk.Label(pf, text="Положення:", width=12).pack(side=tk.LEFT)
        self.wm_pos = tk.StringVar(value="bottom-right")
        ttk.Combobox(pf, textvariable=self.wm_pos, state="readonly",
                    values=["top-left", "top-center", "top-right",
                            "middle-left", "middle-right",
                            "bottom-left", "bottom-center", "bottom-right"],
                    width=16).pack(side=tk.LEFT, fill=tk.X, expand=True)


        sf = ttk.Frame(tab)
        sf.pack(fill=tk.X, pady=3)
        ttk.Label(sf, text="Розмір:", width=12).pack(side=tk.LEFT)
        self.wm_size = tk.IntVar(value=36)
        ttk.Scale(sf, from_=8, to=200, variable=self.wm_size,
                orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        wm_size_lbl = ttk.Label(sf, text="36", width=5)
        wm_size_lbl.pack(side=tk.LEFT)
        self.wm_size.trace_add("write",
            lambda *a: wm_size_lbl.config(text=str(self.wm_size.get())))


        of = ttk.Frame(tab)
        of.pack(fill=tk.X, pady=3)
        ttk.Label(of, text="Прозорість:", width=12).pack(side=tk.LEFT)
        self.wm_opacity = tk.IntVar(value=128)
        ttk.Scale(of, from_=0, to=255, variable=self.wm_opacity,
                orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        wm_op_lbl = ttk.Label(of, text="128", width=5)
        wm_op_lbl.pack(side=tk.LEFT)
        self.wm_opacity.trace_add("write",
            lambda *a: wm_op_lbl.config(text=str(self.wm_opacity.get())))


        cf = ttk.Frame(tab)
        cf.pack(fill=tk.X, pady=3)
        ttk.Label(cf, text="Колір:", width=12).pack(side=tk.LEFT)
        self.wm_color = "#ffffff"
        self.wm_color_preview = tk.Label(cf, width=4, bg="#ffffff", relief=tk.SUNKEN)
        self.wm_color_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(cf, text="Вибрати...",
                command=self.choose_wm_color).pack(side=tk.LEFT)

        ttk.Button(tab, text="Додати водяний знак",
                command=self.do_watermark).pack(fill=tk.X, pady=10)



    def _build_tab_slideshow(self):
            tab = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(tab, text="10. Слайд-шоу")

            ttk.Label(tab, text="Програвач слайд-шоу",
                    font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

            bf = ttk.Frame(tab)
            bf.pack(fill=tk.X, pady=5)
            ttk.Button(bf, text="Додати файли...",
                    command=self.ss_add_files).pack(side=tk.LEFT, padx=2)
            ttk.Button(bf, text="Очистити",
                    command=self.ss_clear).pack(side=tk.LEFT, padx=2)


            lf = ttk.LabelFrame(tab, text="Черга слайдів")
            lf.pack(fill=tk.BOTH, expand=True, pady=5)
            self.ss_listbox = tk.Listbox(lf, height=8)
            self.ss_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb = ttk.Scrollbar(lf, orient=tk.VERTICAL,
                            command=self.ss_listbox.yview)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            self.ss_listbox.config(yscrollcommand=sb.set)

            self.ss_files = []  


            pf = ttk.Frame(tab)
            pf.pack(fill=tk.X, pady=3)
            ttk.Label(pf, text="Затримка, мс:", width=14).pack(side=tk.LEFT)
            self.ss_delay = tk.IntVar(value=1500)
            ttk.Spinbox(pf, from_=100, to=10000, increment=100,
                        textvariable=self.ss_delay, width=8).pack(side=tk.LEFT)

            # Керування
            cf = ttk.Frame(tab)
            cf.pack(fill=tk.X, pady=8)
            self.ss_btn_start = ttk.Button(cf, text="Старт",
                                        command=self.ss_start)
            self.ss_btn_start.pack(side=tk.LEFT, padx=2)

            self.ss_btn_stop = ttk.Button(cf, text="Стоп",
                                        command=self.ss_stop, state=tk.DISABLED)
            self.ss_btn_stop.pack(side=tk.LEFT, padx=2)


            self.ss_index = 0
            self.ss_running = False
            self.ss_job = None


    def choose_merge_second(self):
        path = filedialog.askopenfilename(
            title="Друге зображення",
            filetypes=[("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp")]
        )
        if path:
            self.merge_second_path.set(path)


    def do_merge(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте перше зображення")
            return
        if not self.merge_second_path.get():
            messagebox.showwarning("Увага", "Виберіть друге зображення")
            return

        try:
            img1 = self.current_image.convert("RGB")
            img2 = load_image(self.merge_second_path.get()).convert("RGB")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося відкрити друге зображення:\n{e}")
            return

        horizontal = self.merge_dir.get() == "horizontal"

        if horizontal:
            target_h = min(img1.height, img2.height)
            img1 = self._resize_to_height(img1, target_h)
            img2 = self._resize_to_height(img2, target_h)

            result_w = img1.width + img2.width
            result_h = target_h
            result = Image.new("RGB", (result_w, result_h))
            result.paste(img1, (0, 0))
            result.paste(img2, (img1.width, 0))
        else:
            target_w = min(img1.width, img2.width)
            img1 = self._resize_to_width(img1, target_w)
            img2 = self._resize_to_width(img2, target_w)

            result_w = target_w
            result_h = img1.height + img2.height
            result = Image.new("RGB", (result_w, result_h))
            result.paste(img1, (0, 0))
            result.paste(img2, (0, img1.height))

        self.current_image = result
        self.reset_crop()
        self.update_preview()


    def _resize_to_height(self, img, target_h):
        if img.height == target_h:
            return img
        ratio = target_h / img.height
        new_w = max(1, int(round(img.width * ratio)))
        return img.resize((new_w, target_h), Image.LANCZOS)


    def _resize_to_width(self, img, target_w):
        if img.width == target_w:
            return img
        ratio = target_w / img.width
        new_h = max(1, int(round(img.height * ratio)))
        return img.resize((target_w, new_h), Image.LANCZOS)


    def choose_wm_color(self):
        color = colorchooser.askcolor(color=self.wm_color,
                                      title="Колір водяного знаку")[0]
        if color:
            self.wm_color = self._rgb_to_hex(tuple(int(c) for c in color))
            self.wm_color_preview.config(bg=self.wm_color)

    def _get_wm_font(self):
        size = int(self.wm_size.get())

        for candidate in ["arial.ttf", "DejaVuSans.ttf", "Arial.ttf",
                          "LiberationSans-Regular.ttf"]:
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _compute_wm_position(self, img_w, img_h, text_w, text_h, pos, margin=20):
        if pos.startswith("top"):
            y = margin
        elif pos.startswith("middle"):
            y = (img_h - text_h) // 2
        else:
            y = img_h - text_h - margin

        if pos.endswith("left"):
            x = margin
        elif pos.endswith("center") or pos == "center":
            x = (img_w - text_w) // 2
        else:
            x = img_w - text_w - margin
        return x, y

    def _render_watermark(self, base_img):
        text = self.wm_text.get()
        if not text:
            return base_img.copy()

        img = base_img.convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        font = self._get_wm_font()


        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = font.getsize(text)

        x, y = self._compute_wm_position(img.width, img.height,
                                         text_w, text_h, self.wm_pos.get())

      
        rgb = tuple(int(self.wm_color[i:i+2], 16) for i in (1, 3, 5))
        alpha = int(self.wm_opacity.get())
        fill = rgb + (alpha,)

        draw.text((x, y), text, font=font, fill=fill)

        result = Image.alpha_composite(img, overlay)
        return result

    def do_watermark(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return
        self.current_image = self._render_watermark(self.current_image)
        self.update_preview()


    def ss_add_files(self):
        paths = filedialog.askopenfilenames(
            title="Виберіть зображення для слайд-шоу",
            filetypes=[("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp")]
        )
        for p in paths:
            self.ss_files.append(p)
        self._ss_refresh_list()


    def ss_clear(self):
        self.ss_files = []
        self._ss_refresh_list()

    def _ss_refresh_list(self):
        self.ss_listbox.delete(0, tk.END)
        for i, p in enumerate(self.ss_files, 1):
            self.ss_listbox.insert(tk.END, f"{i}. {os.path.basename(p)}")

    def ss_start(self):
        if not self.ss_files:
            messagebox.showwarning("Увага", "Додайте хоча б одне зображення")
            return
        self.ss_running = True
        self.ss_index = 0
        self.ss_btn_start.config(state=tk.DISABLED)
        self.ss_btn_stop.config(state=tk.NORMAL)
        self._ss_show_next()

    def _ss_show_next(self):
        if not self.ss_running:
            return
        if self.ss_index >= len(self.ss_files):
            self.ss_index = 0

        path = self.ss_files[self.ss_index]
        try:
            img = load_image(path)
            self.current_image = img
            self.current_path = path
            self.reset_crop()
            self.update_preview()

            self.ss_listbox.selection_clear(0, tk.END)
            self.ss_listbox.selection_set(self.ss_index)
            self.ss_listbox.see(self.ss_index)
        except Exception as e:
            print(f"Не вдалося показати {path}: {e}")

        self.ss_index += 1
        if self.ss_running: 
            self.ss_job = self.root.after(self.ss_delay.get(), self._ss_show_next)

    def ss_stop(self):
        self.ss_running = False
        if self.ss_job is not None:
            try:
                self.root.after_cancel(self.ss_job)
            except Exception:
                pass
            self.ss_job = None
        self.ss_btn_start.config(state=tk.NORMAL)
        self.ss_btn_stop.config(state=tk.DISABLED)
 
 
    def do_opacity(self):
        if self.current_image is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення")
            return

        alpha = int(self.opacity_var.get() * 255 / 100)
        img = self.current_image.convert("RGBA")
        data = np.array(img)
        data[:, :, 3] = alpha
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


    def on_label_resize(self):
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