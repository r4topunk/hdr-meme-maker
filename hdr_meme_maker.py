#!/usr/bin/env python3
"""
HDR Meme Maker + Deep Fryer - Ferramenta de experimentação artística
Cria imagens HDR reais e memes deep fried
"""

import sys
import os
import subprocess
import shutil
import tempfile
import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
from PIL.ImageQt import ImageQt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QMessageBox, QFrame,
    QGroupBox, QGridLayout, QComboBox, QTabWidget, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap

COLORS = {
    "bg": "#0a0a0a",
    "bg_panel": "#0d0d0d",
    "green": "#00ff00",
    "green_dim": "#00aa00",
    "green_dark": "#005500",
    "text_dim": "#008800",
    "danger": "#ff3333",
    "orange": "#ff8c00",
}

MONO_FONT = "Monaco, Menlo, Consolas, monospace"

EXIFTOOL_CONFIG = """
%Image::ExifTool::UserDefined = (
    'Image::ExifTool::Apple::Main' => {
        0x0021 => {
            Name => 'HDRGamma',
            Writable => 'float',
        },
    },
);
1;
"""

APPLE_MAKERNOTES_HEX = (
    "4170706c6500004d4d002a000000080005000100030000000100050000"
    "000200070001000000106170706c650000000000000000000003000300"
    "01000000010000000004000a00010000004a0000000500050001000000"
    "520000000000000000010000000100000001000000"
)


class ImagePreview(QLabel):
    def __init__(self, title=""):
        super().__init__()
        self.title = title
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(380, 320)
        self.set_placeholder()

    def set_placeholder(self):
        self.setText(f"[ {self.title} ]\n\n> awaiting input...")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg']};
                border: 1px solid {COLORS['green_dark']};
                color: {COLORS['text_dim']};
                font-family: {MONO_FONT};
                font-size: 12px;
            }}
        """)

    def set_image(self, pil_image):
        if pil_image.mode not in ("RGB", "RGBA"):
            pil_image = pil_image.convert("RGB")
        qimage = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg']};
                border: 1px solid {COLORS['green']};
            }}
        """)


class HDRMemeMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.original_image = None
        self.preview_image = None
        self.exiftool_available = shutil.which('exiftool') is not None

        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("HDR_MEME_MAKER // DEEP_FRYER")
        self.setMinimumSize(1200, 850)
        self.resize(1280, 900)

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {COLORS['bg']}; }}
            QWidget {{
                background-color: {COLORS['bg']};
                color: {COLORS['green']};
                font-family: {MONO_FONT};
            }}
            QLabel {{ color: {COLORS['green']}; }}
            QPushButton {{
                background-color: {COLORS['bg']};
                color: {COLORS['green']};
                border: 1px solid {COLORS['green']};
                padding: 6px 12px;
                font-family: {MONO_FONT};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['green']};
                color: {COLORS['bg']};
            }}
            QPushButton:disabled {{
                border-color: {COLORS['green_dark']};
                color: {COLORS['green_dark']};
            }}
            QSlider::groove:horizontal {{
                height: 4px;
                background: {COLORS['green_dark']};
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['green']};
                width: 10px;
                height: 10px;
                margin: -3px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['green']};
            }}
            QGroupBox {{
                border: 1px solid {COLORS['green_dark']};
                margin-top: 10px;
                padding-top: 6px;
                font-size: 10px;
            }}
            QGroupBox::title {{
                color: {COLORS['green']};
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['green_dark']};
                background-color: {COLORS['bg']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg']};
                color: {COLORS['green_dim']};
                border: 1px solid {COLORS['green_dark']};
                padding: 6px 12px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['green_dark']};
                color: {COLORS['green']};
            }}
            QCheckBox {{
                color: {COLORS['green']};
                font-size: 10px;
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
                border: 1px solid {COLORS['green']};
                background-color: {COLORS['bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['green']};
            }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # === PAINEL ESQUERDO: CONTROLES ===
        controls_widget = QWidget()
        controls_widget.setFixedWidth(420)
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(6)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("""┌────────────────────────────────────────────┐
│  ██╗  ██╗██████╗ ██████╗   MEME STUDIO    │
│  ██║  ██║██╔══██╗██╔══██╗  ─────────────  │
│  ███████║██║  ██║██████╔╝  HDR + DEEPFRY  │
│  ██║  ██║██████╔╝██║  ██║  v4.0 ARTIST    │
└────────────────────────────────────────────┘""")
        header.setStyleSheet(f"color: {COLORS['green']}; font-size: 8px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(header)

        # File input
        file_group = QGroupBox("[ FILE ]")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(4)

        self.select_btn = QPushButton("> LOAD IMAGE")
        self.select_btn.clicked.connect(self.select_image)
        file_layout.addWidget(self.select_btn)

        self.file_label = QLabel("no file")
        self.file_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(self.file_label)

        controls_layout.addWidget(file_group)

        # Tabs para diferentes modos
        self.tabs = QTabWidget()

        # === TAB 1: BASIC ===
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.setSpacing(8)

        self.sliders = {}

        basic_sliders = [
            ("saturation", "SATURATION", 0, 50, 10),
            ("contrast", "CONTRAST", 0, 30, 10),
            ("brightness", "BRIGHTNESS", 5, 20, 10),
            ("sharpness", "SHARPNESS", 0, 50, 10),
            ("vibrance", "VIBRANCE", 0, 30, 10),
        ]

        for key, label, min_v, max_v, default in basic_sliders:
            self.create_slider(basic_layout, key, label, min_v, max_v, default)

        basic_layout.addStretch()
        self.tabs.addTab(basic_tab, "BASIC")

        # === TAB 2: HDR ===
        hdr_tab = QWidget()
        hdr_layout = QVBoxLayout(hdr_tab)
        hdr_layout.setSpacing(8)

        hdr_info = QLabel("// Apple HDRGamma EXIF tag")
        hdr_info.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px;")
        hdr_layout.addWidget(hdr_info)

        hdr_sliders = [
            ("hdr_gamma", "HDR GAMMA", 0, 40, 0),
            ("highlights", "HIGHLIGHTS", 0, 30, 10),
            ("shadows", "SHADOWS", 0, 30, 10),
            ("bloom", "BLOOM", 0, 20, 0),
        ]

        for key, label, min_v, max_v, default in hdr_sliders:
            self.create_slider(hdr_layout, key, label, min_v, max_v, default)

        hdr_layout.addStretch()
        self.tabs.addTab(hdr_tab, "HDR")

        # === TAB 3: DEEP FRY ===
        fry_tab = QWidget()
        fry_layout = QVBoxLayout(fry_tab)
        fry_layout.setSpacing(8)

        fry_info = QLabel("// Deep fried meme effects")
        fry_info.setStyleSheet(f"color: {COLORS['orange']}; font-size: 9px;")
        fry_layout.addWidget(fry_info)

        fry_sliders = [
            ("fry_intensity", "FRY LEVEL", 0, 30, 0),
            ("jpeg_quality", "JPEG CRUNCH", 1, 100, 100),
            ("noise", "NOISE/GRAIN", 0, 50, 0),
            ("posterize", "POSTERIZE", 2, 32, 32),
            ("color_shift", "COLOR SHIFT", 0, 30, 0),
        ]

        for key, label, min_v, max_v, default in fry_sliders:
            self.create_slider(fry_layout, key, label, min_v, max_v, default)

        # Checkboxes para efeitos
        self.lens_flare_check = QCheckBox("LENS FLARE (eyes)")
        self.lens_flare_check.stateChanged.connect(self.schedule_preview_update)
        fry_layout.addWidget(self.lens_flare_check)

        self.bulge_check = QCheckBox("BULGE EFFECT")
        self.bulge_check.stateChanged.connect(self.schedule_preview_update)
        fry_layout.addWidget(self.bulge_check)

        fry_layout.addStretch()
        self.tabs.addTab(fry_tab, "DEEP FRY")

        # === TAB 4: DISTORT ===
        distort_tab = QWidget()
        distort_layout = QVBoxLayout(distort_tab)
        distort_layout.setSpacing(8)

        distort_info = QLabel("// Glitch & distortion")
        distort_info.setStyleSheet(f"color: {COLORS['danger']}; font-size: 9px;")
        distort_layout.addWidget(distort_info)

        distort_sliders = [
            ("chromatic", "CHROMATIC ABR", 0, 30, 0),
            ("scanlines", "SCANLINES", 0, 20, 0),
            ("pixelate", "PIXELATE", 1, 32, 1),
            ("vhs", "VHS EFFECT", 0, 20, 0),
            ("glitch", "GLITCH", 0, 20, 0),
        ]

        for key, label, min_v, max_v, default in distort_sliders:
            self.create_slider(distort_layout, key, label, min_v, max_v, default)

        distort_layout.addStretch()
        self.tabs.addTab(distort_tab, "DISTORT")

        controls_layout.addWidget(self.tabs)

        # Presets
        presets_group = QGroupBox("[ PRESETS ]")
        presets_layout = QGridLayout(presets_group)
        presets_layout.setSpacing(4)

        presets = [
            ("RESET", self.preset_reset, COLORS['green']),
            ("HDR GLOW", self.preset_hdr_glow, COLORS['green']),
            ("LIGHT FRY", self.preset_light_fry, COLORS['orange']),
            ("CRISPY", self.preset_crispy, COLORS['orange']),
            ("NUCLEAR", self.preset_nuclear, COLORS['danger']),
            ("CURSED", self.preset_cursed, COLORS['danger']),
        ]

        for i, (name, callback, color) in enumerate(presets):
            btn = QPushButton(name)
            btn.setStyleSheet(f"""
                QPushButton {{ border-color: {color}; color: {color}; font-size: 10px; padding: 4px; }}
                QPushButton:hover {{ background-color: {color}; color: {COLORS['bg']}; }}
            """)
            btn.clicked.connect(callback)
            presets_layout.addWidget(btn, i // 3, i % 3)

        controls_layout.addWidget(presets_group)

        # Export
        export_layout = QHBoxLayout()

        self.export_jpg_btn = QPushButton("EXPORT JPG")
        self.export_jpg_btn.clicked.connect(lambda: self.save_image('jpg'))
        self.export_jpg_btn.setEnabled(False)
        export_layout.addWidget(self.export_jpg_btn)

        self.export_png_btn = QPushButton("EXPORT PNG")
        self.export_png_btn.clicked.connect(lambda: self.save_image('png'))
        self.export_png_btn.setEnabled(False)
        export_layout.addWidget(self.export_png_btn)

        controls_layout.addLayout(export_layout)

        # Log
        self.output_label = QLabel("")
        self.output_label.setStyleSheet(f"""
            color: {COLORS['green']}; font-size: 9px; padding: 4px;
            background-color: {COLORS['bg_panel']};
            border: 1px solid {COLORS['green_dark']};
        """)
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_label.setMinimumHeight(24)
        controls_layout.addWidget(self.output_label)

        main_layout.addWidget(controls_widget)

        # === PAINEL DIREITO: PREVIEW ===
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setSpacing(8)

        preview_header = QLabel("┌─────────────────── [ LIVE PREVIEW ] ───────────────────┐")
        preview_header.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px;")
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)

        labels_layout = QHBoxLayout()
        for text in ["INPUT", "OUTPUT"]:
            label = QLabel(f"[ {text} ]")
            label.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            labels_layout.addWidget(label)
        preview_layout.addLayout(labels_layout)

        previews_layout = QHBoxLayout()
        previews_layout.setSpacing(10)
        self.original_preview = ImagePreview("INPUT")
        self.output_preview = ImagePreview("OUTPUT")
        previews_layout.addWidget(self.original_preview)
        previews_layout.addWidget(self.output_preview)
        preview_layout.addLayout(previews_layout)

        preview_footer = QLabel("└────────────────────────────────────────────────────────┘")
        preview_footer.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px;")
        preview_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_footer)

        self.info_bar = QLabel("Ready // Load an image to start")
        self.info_bar.setStyleSheet(f"""
            color: {COLORS['text_dim']}; font-size: 9px; padding: 6px;
            background-color: {COLORS['bg_panel']};
            border: 1px solid {COLORS['green_dark']};
        """)
        self.info_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.info_bar)

        main_layout.addWidget(preview_widget, 1)

    def create_slider(self, parent_layout, key, label_text, min_val, max_val, default):
        container = QHBoxLayout()
        container.setSpacing(6)

        label = QLabel(f"{label_text}:")
        label.setFixedWidth(100)
        label.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px;")
        container.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        container.addWidget(slider)

        value_label = QLabel(f"{default}")
        value_label.setFixedWidth(30)
        value_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px;")
        container.addWidget(value_label)

        def on_change(v):
            value_label.setText(str(v))
            self.schedule_preview_update()

        slider.valueChanged.connect(on_change)
        self.sliders[key] = slider
        parent_layout.addLayout(container)

    def get_val(self, key):
        if key in self.sliders:
            return self.sliders[key].value()
        return 0

    def schedule_preview_update(self):
        self.preview_timer.start(80)

    def log(self, msg, error=False):
        color = COLORS['danger'] if error else COLORS['green']
        self.output_label.setText(f"> {msg}")
        self.output_label.setStyleSheet(f"""
            color: {color}; font-size: 9px; padding: 4px;
            background-color: {COLORS['bg_panel']};
            border: 1px solid {COLORS['green_dark']};
        """)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.heic);;All (*.*)"
        )
        if path:
            self.image_path = path
            self.original_image = Image.open(path).convert("RGB")

            # Preview reduzido
            self.preview_image = self.original_image.copy()
            max_size = 600
            if max(self.preview_image.size) > max_size:
                ratio = max_size / max(self.preview_image.size)
                new_size = (int(self.preview_image.width * ratio),
                           int(self.preview_image.height * ratio))
                self.preview_image = self.preview_image.resize(new_size, Image.Resampling.LANCZOS)

            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 9px;")
            self.export_jpg_btn.setEnabled(True)
            self.export_png_btn.setEnabled(True)

            w, h = self.original_image.size
            self.info_bar.setText(f"Loaded: {w}x{h} // {os.path.basename(path)}")

            self.original_preview.set_image(self.preview_image)
            self.update_preview()
            self.log(f"loaded: {os.path.basename(path)}")

    def update_preview(self):
        if not self.preview_image:
            return
        try:
            processed = self.apply_all_effects(self.preview_image.copy())
            self.output_preview.set_image(processed)
        except Exception as e:
            self.log(f"error: {str(e)[:40]}", error=True)

    def apply_all_effects(self, img):
        """Aplica todos os efeitos na imagem"""

        # === BASIC ===
        # Saturation
        sat = self.get_val("saturation") / 10.0
        if sat != 1.0:
            img = ImageEnhance.Color(img).enhance(sat)

        # Contrast
        con = self.get_val("contrast") / 10.0
        if con != 1.0:
            img = ImageEnhance.Contrast(img).enhance(con)

        # Brightness
        bri = self.get_val("brightness") / 10.0
        if bri != 1.0:
            img = ImageEnhance.Brightness(img).enhance(bri)

        # Sharpness
        shp = self.get_val("sharpness") / 10.0
        if shp != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(shp)

        # Vibrance (saturação seletiva)
        vib = self.get_val("vibrance") / 10.0
        if vib > 1.0:
            img = self.apply_vibrance(img, vib)

        # === HDR ===
        # Highlights
        highlights = self.get_val("highlights") / 10.0
        if highlights != 1.0:
            img = self.adjust_highlights(img, highlights)

        # Shadows
        shadows = self.get_val("shadows") / 10.0
        if shadows != 1.0:
            img = self.adjust_shadows(img, shadows)

        # Bloom
        bloom = self.get_val("bloom")
        if bloom > 0:
            img = self.apply_bloom(img, bloom / 20.0)

        # === DEEP FRY ===
        fry = self.get_val("fry_intensity")
        if fry > 0:
            img = self.deep_fry(img, fry / 10.0)

        # JPEG crunch
        jpeg_q = self.get_val("jpeg_quality")
        if jpeg_q < 100:
            img = self.jpeg_compress(img, jpeg_q)

        # Noise
        noise = self.get_val("noise")
        if noise > 0:
            img = self.add_noise(img, noise / 50.0)

        # Posterize
        posterize = self.get_val("posterize")
        if posterize < 32:
            img = self.posterize(img, posterize)

        # Color shift
        color_shift = self.get_val("color_shift")
        if color_shift > 0:
            img = self.shift_colors(img, color_shift / 30.0)

        # === DISTORT ===
        # Chromatic aberration
        chromatic = self.get_val("chromatic")
        if chromatic > 0:
            img = self.chromatic_aberration(img, chromatic)

        # Scanlines
        scanlines = self.get_val("scanlines")
        if scanlines > 0:
            img = self.add_scanlines(img, scanlines / 20.0)

        # Pixelate
        pixelate = self.get_val("pixelate")
        if pixelate > 1:
            img = self.pixelate(img, pixelate)

        # VHS
        vhs = self.get_val("vhs")
        if vhs > 0:
            img = self.vhs_effect(img, vhs / 20.0)

        # Glitch
        glitch = self.get_val("glitch")
        if glitch > 0:
            img = self.glitch_effect(img, glitch)

        # === EXTRAS ===
        if self.lens_flare_check.isChecked():
            img = self.add_lens_flare(img)

        if self.bulge_check.isChecked():
            img = self.bulge_effect(img)

        return img

    def apply_vibrance(self, img, amount):
        """Aumenta saturação mais em cores menos saturadas"""
        arr = np.array(img, dtype=np.float32)
        gray = np.mean(arr, axis=2, keepdims=True)
        saturation = np.std(arr, axis=2, keepdims=True) / 128.0
        mask = 1.0 - np.clip(saturation, 0, 1)
        arr = gray + (arr - gray) * (1 + mask * (amount - 1))
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def adjust_highlights(self, img, amount):
        """Ajusta áreas claras"""
        arr = np.array(img, dtype=np.float32)
        luminance = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        mask = np.clip((luminance - 128) / 127, 0, 1)[:,:,np.newaxis]
        arr = arr * (1 + mask * (amount - 1))
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def adjust_shadows(self, img, amount):
        """Ajusta áreas escuras"""
        arr = np.array(img, dtype=np.float32)
        luminance = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        mask = np.clip((128 - luminance) / 128, 0, 1)[:,:,np.newaxis]
        arr = arr + mask * (amount - 1) * 50
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def apply_bloom(self, img, amount):
        """Adiciona bloom/glow em áreas claras"""
        blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
        arr = np.array(img, dtype=np.float32)
        blur_arr = np.array(blurred, dtype=np.float32)

        luminance = np.max(blur_arr, axis=2, keepdims=True)
        mask = np.clip((luminance - 180) / 75, 0, 1)

        result = arr + blur_arr * mask * amount
        return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

    def deep_fry(self, img, intensity):
        """Efeito deep fry clássico"""
        # Saturação extrema
        img = ImageEnhance.Color(img).enhance(1 + intensity * 2)
        # Contraste extremo
        img = ImageEnhance.Contrast(img).enhance(1 + intensity * 1.5)
        # Sharpness extremo
        img = ImageEnhance.Sharpness(img).enhance(1 + intensity * 3)

        # Shift para amarelo/laranja
        arr = np.array(img, dtype=np.float32)
        arr[:,:,0] = np.clip(arr[:,:,0] * (1 + intensity * 0.3), 0, 255)  # R
        arr[:,:,1] = np.clip(arr[:,:,1] * (1 + intensity * 0.15), 0, 255)  # G
        arr[:,:,2] = np.clip(arr[:,:,2] * (1 - intensity * 0.2), 0, 255)  # B

        return Image.fromarray(arr.astype(np.uint8))

    def jpeg_compress(self, img, quality):
        """Compressão JPEG para criar artefatos"""
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=int(quality))
        buffer.seek(0)
        return Image.open(buffer).convert("RGB")

    def add_noise(self, img, amount):
        """Adiciona ruído/grain"""
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, amount * 50, arr.shape)
        arr = arr + noise
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def posterize(self, img, levels):
        """Reduz níveis de cor"""
        arr = np.array(img)
        factor = 256 // levels
        arr = (arr // factor) * factor
        return Image.fromarray(arr)

    def shift_colors(self, img, amount):
        """Desloca canais de cor"""
        arr = np.array(img, dtype=np.float32)
        # Rotação no espaço HSV simulado
        arr[:,:,0] = np.clip(arr[:,:,0] + amount * 30, 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2] - amount * 20, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    def chromatic_aberration(self, img, amount):
        """Aberração cromática"""
        arr = np.array(img)
        result = np.zeros_like(arr)
        offset = int(amount)

        # Desloca canais R e B
        result[:, offset:, 0] = arr[:, :-offset, 0] if offset > 0 else arr[:,:,0]
        result[:, :, 1] = arr[:, :, 1]
        result[:, :-offset, 2] = arr[:, offset:, 2] if offset > 0 else arr[:,:,2]

        return Image.fromarray(result)

    def add_scanlines(self, img, intensity):
        """Adiciona scanlines"""
        arr = np.array(img, dtype=np.float32)
        for y in range(0, arr.shape[0], 2):
            arr[y, :, :] *= (1 - intensity * 0.5)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    def pixelate(self, img, size):
        """Pixelização"""
        w, h = img.size
        small = img.resize((w // size, h // size), Image.Resampling.NEAREST)
        return small.resize((w, h), Image.Resampling.NEAREST)

    def vhs_effect(self, img, intensity):
        """Efeito VHS"""
        arr = np.array(img, dtype=np.float32)

        # Blur horizontal
        for i in range(int(intensity * 5)):
            arr = np.roll(arr, 1, axis=1) * 0.1 + arr * 0.9

        # Distorção de cor
        arr[:,:,0] = np.clip(arr[:,:,0] * (1 + intensity * 0.1), 0, 255)
        arr[:,:,2] = np.clip(arr[:,:,2] * (1 - intensity * 0.1), 0, 255)

        return Image.fromarray(arr.astype(np.uint8))

    def glitch_effect(self, img, intensity):
        """Efeito glitch"""
        arr = np.array(img)
        h, w = arr.shape[:2]

        for _ in range(int(intensity)):
            y = np.random.randint(0, h - 10)
            height = np.random.randint(1, 10)
            offset = np.random.randint(-20, 20)

            if 0 <= y + height < h:
                arr[y:y+height, :, :] = np.roll(arr[y:y+height, :, :], offset, axis=1)

        return Image.fromarray(arr)

    def add_lens_flare(self, img):
        """Adiciona lens flare simples"""
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]

        # Encontra pontos brilhantes
        gray = np.mean(arr, axis=2)
        bright_points = np.where(gray > 200)

        if len(bright_points[0]) > 0:
            # Pega alguns pontos aleatórios
            indices = np.random.choice(len(bright_points[0]), min(5, len(bright_points[0])), replace=False)

            for idx in indices:
                cy, cx = bright_points[0][idx], bright_points[1][idx]

                # Cria flare
                y, x = np.ogrid[:h, :w]
                dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                flare = np.exp(-dist / 30) * 100

                arr[:,:,0] = np.clip(arr[:,:,0] + flare, 0, 255)
                arr[:,:,1] = np.clip(arr[:,:,1] + flare * 0.8, 0, 255)

        return Image.fromarray(arr.astype(np.uint8))

    def bulge_effect(self, img):
        """Efeito bulge no centro"""
        arr = np.array(img)
        h, w = arr.shape[:2]
        cx, cy = w // 2, h // 2

        y, x = np.indices((h, w))
        dx = x - cx
        dy = y - cy
        dist = np.sqrt(dx**2 + dy**2)

        radius = min(w, h) // 3
        mask = dist < radius

        factor = 1 + 0.5 * (1 - dist / radius)
        factor = np.where(mask, factor, 1)

        new_x = (cx + dx / factor).astype(int)
        new_y = (cy + dy / factor).astype(int)

        new_x = np.clip(new_x, 0, w - 1)
        new_y = np.clip(new_y, 0, h - 1)

        result = arr[new_y, new_x]
        return Image.fromarray(result)

    def add_hdr_metadata(self, filepath, hdr_gamma):
        """Adiciona metadados HDR"""
        if not self.exiftool_available or hdr_gamma <= 0:
            return False

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False) as f:
                f.write(EXIFTOOL_CONFIG)
                config_path = f.name

            makernotes_path = tempfile.mktemp(suffix='.bin')
            with open(makernotes_path, 'wb') as f:
                f.write(bytes.fromhex(APPLE_MAKERNOTES_HEX))

            subprocess.run([
                'exiftool', '-config', config_path, '-overwrite_original',
                '-if', 'not $makernotes', f'-makernotes<={makernotes_path}', filepath
            ], capture_output=True, timeout=30)

            subprocess.run([
                'exiftool', '-config', config_path, '-overwrite_original',
                f'-Apple:HDRGamma={hdr_gamma}', filepath
            ], capture_output=True, timeout=30)

            os.unlink(config_path)
            if os.path.exists(makernotes_path):
                os.unlink(makernotes_path)

            return True
        except:
            return False

    def save_image(self, format='jpg'):
        if not self.original_image:
            return

        try:
            self.log("processing...")
            QApplication.processEvents()

            processed = self.apply_all_effects(self.original_image.copy())

            ext = '.jpg' if format == 'jpg' else '.png'
            default_name = f"meme_{os.path.splitext(os.path.basename(self.image_path))[0]}{ext}"

            filter_str = "JPEG (*.jpg)" if format == 'jpg' else "PNG (*.png)"
            save_path, _ = QFileDialog.getSaveFileName(self, "Export", default_name, filter_str)

            if save_path:
                if format == 'jpg':
                    processed.save(save_path, 'JPEG', quality=98, subsampling=0)

                    hdr_gamma = self.get_val("hdr_gamma") / 10.0
                    if hdr_gamma > 0:
                        self.add_hdr_metadata(save_path, hdr_gamma)
                        self.log(f"saved with HDRGamma={hdr_gamma}")
                    else:
                        self.log(f"saved: {os.path.basename(save_path)}")
                else:
                    processed.save(save_path, 'PNG')
                    self.log(f"saved: {os.path.basename(save_path)}")

                QMessageBox.information(self, "Exported", f"Saved to:\n{save_path}")

        except Exception as e:
            self.log(f"error: {str(e)}", error=True)

    # === PRESETS ===
    def preset_reset(self):
        for key, slider in self.sliders.items():
            if key == "brightness":
                slider.setValue(10)
            elif key == "jpeg_quality":
                slider.setValue(100)
            elif key == "posterize":
                slider.setValue(32)
            elif key == "pixelate":
                slider.setValue(1)
            else:
                slider.setValue(slider.minimum() if key in ["fry_intensity", "noise", "chromatic", "glitch"] else 10)
        self.lens_flare_check.setChecked(False)
        self.bulge_check.setChecked(False)
        self.log("preset: RESET")

    def preset_hdr_glow(self):
        self.preset_reset()
        self.sliders["saturation"].setValue(18)
        self.sliders["contrast"].setValue(14)
        self.sliders["hdr_gamma"].setValue(25)
        self.sliders["highlights"].setValue(18)
        self.sliders["bloom"].setValue(8)
        self.log("preset: HDR GLOW")

    def preset_light_fry(self):
        self.preset_reset()
        self.sliders["saturation"].setValue(25)
        self.sliders["contrast"].setValue(18)
        self.sliders["sharpness"].setValue(25)
        self.sliders["fry_intensity"].setValue(10)
        self.sliders["jpeg_quality"].setValue(40)
        self.log("preset: LIGHT FRY")

    def preset_crispy(self):
        self.preset_reset()
        self.sliders["saturation"].setValue(35)
        self.sliders["contrast"].setValue(22)
        self.sliders["sharpness"].setValue(40)
        self.sliders["fry_intensity"].setValue(20)
        self.sliders["jpeg_quality"].setValue(15)
        self.sliders["noise"].setValue(15)
        self.log("preset: CRISPY")

    def preset_nuclear(self):
        self.preset_reset()
        self.sliders["saturation"].setValue(45)
        self.sliders["contrast"].setValue(28)
        self.sliders["sharpness"].setValue(50)
        self.sliders["fry_intensity"].setValue(30)
        self.sliders["jpeg_quality"].setValue(5)
        self.sliders["noise"].setValue(25)
        self.sliders["hdr_gamma"].setValue(35)
        self.lens_flare_check.setChecked(True)
        self.log("preset: NUCLEAR")

    def preset_cursed(self):
        self.preset_reset()
        self.sliders["saturation"].setValue(40)
        self.sliders["contrast"].setValue(25)
        self.sliders["fry_intensity"].setValue(25)
        self.sliders["jpeg_quality"].setValue(8)
        self.sliders["noise"].setValue(30)
        self.sliders["posterize"].setValue(8)
        self.sliders["chromatic"].setValue(15)
        self.sliders["glitch"].setValue(10)
        self.bulge_check.setChecked(True)
        self.log("preset: CURSED")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 255, 0))
    app.setPalette(palette)

    window = HDRMemeMaker()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
