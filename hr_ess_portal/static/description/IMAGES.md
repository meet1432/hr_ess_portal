# Module Images Guide

## Overview

The following images are included in `static/description/` for the Odoo App Store listing:

### 1. **icon.png** (256×256 px)
- **Purpose**: Module icon displayed in Odoo App Store listing
- **Format**: PNG with transparent background recommended
- **Current**: Auto-generated placeholder with "ESS" branding
- **Location**: `static/description/icon.png`

### 2. **cover.png** (1200×630 px)
- **Purpose**: Cover/thumbnail image for the app store
- **Format**: PNG (landscape orientation)
- **Current**: Auto-generated placeholder
- **Location**: `static/description/cover.png`
- **Usage**: Displayed as the featured image on app store listing

### 3. **og_image.png** (1200×627 px)
- **Purpose**: Open Graph image for social sharing
- **Format**: PNG
- **Current**: Auto-generated placeholder
- **Location**: `static/description/og_image.png`

## Design Guidelines

### Icon Design (256×256)
✅ **Do:**
- Use the Neo-Brutalist color scheme (#6b4c7a primary, #354224 secondary)
- Keep design simple and scalable
- Ensure good contrast for visibility
- Use bold, clear typography or symbols

❌ **Don't:**
- Use too many colors
- Include small details that won't scale
- Use gradients (stick to solid colors)

**Example Icon Elements:**
- "ESS" text in bold sans-serif
- HR-related symbols (calendar, clock, person)
- Odoo-compatible styling

### Cover Image Design (1200×630)
✅ **Do:**
- Use landscape orientation (wider than tall)
- Feature the module name prominently
- Include 2-3 key benefits/features
- Use Neo-Brutalist design aesthetic
- Ensure text is readable at small sizes

**Recommended Content:**
- Module title: "Employee Self-Service Portal"
- Tagline: "Modern ESS for Odoo 19"
- Key benefit: "Reduce License Costs"
- Company/branding: "Odoo 19 Enterprise"

### Social Sharing Image (1200×627)
✅ **Do:**
- Similar design to cover image
- Optimized for Twitter, LinkedIn, etc.
- Include module benefits
- Clear, readable text

## Replacing the Placeholder Images

### Step 1: Create Better Designs

**Using Adobe XD, Figma, or Canva:**
1. Create icon (256×256 px)
2. Create cover (1200×630 px)
3. Create OG image (1200×627 px)
4. Export as PNG

**Design Principles:**
- Use the brand colors: #6b4c7a (primary), #354224 (secondary)
- Use system fonts: -apple-system, BlinkMacSystemFont, "Segoe UI"
- Keep design minimal and bold (Neo-Brutalist)
- Focus on clarity and readability

### Step 2: Save to static/description/

Replace the placeholder files:
- `static/description/icon.png`
- `static/description/cover.png`
- `static/description/og_image.png`

### Step 3: Test

1. Open `index.html` in a browser
2. Verify images display correctly
3. Check image quality at different sizes
4. Ensure branding consistency

## Current Placeholder Specifications

| File | Size | Background | Text | Status |
|------|------|-----------|------|--------|
| icon.png | 256×256 | #6b4c7a | "ESS" white | ⚠️ Placeholder |
| cover.png | 1200×630 | #6b4c7a gradient | Title + Subtitle | ⚠️ Placeholder |
| og_image.png | 1200×627 | #6b4c7a pattern | "ESS Portal" | ⚠️ Placeholder |

## Recommended Tools

### Free Options:
- **Figma** (figma.com) - Professional design tool, free tier available
- **Canva** (canva.com) - Template-based design, easy to use
- **Inkscape** (inkscape.org) - Open-source vector graphics
- **GIMP** (gimp.org) - Open-source image editor
- **Pixlr** (pixlr.com) - Browser-based editor

### Paid Options:
- **Adobe XD** - Professional design tool
- **Adobe Photoshop** - Full-featured image editor
- **Sketch** (macOS) - Professional design tool

## Color Palette Reference

Use these colors for consistency with the module:

```
Primary: #6b4c7a (Purple)
Secondary: #8b7297 (Light Purple)
Dark: #354224 (Dark Green)
Light: #f5f5f5 (Light Gray)
White: #ffffff
Accent Green: #27ae60
Accent Orange: #f59e0b
Accent Red: #dc2626
```

## App Store Requirements Summary

| Element | Required | Optional |
|---------|----------|----------|
| icon.png | ✅ Yes | No |
| cover.png | No | ✅ Recommended |
| og_image.png | No | ✅ Recommended |
| index.html | ✅ Yes | No |
| Screenshots | No | ✅ Recommended |

## Odoo App Store Submission

When submitting to apps.odoo.com:
1. ✅ icon.png will be displayed as the module icon
2. ✅ cover.png will be used as featured image (if provided)
3. ✅ og_image.png improves social sharing preview
4. ✅ Screenshots from index.html display in gallery
5. ✅ index.html content shown in full description

---

**Next Steps:**
1. Review current placeholder images
2. Create or commission professional designs
3. Replace PNG files in `static/description/`
4. Test before submitting to app store

For questions, see the main README.md file.