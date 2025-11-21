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
                logger.info("🖥️ Headless environment detected, setting up Xvfb...")

                # Check if Xvfb is already running
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "Xvfb"],
                        capture_output=True,
                        text=True
                    )

                    if result.returncode != 0:
                        # Start Xvfb on display :99
                        subprocess.Popen(
                            ["Xvfb", ":99", "-screen", "0", "1024x768x24"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        logger.info("✅ Started Xvfb virtual display")
                        os.environ['DISPLAY'] = ':99'
                    else:
                        os.environ['DISPLAY'] = ':99'
                        logger.info("✅ Using existing Xvfb display")

        except Exception as e:
            logger.warning(f"⚠️ Could not set up virtual display: {e}")

    def render_text_layer(
        self,
        text: str,
        font_family: str,
        font_size: int,
        color: str,
        stroke_color: Optional[str] = None,
        stroke_width: int = 0,
        opacity: float = 1.0,
        position: Tuple[int, int] = (0, 0),
        max_width: Optional[int] = None
    ) -> bytes:
        """
        Render text as PNG image using Tkinter.

        Args:
            text: Text to render
            font_family: Font family name
            font_size: Font size in pixels
            color: Text color in hex (e.g., "#FFFFFF")
            stroke_color: Stroke color in hex
            stroke_width: Stroke width in pixels
            opacity: Text opacity (0.0 to 1.0)
            position: (x, y) position
            max_width: Maximum text width before wrapping

        Returns:
            PNG image bytes
        """
        try:
            import tkinter as tk
            from tkinter import font as tkfont
            from PIL import Image
            import textwrap

            logger.info(f"🎨 Rendering text with Tkinter: '{text}' font={font_family} size={font_size}")

            # Create root window (hidden)
            root = tk.Tk()
            root.withdraw()

            # Convert hex color to RGB
            color_rgb = self._hex_to_rgb(color)
            stroke_rgb = self._hex_to_rgb(stroke_color) if stroke_color else None

            # Create a canvas with some padding
            padding = stroke_width * 2 + 10 if stroke_width > 0 else 10
            canvas_width = max_width + padding * 2 if max_width else 1000
            canvas_height = 500

            canvas = tk.Canvas(
                root,
                width=canvas_width,
                height=canvas_height,
                bg='transparent',
                highlightthickness=0
            )

            # Load font
            font_path = self._find_font_file(font_family)
            if font_path:
                logger.info(f"✅ Loaded font: {font_path}")
                custom_font = tkfont.Font(
                    family=font_family,
                    size=font_size,
                    weight='normal'
                )
            else:
                logger.warning(f"⚠️ Font not found: {font_family}, using default")
                custom_font = tkfont.Font(
                    family='Arial',
                    size=font_size,
                    weight='normal'
                )

            # Wrap text if max_width specified
            if max_width and text:
                # Create a temp label to measure wrapped text
                temp_label = tk.Label(root, text="", font=custom_font)
                temp_label.update()

                # Calculate character wrap width
                char_width = custom_font.measure('A')
                wrap_chars = max(1, max_width // char_width) if char_width > 0 else 50
                wrapped_text = textwrap.fill(text, width=wrap_chars)

                lines = wrapped_text.split('\n')
            else:
                lines = text.split('\n')

            # Calculate total text height
            line_height = custom_font.metrics('linespace')
            total_height = len(lines) * line_height + padding * 2

            # Resize canvas to fit text
            canvas.config(height=total_height)

            # Draw text line by line
            y = padding + line_height
            for line in lines:
                x = padding

                # Draw stroke if specified
                if stroke_width > 0 and stroke_rgb:
                    for dx in range(-stroke_width, stroke_width + 1):
                        for dy in range(-stroke_width, stroke_width + 1):
                            if dx*dx + dy*dy <= stroke_width * stroke_width:
                                canvas.create_text(
                                    x + position[0],
                                    y + position[1],
                                    text=line,
                                    font=custom_font,
                                    fill=f'#{stroke_rgb[0]:02x}{stroke_rgb[1]:02x}{stroke_rgb[2]:02x}',
                                    anchor='nw'
                                )

                # Draw main text
                canvas.create_text(
                    x + position[0],
                    y + position[1],
                    text=line,
                    font=custom_font,
                    fill=f'#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}',
                    anchor='nw'
                )

                y += line_height

            # Get canvas as image
            canvas.update()
            ps_image = canvas.postscript(colormode='color', pagewidth=canvas_width, pageheight=total_height)

            # Convert PostScript to PIL Image
            img = Image.open(BytesIO(ps_image.encode('utf-8')))

            # Convert to RGBA if opacity < 1
            if opacity < 1.0:
                img = img.convert('RGBA')
                # Apply opacity using alpha channel
                alpha = img.split()[3]
                alpha = Image.new('L', img.size, int(255 * opacity))
                img.putalpha(alpha)

            # Save to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()

            # Cleanup
            root.destroy()

            logger.info(f"✅ Text rendered successfully: {len(img_bytes)} bytes")
            return img_bytes

        except Exception as e:
            logger.error(f"❌ Tkinter text rendering failed: {e}", exc_info=True)
            raise

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _find_font_file(self, font_family: str) -> Optional[str]:
        """Find TTF font file for given font family."""
        font_name = font_family.lower().strip()

        # Common font directories
        font_dirs = ["/app/fonts", "/fonts", "/tmp/fonts", "/usr/share/fonts", "/System/Library/Fonts", "/Windows/Fonts"]

        # Search in /fonts and subdirectories
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                # Recursively find all .ttf files
                for ttf_file in glob.glob(os.path.join(font_dir, "**/*.ttf"), recursive=True):
                    font_basename = os.path.basename(ttf_file).lower()

                    # Check if font name is in filename
                    if font_name in font_basename:
                        return ttf_file

                    # Check alternative names
                    name_map = {
                        "arial": ["arial", "helvetica"],
                        "times new roman": ["times", "timesnewroman"],
                        "times": ["times", "timesnewroman"],
                        "open sans": ["opensans", "open-sans"],
                        "roboto": ["roboto"],
                        "helvetica": ["helvetica", "arial"],
                        "impact": ["impact"],
                        "georgia": ["georgia"],
                        "verdana": ["verdana"],
                        "trebuchet": ["trebuchet"],
                    }

                    if font_name in name_map:
                        for alt_name in name_map[font_name]:
                            if alt_name in font_basename:
                                return ttf_file

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

            logger.info(f"🎨 Rendering text with PIL: '{text}' font={font_family} size={font_size}")

            # Find font file
            font_path = self._find_font_file(font_family)
            if font_path:
                logger.info(f"✅ Found font: {font_path}")
                font = ImageFont.truetype(font_path, font_size)
            else:
                logger.warning(f"⚠️ Font not found: {font_family}")
                font = ImageFont.load_default()

            # Calculate text size
            dummy_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(dummy_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Add padding for stroke
            padding = stroke_width * 2 if stroke_width > 0 else 0

            # Create image
            img_width = text_width + position[0] + padding * 2
            img_height = text_height + position[1] + padding * 2

            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Convert colors
            color_rgb = self._hex_to_rgb(color)
            stroke_rgb = self._hex_to_rgb(stroke_color) if stroke_color else (0, 0, 0)

            # Draw stroke if specified
            if stroke_width > 0 and stroke_color:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx*dx + dy*dy <= stroke_width * stroke_width:
                            draw.text(
                                (position[0] + padding + dx, position[1] + padding + dy),
                                text,
                                font=font,
                                fill=stroke_rgb
                            )

            # Draw main text
            draw.text(
                (position[0] + padding, position[1] + padding),
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

            logger.info(f"✅ Text rendered successfully: {len(img_bytes)} bytes")
            return img_bytes

        except Exception as e:
            logger.error(f"❌ PIL text rendering failed: {e}", exc_info=True)
            raise
