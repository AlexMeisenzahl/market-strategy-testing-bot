#!/usr/bin/env python3
"""
Icon Generator for PWA
Generates app icons in all required sizes for Progressive Web App
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

# Icon sizes to generate
ICON_SIZES = [72, 96, 128, 144, 152, 180, 192, 384, 512]

# Splash screen sizes for iPhone models
SPLASH_SIZES = [
    (640, 1136, 'iphone-5'),      # iPhone SE (1st gen), 5s
    (750, 1334, 'iphone-6'),      # iPhone 6, 7, 8, SE (2nd gen)
    (1242, 2208, 'iphone-6plus'), # iPhone 6+, 7+, 8+
    (1125, 2436, 'iphone-x'),     # iPhone X, XS, 11 Pro
    (828, 1792, 'iphone-xr'),     # iPhone XR, 11
    (1170, 2532, 'iphone-12'),    # iPhone 12, 12 Pro, 13, 13 Pro
    (1284, 2778, 'iphone-12max'), # iPhone 12 Pro Max, 13 Pro Max
]

# Colors
BG_COLOR = '#0f172a'
PRIMARY_COLOR = '#3b82f6'
ACCENT_COLOR = '#10b981'
TEXT_COLOR = '#f1f5f9'


def create_icon(size, output_path):
    """Create a simple icon with chart design"""
    # Create image with dark background
    img = Image.new('RGB', (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Add padding
    padding = size // 10
    canvas_size = size - (2 * padding)
    
    # Draw a simple chart/graph icon
    # Background circle
    circle_margin = size // 8
    draw.ellipse(
        [circle_margin, circle_margin, size - circle_margin, size - circle_margin],
        fill=PRIMARY_COLOR,
        outline=None
    )
    
    # Draw chart bars
    bar_width = canvas_size // 8
    bar_spacing = canvas_size // 12
    start_x = padding + bar_spacing
    base_y = size - padding - bar_spacing
    
    bars = [
        (start_x, base_y - canvas_size * 0.3),
        (start_x + bar_width + bar_spacing, base_y - canvas_size * 0.5),
        (start_x + 2 * (bar_width + bar_spacing), base_y - canvas_size * 0.4),
        (start_x + 3 * (bar_width + bar_spacing), base_y - canvas_size * 0.6),
    ]
    
    for x, y in bars:
        # Draw bar with gradient effect (simulate with rectangles)
        draw.rectangle(
            [x, y, x + bar_width, base_y],
            fill=ACCENT_COLOR
        )
        # Highlight on top
        highlight_height = bar_width // 3
        draw.rectangle(
            [x, y, x + bar_width, y + highlight_height],
            fill='#22c55e'
        )
    
    # Draw upward trend line
    line_color = TEXT_COLOR
    line_width = max(2, size // 128)
    trend_points = [
        (padding, size - padding - canvas_size * 0.2),
        (padding + canvas_size * 0.3, size - padding - canvas_size * 0.35),
        (padding + canvas_size * 0.6, size - padding - canvas_size * 0.45),
        (size - padding, size - padding - canvas_size * 0.65),
    ]
    
    for i in range(len(trend_points) - 1):
        draw.line(
            [trend_points[i], trend_points[i + 1]],
            fill=line_color,
            width=line_width
        )
    
    # Save icon
    img.save(output_path, 'PNG', quality=95, optimize=True)
    print(f'✓ Created icon: {output_path.name} ({size}x{size})')


def create_splash_screen(width, height, name, output_path):
    """Create splash screen for iPhone"""
    # Create image with gradient background
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Add gradient effect (simple linear gradient from top to bottom)
    for y in range(height):
        # Interpolate between two colors
        ratio = y / height
        r1, g1, b1 = int(BG_COLOR[1:3], 16), int(BG_COLOR[3:5], 16), int(BG_COLOR[5:7], 16)
        r2, g2, b2 = 30, 41, 59  # Lighter shade
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw centered icon
    icon_size = min(width, height) // 3
    icon_x = (width - icon_size) // 2
    icon_y = (height - icon_size) // 2 - height // 8
    
    # Draw circle background for icon
    draw.ellipse(
        [icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
        fill=PRIMARY_COLOR,
        outline=None
    )
    
    # Draw simple chart icon inside
    padding = icon_size // 5
    bar_width = icon_size // 10
    bar_spacing = icon_size // 15
    start_x = icon_x + padding
    base_y = icon_y + icon_size - padding
    
    for i in range(4):
        height_ratio = [0.3, 0.5, 0.4, 0.6][i]
        bar_x = start_x + i * (bar_width + bar_spacing)
        bar_y = base_y - icon_size * height_ratio
        
        draw.rectangle(
            [bar_x, bar_y, bar_x + bar_width, base_y],
            fill=ACCENT_COLOR
        )
    
    # Add app name text
    text_y = icon_y + icon_size + padding * 2
    
    try:
        # Try to load a font
        font_size = width // 25
        # Use default font if custom font not available
        font = ImageFont.load_default()
    except:
        font = None
    
    app_name = "Market Strategy Bot"
    
    # Get text size using textbbox
    if font:
        bbox = draw.textbbox((0, 0), app_name, font=font)
        text_width = bbox[2] - bbox[0]
    else:
        # Estimate width if font is not available
        text_width = len(app_name) * (width // 50)
    
    text_x = (width - text_width) // 2
    
    draw.text(
        (text_x, text_y),
        app_name,
        fill=TEXT_COLOR,
        font=font
    )
    
    # Save splash screen
    img.save(output_path, 'PNG', quality=95, optimize=True)
    print(f'✓ Created splash screen: {output_path.name} ({width}x{height})')


def main():
    """Generate all icons and splash screens"""
    print("=" * 60)
    print("PWA Icon Generator")
    print("=" * 60)
    
    # Get script directory
    script_dir = Path(__file__).parent.parent
    icons_dir = script_dir / 'dashboard' / 'static' / 'icons'
    splash_dir = script_dir / 'dashboard' / 'static' / 'splash'
    
    # Create directories if they don't exist
    icons_dir.mkdir(parents=True, exist_ok=True)
    splash_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating icons in: {icons_dir}")
    print(f"Generating splash screens in: {splash_dir}\n")
    
    # Generate app icons
    print("Generating app icons...")
    for size in ICON_SIZES:
        output_path = icons_dir / f'icon-{size}x{size}.png'
        try:
            create_icon(size, output_path)
        except Exception as e:
            print(f'✗ Error creating {size}x{size} icon: {e}')
    
    # Generate splash screens
    print("\nGenerating splash screens...")
    for width, height, name in SPLASH_SIZES:
        output_path = splash_dir / f'splash-{name}.png'
        try:
            create_splash_screen(width, height, name, output_path)
        except Exception as e:
            print(f'✗ Error creating {name} splash screen: {e}')
    
    print("\n" + "=" * 60)
    print(f"✓ Generation complete!")
    print(f"  - {len(ICON_SIZES)} app icons")
    print(f"  - {len(SPLASH_SIZES)} splash screens")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGeneration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
