# PWA Icons

This directory should contain the following icon sizes for the Progressive Web App:

- `icon-72x72.png` (72x72 pixels)
- `icon-96x96.png` (96x96 pixels)
- `icon-128x128.png` (128x128 pixels)
- `icon-144x144.png` (144x144 pixels)
- `icon-152x152.png` (152x152 pixels)
- `icon-192x192.png` (192x192 pixels)
- `icon-384x384.png` (384x384 pixels)
- `icon-512x512.png` (512x512 pixels)

## Generating Icons

You can generate these icons from a source image using:

1. **Online Tools**:
   - [PWA Asset Generator](https://www.pwabuilder.com/imageGenerator)
   - [RealFaviconGenerator](https://realfavicongenerator.net/)

2. **Command Line**:
   ```bash
   # Install pwa-asset-generator
   npm install -g pwa-asset-generator
   
   # Generate icons from source image
   pwa-asset-generator source-logo.png ./icons
   ```

3. **Manually**:
   - Use any image editor (GIMP, Photoshop, etc.)
   - Resize to each dimension listed above
   - Export as PNG with transparency

## Recommended Source Image

- **Format**: PNG with transparency
- **Size**: 1024x1024 pixels or larger
- **Content**: Simple, recognizable logo/icon
- **Style**: Works well at small sizes
- **Colors**: High contrast for visibility

## Note

The manifest.json already references these icon files. Once generated, place them in this directory and they will be automatically used by the PWA.
