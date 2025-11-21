# Fonts Directory

This directory contains TTF font files for text overlay functionality.

## Adding Fonts

### Option 1: Copy from System (Linux/Mac)
```bash
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf ./fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf ./fonts/
```

### Option 2: Download from Google Fonts
1. Go to fonts.google.com
2. Select a font and download the TTF files
3. Place .ttf files in this directory

### Option 3: Use Free Font Repositories
- Font Squirrel: https://www.fontsquirrel.com/
- DaFont: https://www.dafont.com/
- 1001 Free Fonts: https://www.1001freefonts.com/

## Required Fonts

The app looks for these fonts (in order):
1. DejaVuSans.ttf
2. OpenSans-Regular.ttf
3. Roboto-Regular.ttf
4. Arial.ttf

## Note

TTF files can be large (>500KB). The fonts directory is tracked in git.
