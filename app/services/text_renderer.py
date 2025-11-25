"""Text rendering service using Tkinter for high-quality text overlay."""
import os
import glob
import logging
from typing import Optional, Tuple, List
from io import BytesIO

logger = logging.getLogger(__name__)


class TkinterTextRenderer:
    """Render text using Tkinter with system/bundled fonts."""

    def __init__(self):
        """Initialize the text renderer."""
        # Try to set up virtual display for headless environments
        self._setup_virtual_display()

    def _setup_virtual_display(self):
        """Set up virtual display if running headless."""
        try:
            import subprocess
            import sys

            # Check if we're in a headless environment
            if os.environ.get('DISPLAY') is None:
                logger.info("Headless environment detected, setting up Xvfb...")

                # Start Xvfb on display :99
                subprocess.Popen(
                    ["Xvfb", ":99", "-screen", "0", "1024x768x24"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                os.environ['DISPLAY'] = ':99'
                logger.info("Started Xvfb virtual display")

        except Exception as e:
            logger.warning(f"Could not set up virtual display: {e}")

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _find_font_file(self, font_family: str) -> Optional[str]:
        """Find TTF font file for given font family."""
        font_name = font_family.lower().strip()

        # Common font directories - prioritize /app/app/fonts first (Railway path)
        font_dirs = ["/app/app/fonts", "/app/fonts", "/fonts", "/tmp/fonts", "/usr/share/fonts", "/System/Library/Fonts", "/Windows/Fonts"]

        # Normalize font name: remove spaces, replace with common variations
        font_name_normalized = font_name.replace(" ", "").replace("-", "")

        # Search in /fonts and subdirectories
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                # Recursively find all .ttf files
                for ttf_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                    font_basename = os.path.basename(ttf_file).lower()
                    font_name_only = os.path.splitext(font_basename)[0]

                    # Remove extension and normalize
                    font_name_only_normalized = font_name_only.replace("-", "").replace("_", "")

                    # Check if normalized font name matches
                    if font_name_normalized in font_name_only_normalized or font_name_only_normalized in font_name_normalized:
                        logger.info(f"✅ Font matched: '{font_family}' -> '{ttf_file}'")
                        return ttf_file

                    # Check alternative names with better matching
                    name_map = {
                        "arial": ["arial", "helvetica"],
                        "times new roman": ["times", "timesnewroman", "timesnewromanpsmt"],
                        "times": ["times", "timesnewroman", "timesnewromanpsmt"],
                        "open sans": ["opensans", "open-sans"],
                        "roboto": ["roboto"],
                        "helvetica": ["helvetica", "arial"],
                        "impact": ["impact"],
                        "georgia": ["georgia"],
                        "verdana": ["verdana"],
                        "trebuchet": ["trebuchet", "trebuchetsms"],
                        "dejavusans": ["dejavusans", "dejavusansans"],
                        "dejavusans bold": ["dejavusans-bold", "dejavusansbold"],
                        "dejavuserif": ["dejavuserif", "dejavuserifcondensed"],
                        "dejavuserif bold": ["dejavuserif-bold", "dejavuserifbold"],
                        "liberationsans": ["liberationsans", "liberationsans-regular"],
                        "liberationsans bold": ["liberationsans-bold", "liberationsansbold"],
                        "liberationserif": ["liberationserif", "liberationserif-regular"],
                        "liberationserif bold": ["liberationserif-bold", "liberationserifbold"],
                    }

                    if font_name in name_map:
                        for alt_name in name_map[font_name]:
                            alt_normalized = alt_name.replace("-", "").replace("_", "")
                            if alt_normalized in font_name_only_normalized:
                                logger.info(f"✅ Font matched via map: '{font_family}' -> '{ttf_file}'")
                                return ttf_file

        logger.warning(f"❌ Font not found: '{font_family}' (normalized: '{font_name_normalized}')")
        return None

    def render_text_with_pil(
        self,
        text: str,
        font_family: str,
        font_size: int,
        color: str,
        stroke_color: Optional[str] = None,
        stroke_width: int = 0,
        opacity: float = 1.0,
        position: Tuple[int, int] = (0, 0)
    ) -> bytes:
        """
        Alternative: Render text using PIL with better font loading.

        This method uses PIL but with improved font handling.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            from io import BytesIO

            logger.info(f"Rendering text with PIL: '{text}' font={font_family} size={font_size}")

            # Find font file
            font_path = self._find_font_file(font_family)
            if font_path:
                logger.info(f"Found font: {font_path}")
                font = ImageFont.truetype(font_path, font_size)
            else:
                logger.warning(f"Font not found: {font_family}")
                font = ImageFont.load_default()

            # Calculate text size and position
            dummy_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(dummy_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate padding needed for stroke (extra space around text)
            stroke_padding = stroke_width * 2 if stroke_width > 0 else 0

            # Add extra bottom padding for descenders (g, p, q, y, etc.)
            # Increase to 30% of font size for better coverage
            descender_padding = int(font_size * 0.3)

            # Account for font left-side bearing
            left_bearing_offset = bbox[0]
            right_bearing_offset = text_width - (bbox[2] - bbox[0])

            logger.info(f"📏 Font metrics - bbox: {bbox}, left_bearing: {left_bearing_offset}, width: {text_width}, right_bearing: {right_bearing_offset}")

            # Create image - big enough for text + padding
            img_width = text_width + stroke_padding + left_bearing_offset
            img_height = text_height + stroke_padding + descender_padding

            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Convert colors
            color_rgb = self._hex_to_rgb(color)
            stroke_rgb = self._hex_to_rgb(stroke_color) if stroke_color else (0, 0, 0)

            # Calculate text position within the image
            # Draw text starting at left_bearing_offset (no negative coords!)
            text_x = stroke_padding + left_bearing_offset
            text_y = stroke_padding

            logger.info(f"📍 Text position in image: ({text_x}, {text_y})")
            logger.info(f"📐 Text image size: {img_width}x{img_height}")
            logger.info(f"📏 Left bearing (ink offset): {left_bearing_offset}px")

            # Draw stroke if specified (around the text)
            if stroke_width > 0 and stroke_color:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx*dx + dy*dy <= stroke_width * stroke_width:
                            draw.text(
                                (text_x + dx, text_y + dy),
                                text,
                                font=font,
                                fill=stroke_rgb
                            )

            # Draw main text at calculated position
            draw.text(
                (text_x, text_y),
                text,
                font=font,
                fill=color_rgb
            )

            # Apply opacity
            if opacity < 1.0:
                alpha = img.split()[3]
                alpha = Image.new('L', img.size, int(255 * opacity))
                img.putalpha(alpha)

            # Save to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()

            logger.info(f"Text rendered successfully: {len(img_bytes)} bytes")
            # Return both the image bytes AND the left bearing offset for precise positioning
            return img_bytes, left_bearing_offset

        except Exception as e:
            logger.error(f"PIL text rendering failed: {e}", exc_info=True)
            raise
