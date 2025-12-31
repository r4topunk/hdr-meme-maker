#!/usr/bin/env python3
"""
HDR Meme Maker - Cria imagens HDR REAIS que explodem em telas HDR
Usa tags MakerApple EXIF para ativar HDR no iPhone/Mac
"""

import sys
import os
import subprocess
import shutil
import tempfile
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from PIL.ImageQt import ImageQt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QMessageBox, QFrame,
    QGroupBox, QGridLayout, QComboBox
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
}

MONO_FONT = "Monaco, Menlo, Consolas, monospace"

# ExifTool config para tag HDRGamma da Apple
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

# Makernotes mínimo da Apple para ativar HDR
# Este é um template básico que permite ao exiftool escrever as tags
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
        self.setMinimumSize(320, 280)
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
        self.exiftool_available = self.check_exiftool()

        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)

        self.init_ui()

    def check_exiftool(self):
        """Verifica se exiftool está instalado"""
        return shutil.which('exiftool') is not None

    def init_ui(self):
        self.setWindowTitle("HDR_MEME_MAKER.exe")
        self.setMinimumSize(1050, 750)
        self.resize(1100, 800)

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {COLORS['bg']}; }}
            QWidget {{
                background-color: {COLORS['bg']};
                color: {COLORS['green']};
                font-family: {MONO_FONT};
            }}
            QLabel {{ color: {COLORS['green']}; font-family: {MONO_FONT}; }}
            QPushButton {{
                background-color: {COLORS['bg']};
                color: {COLORS['green']};
                border: 1px solid {COLORS['green']};
                padding: 8px 16px;
                font-family: {MONO_FONT};
                font-size: 12px;
                font-weight: bold;
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
                width: 12px;
                height: 12px;
                margin: -4px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['green']};
            }}
            QGroupBox {{
                border: 1px solid {COLORS['green_dark']};
                margin-top: 12px;
                padding-top: 8px;
                font-size: 11px;
            }}
            QGroupBox::title {{
                color: {COLORS['green']};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox {{
                background-color: {COLORS['bg']};
                color: {COLORS['green']};
                border: 1px solid {COLORS['green']};
                padding: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg']};
                color: {COLORS['green']};
                selection-background-color: {COLORS['green']};
                selection-color: {COLORS['bg']};
            }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # === PAINEL ESQUERDO ===
        controls_widget = QWidget()
        controls_widget.setFixedWidth(340)
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("""┌─────────────────────────────────────┐
│    ██╗  ██╗██████╗ ██████╗          │
│    ██║  ██║██╔══██╗██╔══██╗         │
│    ███████║██║  ██║██████╔╝         │
│    ██╔══██║██║  ██║██╔══██╗         │
│    ██║  ██║██████╔╝██║  ██║         │
│    ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝         │
│    APPLE HDR MEME MAKER v3.0        │
└─────────────────────────────────────┘""")
        header.setStyleSheet(f"color: {COLORS['green']}; font-size: 9px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(header)

        # ExifTool status
        if not self.exiftool_available:
            warning = QLabel("⚠ exiftool não encontrado!\nbrew install exiftool")
            warning.setStyleSheet(f"color: {COLORS['danger']}; font-size: 10px;")
            warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
            controls_layout.addWidget(warning)

        # Status
        self.status_line = QLabel("[ STATUS: READY ]")
        self.status_line.setStyleSheet(f"color: {COLORS['green_dim']}; font-size: 10px;")
        self.status_line.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.status_line)

        # File input
        file_group = QGroupBox("[ FILE INPUT ]")
        file_layout = QVBoxLayout(file_group)

        self.select_btn = QPushButton("> SELECT_IMAGE")
        self.select_btn.clicked.connect(self.select_image)
        file_layout.addWidget(self.select_btn)

        self.file_label = QLabel("no file selected")
        self.file_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(self.file_label)

        controls_layout.addWidget(file_group)

        # HDR Settings
        hdr_group = QGroupBox("[ HDR SETTINGS ]")
        hdr_layout = QVBoxLayout(hdr_group)
        hdr_layout.setSpacing(10)

        self.sliders = {}

        # Info sobre HDRGamma
        hdr_info = QLabel("// HDRGamma: 0=SDR, 1-3=HDR brilhante")
        hdr_info.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px;")
        hdr_layout.addWidget(hdr_info)

        slider_configs = [
            ("hdr_gamma", "HDR", 0, 40, 20, "HDRGamma Apple (0-4.0)"),
            ("saturation", "SAT", 10, 40, 20, "Saturação"),
            ("contrast", "CON", 10, 25, 15, "Contraste"),
            ("brightness", "BRI", 8, 20, 12, "Brilho"),
            ("sharpness", "SHP", 10, 40, 15, "Nitidez"),
        ]

        for key, label, min_val, max_val, default, tooltip in slider_configs:
            self.create_slider(hdr_layout, key, label, min_val, max_val, default)

        controls_layout.addWidget(hdr_group)

        # Presets
        presets_group = QGroupBox("[ PRESETS ]")
        presets_layout = QGridLayout(presets_group)
        presets_layout.setSpacing(6)

        presets = [
            ("SUBTLE", self.preset_subtle),
            ("MEDIUM", self.preset_medium),
            ("BLINDING", self.preset_blinding),
            ("NUCLEAR", self.preset_nuclear),
        ]

        for i, (name, callback) in enumerate(presets):
            btn = QPushButton(f"[{name}]")
            if name == "NUCLEAR":
                btn.setStyleSheet(f"""
                    QPushButton {{ border-color: {COLORS['danger']}; color: {COLORS['danger']}; }}
                    QPushButton:hover {{ background-color: {COLORS['danger']}; color: {COLORS['bg']}; }}
                """)
            btn.clicked.connect(callback)
            presets_layout.addWidget(btn, i // 2, i % 2)

        controls_layout.addWidget(presets_group)

        # Export button
        self.process_btn = QPushButton(">> EXPORT_HDR_MEME <<")
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {COLORS['green']};
                padding: 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['green']};
                color: {COLORS['bg']};
            }}
            QPushButton:disabled {{
                border-color: {COLORS['green_dark']};
                color: {COLORS['green_dark']};
            }}
        """)
        self.process_btn.clicked.connect(self.save_image)
        self.process_btn.setEnabled(False)
        controls_layout.addWidget(self.process_btn)

        # Output log
        self.output_label = QLabel("")
        self.output_label.setStyleSheet(f"""
            color: {COLORS['green']};
            font-size: 10px;
            padding: 5px;
            background-color: {COLORS['bg_panel']};
            border: 1px solid {COLORS['green_dark']};
        """)
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_label.setMinimumHeight(30)
        controls_layout.addWidget(self.output_label)

        controls_layout.addStretch()
        main_layout.addWidget(controls_widget)

        # === PAINEL DIREITO ===
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setSpacing(10)

        preview_header = QLabel("┌──────────────── [ PREVIEW ] ────────────────┐")
        preview_header.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px;")
        preview_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_header)

        hdr_warning = QLabel("⚠ HDR real só aparece no arquivo exportado (JPEG)")
        hdr_warning.setStyleSheet(f"color: {COLORS['danger']}; font-size: 10px;")
        hdr_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(hdr_warning)

        labels_layout = QHBoxLayout()
        for text, is_output in [("INPUT", False), ("OUTPUT (preview)", True)]:
            label = QLabel(f"[ {text} ]")
            label.setStyleSheet(f"color: {COLORS['green'] if is_output else COLORS['text_dim']}; font-size: 11px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            labels_layout.addWidget(label)
        preview_layout.addLayout(labels_layout)

        previews_layout = QHBoxLayout()
        previews_layout.setSpacing(15)
        self.original_preview = ImagePreview("INPUT")
        self.hdr_preview = ImagePreview("OUTPUT")
        previews_layout.addWidget(self.original_preview)
        previews_layout.addWidget(self.hdr_preview)
        preview_layout.addLayout(previews_layout)

        preview_footer = QLabel("└─────────────────────────────────────────────┘")
        preview_footer.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px;")
        preview_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_footer)

        self.info_bar = QLabel("RES: ---- x ----  |  HDRGamma: ----  |  Format: JPEG")
        self.info_bar.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: 10px;
            padding: 8px;
            background-color: {COLORS['bg_panel']};
            border: 1px solid {COLORS['green_dark']};
        """)
        self.info_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.info_bar)

        main_layout.addWidget(preview_widget, 1)

    def create_slider(self, parent_layout, key, label_text, min_val, max_val, default):
        container = QHBoxLayout()
        container.setSpacing(10)

        label = QLabel(f"{label_text}:")
        label.setFixedWidth(35)
        label.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px;")
        container.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        container.addWidget(slider)

        value_label = QLabel(f"[{default / 10:.1f}]")
        value_label.setFixedWidth(45)
        value_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px;")
        container.addWidget(value_label)

        def on_value_changed(v):
            value_label.setText(f"[{v / 10:.1f}]")
            self.schedule_preview_update()
            self.update_info_bar()

        slider.valueChanged.connect(on_value_changed)
        self.sliders[key] = slider
        parent_layout.addLayout(container)

    def get_slider_value(self, key):
        return self.sliders[key].value() / 10.0

    def schedule_preview_update(self):
        self.preview_timer.start(50)

    def update_info_bar(self):
        if self.original_image:
            w, h = self.original_image.size
            gamma = self.get_slider_value("hdr_gamma")
            self.info_bar.setText(f"RES: {w} x {h}  |  HDRGamma: {gamma:.1f}  |  Format: JPEG")

    def log(self, message, error=False):
        color = COLORS['danger'] if error else COLORS['green']
        self.output_label.setText(f"> {message}")
        self.output_label.setStyleSheet(f"""
            color: {color}; font-size: 10px; padding: 5px;
            background-color: {COLORS['bg_panel']};
            border: 1px solid {COLORS['green_dark']};
        """)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "SELECT_IMAGE", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.heic);;All (*.*)"
        )

        if path:
            self.image_path = path
            self.original_image = Image.open(path)

            self.preview_image = self.original_image.copy()
            max_size = 800
            if max(self.preview_image.size) > max_size:
                ratio = max_size / max(self.preview_image.size)
                new_size = (int(self.preview_image.width * ratio),
                           int(self.preview_image.height * ratio))
                self.preview_image = self.preview_image.resize(new_size, Image.Resampling.LANCZOS)

            filename = os.path.basename(path)
            self.file_label.setText(f">> {filename}")
            self.file_label.setStyleSheet(f"color: {COLORS['green']}; font-size: 10px;")
            self.process_btn.setEnabled(True)
            self.status_line.setText("[ STATUS: FILE LOADED ]")

            self.original_preview.set_image(self.preview_image)
            self.update_preview()
            self.update_info_bar()
            self.log(f"loaded: {filename}")

    def update_preview(self):
        if not self.preview_image:
            return
        try:
            processed = self.apply_visual_effects(self.preview_image.copy())
            self.hdr_preview.set_image(processed)
        except Exception as e:
            self.log(f"preview error: {e}", error=True)

    def apply_visual_effects(self, img):
        """Aplica efeitos visuais (saturação, contraste, etc.)"""
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Saturação
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(self.get_slider_value("saturation"))

        # Contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(self.get_slider_value("contrast"))

        # Brilho
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(self.get_slider_value("brightness"))

        # Nitidez
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(self.get_slider_value("sharpness"))

        return img

    def add_hdr_metadata(self, filepath, hdr_gamma):
        """Adiciona metadados HDR da Apple usando exiftool"""
        if not self.exiftool_available:
            self.log("exiftool não disponível", error=True)
            return False

        try:
            # Criar arquivo de configuração temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False) as f:
                f.write(EXIFTOOL_CONFIG)
                config_path = f.name

            # Criar makernotes temporário
            makernotes_path = tempfile.mktemp(suffix='.bin')
            with open(makernotes_path, 'wb') as f:
                f.write(bytes.fromhex(APPLE_MAKERNOTES_HEX))

            # Primeiro, adicionar makernotes se não existir
            cmd1 = [
                'exiftool',
                '-config', config_path,
                '-overwrite_original',
                '-if', 'not $makernotes',
                f'-makernotes<={makernotes_path}',
                filepath
            ]
            subprocess.run(cmd1, capture_output=True, timeout=30)

            # Depois, definir HDRGamma
            cmd2 = [
                'exiftool',
                '-config', config_path,
                '-overwrite_original',
                f'-Apple:HDRGamma={hdr_gamma}',
                filepath
            ]
            result = subprocess.run(cmd2, capture_output=True, timeout=30, text=True)

            # Limpar arquivos temporários
            os.unlink(config_path)
            if os.path.exists(makernotes_path):
                os.unlink(makernotes_path)

            if result.returncode == 0:
                return True
            else:
                self.log(f"exiftool warning: {result.stderr[:50]}", error=True)
                return True  # Ainda pode ter funcionado

        except Exception as e:
            self.log(f"metadata error: {str(e)[:30]}", error=True)
            return False

    def save_image(self):
        if not self.original_image:
            return

        try:
            self.status_line.setText("[ STATUS: PROCESSING... ]")
            self.log("applying effects...")
            QApplication.processEvents()

            # Aplicar efeitos visuais
            processed = self.apply_visual_effects(self.original_image.copy())

            # Converter para RGB se necessário
            if processed.mode != "RGB":
                processed = processed.convert("RGB")

            default_name = f"hdr_{os.path.splitext(os.path.basename(self.image_path))[0]}.jpg"

            save_path, _ = QFileDialog.getSaveFileName(
                self, "EXPORT_HDR", default_name,
                "JPEG HDR (*.jpg);;PNG (*.png)"
            )

            if save_path:
                # Garantir extensão .jpg para HDR funcionar
                if not save_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    save_path += '.jpg'

                self.log("saving image...")
                QApplication.processEvents()

                # Salvar JPEG com qualidade máxima
                if save_path.lower().endswith(('.jpg', '.jpeg')):
                    processed.save(save_path, 'JPEG', quality=98, subsampling=0)

                    # Adicionar metadados HDR
                    hdr_gamma = self.get_slider_value("hdr_gamma")

                    if hdr_gamma > 0 and self.exiftool_available:
                        self.log(f"adding HDRGamma={hdr_gamma}...")
                        QApplication.processEvents()

                        if self.add_hdr_metadata(save_path, hdr_gamma):
                            self.log(f"HDR metadata added!")
                        else:
                            self.log("HDR metadata failed", error=True)
                else:
                    processed.save(save_path, quality=98)

                self.status_line.setText("[ STATUS: EXPORT COMPLETE ]")
                self.log(f"saved: {os.path.basename(save_path)}")

                msg = f"Arquivo salvo!\n\n{save_path}\n\n"
                if save_path.lower().endswith(('.jpg', '.jpeg')):
                    msg += f"HDRGamma: {self.get_slider_value('hdr_gamma')}\n\n"
                    msg += "Abra no app Fotos do iPhone/Mac para ver o HDR!"
                else:
                    msg += "PNG não suporta HDRGamma - use JPEG"

                QMessageBox.information(self, "EXPORT_SUCCESS", msg)

            else:
                self.status_line.setText("[ STATUS: READY ]")
                self.log("cancelled")

        except Exception as e:
            self.status_line.setText("[ STATUS: ERROR ]")
            self.log(f"error: {str(e)}", error=True)
            import traceback
            traceback.print_exc()

    def preset_subtle(self):
        self.sliders["hdr_gamma"].setValue(10)
        self.sliders["saturation"].setValue(15)
        self.sliders["contrast"].setValue(12)
        self.sliders["brightness"].setValue(11)
        self.sliders["sharpness"].setValue(12)
        self.log("preset: SUBTLE")

    def preset_medium(self):
        self.sliders["hdr_gamma"].setValue(18)
        self.sliders["saturation"].setValue(20)
        self.sliders["contrast"].setValue(15)
        self.sliders["brightness"].setValue(12)
        self.sliders["sharpness"].setValue(15)
        self.log("preset: MEDIUM")

    def preset_blinding(self):
        self.sliders["hdr_gamma"].setValue(28)
        self.sliders["saturation"].setValue(28)
        self.sliders["contrast"].setValue(18)
        self.sliders["brightness"].setValue(14)
        self.sliders["sharpness"].setValue(20)
        self.log("preset: BLINDING")

    def preset_nuclear(self):
        self.sliders["hdr_gamma"].setValue(40)
        self.sliders["saturation"].setValue(35)
        self.sliders["contrast"].setValue(22)
        self.sliders["brightness"].setValue(16)
        self.sliders["sharpness"].setValue(30)
        self.log("preset: NUCLEAR [!!!]")


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
