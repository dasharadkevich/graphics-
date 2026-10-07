import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk


class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обробка кольорового зображення")
        self.root.geometry("1200x750")

        self.original_img = None
        self.img_array = None
        self.brightness = None
        self.current_photo = None

        self._build_ui()

    def _build_ui(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X)

        top_buttons = [
            ("Відкрити зображення",       self.open_image),
            ("Показати матрицю яскравості", self.show_brightness_matrix),
            ("Гістограма кольорового",      self.show_color_histogram),
            ("Гістограма сірого",           self.show_gray_histogram),
        ]

        for text, command in top_buttons:
            tk.Button(top_frame, text=text, command=command).pack(side=tk.LEFT)

        ops_frame = tk.LabelFrame(self.root, text="Зміна кольоровості")
        ops_frame.pack(fill=tk.X)

        for text, cmd in [
                ("Бінаризація (Ч/Б)", self.binarize),
                ("Відтінки сірого", self.to_grayscale),
                ("Негатив", self.negative),
                ("Оригінал", self.show_original),
            ]:       
            tk.Button(ops_frame, text=text, command=cmd).pack(side=tk.LEFT)
        

        tk.Label(ops_frame, text="Поріг:").pack(side=tk.LEFT)
        self.threshold_var = tk.IntVar(value=128)
        self.threshold_scale = tk.Scale(ops_frame, from_=0, to=255,
                                        orient=tk.HORIZONTAL,
                                        variable=self.threshold_var,
                                        length=200)
        self.threshold_scale.pack(side=tk.LEFT)

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)


        left_frame = tk.LabelFrame(main_frame, text="Зображення")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(left_frame, text="Тут буде зображення")
        self.image_label.pack(fill=tk.BOTH, expand=True)


        right_frame = tk.LabelFrame(main_frame, text="Гістограма / Матриця")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.plot_canvas = tk.Canvas(right_frame, bg='white',
                                     width=500, height=550,
                                     highlightthickness=0)
        self.plot_canvas.pack(fill=tk.BOTH, expand=True)


    def open_image(self):
        path = filedialog.askopenfilename(
            title="Виберіть зображення",
            filetypes=[("Зображення", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                       ("Усі файли", "*.*")]
        )
        if not path:
            return

        try:
            self.original_img = Image.open(path).convert('RGB')
            self.img_array = np.array(self.original_img)
            self._compute_brightness()

            self.show_original()

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося відкрити файл:\n{e}")

    def _compute_brightness(self):
        self.brightness = (0.299 * self.img_array[:, :, 0] +
                           0.587 * self.img_array[:, :, 1] +
                           0.114 * self.img_array[:, :, 2]).astype(np.uint8)

    def show_original(self):
        if self.original_img is None:
            return
        self._display_image(self.original_img, "1. Первинне кольорове зображення")



    def show_brightness_matrix(self):
        if self.brightness is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення!")
            return

        top = tk.Toplevel(self.root)
        top.title("Матриця значень яскравості")
        top.geometry("600x500")

        text_frame = tk.Frame(top)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text = tk.Text(text_frame, font=11,
                       yscrollcommand=scrollbar.set, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        h = min(100, self.brightness.shape[0])
        w = min(100, self.brightness.shape[1])
        text.insert(tk.END,
                    f"Розмір матриці: {self.brightness.shape}\n"
                    f"Мін: {self.brightness.min()}, "
                    f"Макс: {self.brightness.max()}, "
                    f"Середнє: {self.brightness.mean():.2f}\n\n"
                    f"Фрагмент {h}x{w}:\n" + "-" * 80 + "\n")

        for row in self.brightness[:h, :w]:
            text.insert(tk.END, " ".join(f"{v:3d}" for v in row) + "\n")



    def show_color_histogram(self):
        if self.img_array is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення!")
            return
        self._draw_histogram(self.img_array,
                             title="Гістограма кольорового зображення")



    def binarize(self):
        if self.brightness is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення!")
            return

        threshold = self.threshold_var.get()
        binary = np.where(self.brightness >= threshold, 255, 0).astype(np.uint8)
        result = Image.fromarray(binary, mode='L')
        self._display_image(result, f"4.1 Бінаризація (поріг = {threshold})")


    def to_grayscale(self):
        if self.brightness is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення!")
            return

        result = Image.fromarray(self.brightness, mode='L')
        self._display_image(result, "4.2 Відтінки сірого")


    def negative(self):
        if self.img_array is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення!")
            return

        negative_arr = 255 - self.img_array
        result = Image.fromarray(negative_arr.astype(np.uint8), mode='RGB')
        self._display_image(result, "4.3 Негатив")
   


    def show_gray_histogram(self):
        if self.brightness is None:
            messagebox.showwarning("Увага", "Спочатку відкрийте зображення!")
            return

        self._draw_histogram(self.brightness,
                             title="Гістограма сірого зображення",
                             is_gray=True)



    def _display_image(self, pil_image, title=""):
        self.image_label.update_idletasks()

        img = pil_image.copy()

        self.current_photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.current_photo, text="")
        self.root.title(f"Обробка зображення - {title}")

    def _draw_histogram(self, data, title="", is_gray=False):
        self.plot_canvas.delete("all")
        self.plot_canvas.update_idletasks()

        W = self.plot_canvas.winfo_width() or 500
        H = self.plot_canvas.winfo_height() or 550

        pad_left, pad_right = 60, 20
        pad_top, pad_bottom = 40, 60
        plot_w = W - pad_left - pad_right
        plot_h = H - pad_top - pad_bottom

        self.plot_canvas.create_text(W / 2, 20, text=title,
                                     font=('Arial', 11, 'bold'))

        if is_gray:
            hist, _ = np.histogram(data, bins=256, range=(0, 256))
            channels = [('gray', hist, 'gray')]
        else:
            channels = [
                ('R', np.histogram(data[:, :, 0], bins=256,
                                   range=(0, 256))[0], 'red'),
                ('G', np.histogram(data[:, :, 1], bins=256,
                                   range=(0, 256))[0], 'green'),
                ('B', np.histogram(data[:, :, 2], bins=256,
                                   range=(0, 256))[0], 'blue'),
            ]

        max_val = max(h.max() for _, h, _ in channels) or 1

        self.plot_canvas.create_line(pad_left, pad_top,
                                     pad_left, pad_top + plot_h,
                                     pad_left + plot_w, pad_top + plot_h,
                                     width=1, fill='black')

        for x_val in range(0, 256, 32):
            x = pad_left + (x_val / 255) * plot_w
            self.plot_canvas.create_line(x, pad_top + plot_h,
                                         x, pad_top + plot_h + 5, fill='black')
            self.plot_canvas.create_text(x, pad_top + plot_h + 18,
                                         text=str(x_val), font=('Arial', 8))

        self.plot_canvas.create_text(pad_left + plot_w / 2,
                                     H - 15,
                                     text="Значення інтенсивності",
                                     font=('Arial', 9))

        for i in range(5):
            y_val = int(max_val * i / 4)
            y = pad_top + plot_h - (y_val / max_val) * plot_h
            self.plot_canvas.create_line(pad_left - 5, y, pad_left, y, fill='black')
            self.plot_canvas.create_text(pad_left - 10, y,
                                         text=str(y_val), anchor='e',
                                         font=('Arial', 8))

        bin_w = plot_w / 256
        for name, hist, color in channels:
            for i, val in enumerate(hist):
                if val == 0:
                    continue
                x = pad_left + i * bin_w
                h_px = (val / max_val) * plot_h
                self.plot_canvas.create_line(x, pad_top + plot_h,
                                             x, pad_top + plot_h - h_px,
                                             fill=color, width=max(1, int(bin_w)))

        lx = W - 110
        ly = pad_top + 10
        for i, (name, _, color) in enumerate(channels):
            self.plot_canvas.create_rectangle(lx, ly + i * 20,
                                              lx + 15, ly + i * 20 + 15,
                                              fill=color, outline=color)
            self.plot_canvas.create_text(lx + 22, ly + i * 20 + 8,
                                         text=name, anchor='w',
                                         font=('Arial', 9))


if __name__ == '__main__':
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()