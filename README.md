# HDR Meme Maker + Deep Fryer

A Python GUI application for macOS that creates **real HDR images** and **deep fried memes** - the ultimate meme experimentation studio.

Create HDR images that appear extremely bright on HDR displays (iPhone, Mac with XDR/HDR screens), or make deep fried memes with extreme saturation, JPEG artifacts, and glitch effects.

```
┌────────────────────────────────────────────┐
│  ██╗  ██╗██████╗ ██████╗   MEME STUDIO    │
│  ██║  ██║██╔══██╗██╔══██╗  ─────────────  │
│  ███████║██║  ██║██████╔╝  HDR + DEEPFRY  │
│  ██║  ██║██████╔╝██║  ██║  v4.0 ARTIST    │
└────────────────────────────────────────────┘
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

1. **Load Image** - Choose any image (PNG, JPEG, HEIC, etc.)
2. **Adjust Settings** across 4 tabs:

### BASIC Tab
- **Saturation** - Color intensity
- **Contrast** - Light/dark difference
- **Brightness** - Overall luminance
- **Sharpness** - Edge enhancement
- **Vibrance** - Selective saturation (boosts dull colors more)

### HDR Tab
- **HDR Gamma** (0-4.0) - Apple HDRGamma EXIF tag (the magic that makes it glow)
- **Highlights** - Boost bright areas
- **Shadows** - Lift dark areas
- **Bloom** - Glow effect on bright areas

### DEEP FRY Tab
- **Fry Level** - Classic deep fry effect (extreme saturation + contrast + orange tint)
- **JPEG Crunch** - Add compression artifacts
- **Noise/Grain** - Add random noise
- **Posterize** - Reduce color levels
- **Color Shift** - Shift color channels
- **Lens Flare** - Add flares at bright points
- **Bulge Effect** - Distort center of image

### DISTORT Tab
- **Chromatic Aberration** - Color channel separation
- **Scanlines** - CRT-style horizontal lines
- **Pixelate** - Reduce resolution
- **VHS Effect** - Retro video look
- **Glitch** - Random horizontal displacement

3. **Use Presets** (optional):
   - `RESET` - Default values
   - `HDR GLOW` - Clean HDR effect
   - `LIGHT FRY` - Subtle deep fry
   - `CRISPY` - Medium deep fry
   - `NUCLEAR` - Maximum HDR + fry
   - `CURSED` - Full chaos mode
4. **Export as JPEG** (for HDR) or **PNG** (for other effects)
5. **View in Photos app** - Open the exported JPEG in macOS/iOS Photos app to see the HDR effect

> **Important**: The HDR effect only appears in the **Photos app**. Preview, Finder, and most other apps will show the image as SDR. Deep fry effects work everywhere.

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

### Deep Fried Memes

Deep fried memes are a style of meme featuring intentionally degraded images with:

- **Extreme saturation and contrast** - Colors pushed to maximum
- **JPEG compression artifacts** - Low quality compression creates blocky patterns
- **Color shifting** - Typically toward orange/yellow tones
- **Noise and grain** - Random pixel noise
- **Lens flares** - Often over eyes
- **Bulge/distortion** - Warped image areas
- **Glitch effects** - Horizontal line displacement

### Limitations

- HDR effect only visible in Apple Photos app
- May have reduced effectiveness on iOS 17+ / macOS Sonoma due to Apple's HDR processing changes
- Requires ExifTool for HDR metadata injection (deep fry works without it)

### References

- [AppleJPEGGainMap](https://github.com/grapeot/AppleJPEGGainMap) - Reference implementation
- [Decoding MakerApple Metadata](https://juniperphoton.substack.com/p/decoding-some-hidden-magic-of-makerapple)
- [Edit HDR Gamma](https://github.com/anteo/edit-hdr-gamma) - Automator approach
- [Apple Developer - HDR Support](https://developer.apple.com/documentation/appkit/applying-apple-hdr-effect-to-your-photos)
- [Know Your Meme - Deep Fried Memes](https://knowyourmeme.com/memes/deep-fried-memes)

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
- [ ] Face detection for automatic lens flare placement
- [ ] Custom filter presets (save/load)
- [ ] More glitch effects (datamosh, pixel sort)
- [ ] Audio-reactive effects for video export
