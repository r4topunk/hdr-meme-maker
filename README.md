# HDR Meme Maker

A Python GUI application for macOS that creates **real HDR images** that appear extremely bright on HDR displays (iPhone, Mac with XDR/HDR screens).

This tool replicates the viral "HDR meme" effect seen on Twitter/Reddit where images appear to "glow" brighter than the rest of the screen.

```
┌─────────────────────────────────────┐
│    ██╗  ██╗██████╗ ██████╗          │
│    ██║  ██║██╔══██╗██╔══██╗         │
│    ███████║██║  ██║██████╔╝         │
│    ██╔══██║██║  ██║██╔══██╗         │
│    ██║  ██║██████╔╝██║  ██║         │
│    ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝         │
│    APPLE HDR MEME MAKER v3.0        │
└─────────────────────────────────────┘
```

## How It Works

The app uses Apple's proprietary **MakerApple EXIF tags** to enable HDR rendering:

- **Tag 0x0021 (HDRGamma)**: Controls global brightness boost above SDR
  - `0` = Standard SDR image
  - `1.0-2.0` = Moderate HDR glow
  - `2.0-4.0` = Intense HDR effect

When viewed in the **Photos app** on iPhone/Mac, these tags tell the display to render certain pixels brighter than the standard dynamic range allows.

## Requirements

- **macOS** (tested on Sonoma)
- **Python 3.10+**
- **ExifTool** (for HDR metadata injection)

## Installation

### 1. Install ExifTool

```bash
brew install exiftool
```

### 2. Clone and Setup

```bash
git clone https://github.com/YOUR_USERNAME/hdr-meme-maker.git
cd hdr-meme-maker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run

```bash
python3 hdr_meme_maker.py
```

Or use the convenience script:

```bash
./run.sh
```

## Usage

1. **Select Image** - Choose any image (PNG, JPEG, etc.)
2. **Adjust Settings**:
   - **HDR**: HDRGamma value (0-4.0) - the magic that makes it glow
   - **SAT**: Saturation boost
   - **CON**: Contrast
   - **BRI**: Brightness
   - **SHP**: Sharpness
3. **Use Presets** (optional):
   - `SUBTLE` - Light HDR effect
   - `MEDIUM` - Balanced HDR
   - `BLINDING` - Strong HDR
   - `NUCLEAR` - Maximum eye-burning effect
4. **Export as JPEG** - HDR only works with JPEG format
5. **View in Photos app** - Open the exported image in macOS/iOS Photos app to see the HDR effect

> **Important**: The HDR effect only appears in the **Photos app**. Preview, Finder, and most other apps will show the image as SDR.

## Screenshots

The app features a terminal/hacker aesthetic with green-on-black theme:

- Real-time preview (SDR approximation)
- Side-by-side comparison
- Status logging

## Technical Details

### Apple HDR Implementation

Apple devices use a proprietary HDR system based on:

1. **MakerApple EXIF Tags**: Hidden metadata in the `makernotes` section
2. **HDRGamma (0x0021)**: Float value controlling brightness extension
3. **Gain Map (0x0030)**: Optional grayscale map for local HDR adjustments

This tool injects the HDRGamma tag using ExifTool with a custom configuration.

### Limitations

- HDR effect only visible in Apple Photos app
- May have reduced effectiveness on iOS 17+ / macOS Sonoma due to Apple's HDR processing changes
- Requires ExifTool for metadata injection

### References

- [AppleJPEGGainMap](https://github.com/grapeot/AppleJPEGGainMap) - Reference implementation
- [Decoding MakerApple Metadata](https://juniperphoton.substack.com/p/decoding-some-hidden-magic-of-makerapple)
- [Edit HDR Gamma](https://github.com/anteo/edit-hdr-gamma) - Automator approach
- [Apple Developer - HDR Support](https://developer.apple.com/documentation/appkit/applying-apple-hdr-effect-to-your-photos)

## Dependencies

- `PyQt6` - GUI framework
- `Pillow` - Image processing
- `numpy` - Array operations
- `opencv-python` - Image I/O
- `exiftool` (system) - EXIF metadata manipulation

## License

MIT License

## Contributing

Pull requests welcome! Some ideas for improvements:

- [ ] Support for real Gain Map HDR (requires iPhone reference image)
- [ ] HEIC output format support
- [ ] Batch processing
- [ ] Preview HDR effect using EDR APIs
