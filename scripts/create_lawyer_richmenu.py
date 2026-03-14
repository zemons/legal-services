#!/usr/bin/env python3
"""
Create Lawyer Rich Menu for LINE OA with "สร้างเอกสาร" button.

Usage:
    export LINE_CHANNEL_ACCESS_TOKEN="your-token"
    export LIFF_URL="https://liff.line.me/YOUR_LIFF_ID"
    python3 scripts/create_lawyer_richmenu.py

This script will:
1. Create a Rich Menu via LINE API (2x3 grid)
2. Upload the menu image
3. Print the new Rich Menu ID

Update the Rich Menu ID in Odoo System Parameters:
    line_integration.rich_menu_lawyer = <new-id>
"""

import json
import os
import sys

import requests

ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LIFF_URL = os.environ.get('LIFF_URL', 'https://liff.line.me/0000000000-xxxxxxxx')
ODOO_BASE_URL = os.environ.get('ODOO_BASE_URL', 'https://law.zemons.com')

if not ACCESS_TOKEN:
    print("ERROR: Set LINE_CHANNEL_ACCESS_TOKEN environment variable")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}

# ── Rich Menu Definition ───────────────────────────────────
# Layout: 2500 x 1686 px, 2 rows x 3 columns
# Row 1: คดีของฉัน | สร้างเอกสาร | ถ่ายรูปฎีกา
# Row 2: ตารางนัด | ค้นหากฎหมาย | ถามคำถาม

COL_W = 2500 // 3  # ~833
ROW_H = 1686 // 2  # 843

rich_menu_body = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "Lawyer Menu v2 - Document Creation",
    "chatBarText": "เมนูทนาย",
    "areas": [
        # Row 1
        {
            "bounds": {"x": 0, "y": 0, "width": COL_W, "height": ROW_H},
            "action": {"type": "uri", "label": "คดีของฉัน", "uri": f"{LIFF_URL}/liff/cases"}
        },
        {
            "bounds": {"x": COL_W, "y": 0, "width": COL_W, "height": ROW_H},
            "action": {"type": "uri", "label": "สร้างเอกสาร", "uri": f"{LIFF_URL}/liff/document/create"}
        },
        {
            "bounds": {"x": COL_W * 2, "y": 0, "width": 2500 - COL_W * 2, "height": ROW_H},
            "action": {"type": "uri", "label": "ถ่ายรูปฎีกา", "uri": f"{LIFF_URL}/liff/capture"}
        },
        # Row 2
        {
            "bounds": {"x": 0, "y": ROW_H, "width": COL_W, "height": 1686 - ROW_H},
            "action": {"type": "uri", "label": "ตารางนัด", "uri": f"{LIFF_URL}/liff/schedule"}
        },
        {
            "bounds": {"x": COL_W, "y": ROW_H, "width": COL_W, "height": 1686 - ROW_H},
            "action": {"type": "postback", "label": "ค้นหากฎหมาย", "data": "action=legal_search"}
        },
        {
            "bounds": {"x": COL_W * 2, "y": ROW_H, "width": 2500 - COL_W * 2, "height": 1686 - ROW_H},
            "action": {"type": "postback", "label": "ถามคำถาม", "data": "action=ask_question_lawyer"}
        },
    ]
}


def create_rich_menu():
    print("1. Creating Rich Menu...")
    resp = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        headers=HEADERS,
        json=rich_menu_body,
    )
    if resp.status_code != 200:
        print(f"   FAILED: {resp.status_code} {resp.text}")
        sys.exit(1)

    rich_menu_id = resp.json().get('richMenuId')
    print(f"   OK: {rich_menu_id}")
    return rich_menu_id


def upload_image(rich_menu_id, image_path):
    print(f"2. Uploading image: {image_path}")
    with open(image_path, 'rb') as f:
        resp = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'image/png',
            },
            data=f.read(),
        )
    if resp.status_code != 200:
        print(f"   FAILED: {resp.status_code} {resp.text}")
        sys.exit(1)
    print("   OK")


def generate_image(output_path):
    """Generate a Rich Menu image using Pillow."""
    print("0. Generating Rich Menu image...")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("   Pillow not installed. Install with: pip install Pillow")
        print("   Or provide your own image and run with: --image <path>")
        sys.exit(1)

    W, H = 2500, 1686
    img = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(img)

    # Try to load Thai font
    font_large = None
    font_small = None
    font_paths = [
        '/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansThai-Bold.ttf',
        '/usr/share/fonts/truetype/tlwg/Sawasdee-Bold.ttf',
        '/usr/share/fonts/truetype/tlwg/TlwgTypo-Bold.ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_large = ImageFont.truetype(fp, 100)
                font_small = ImageFont.truetype(fp, 64)
                break
            except Exception:
                continue

    if not font_large:
        font_large = ImageFont.load_default()
        font_small = font_large

    # Colors
    colors = {
        'row1_bg': ['#16213e', '#0f3460', '#1a1a40'],
        'row2_bg': ['#1b2838', '#162447', '#1b1b3a'],
        'accent': '#e94560',
        'text': '#ffffff',
        'subtext': '#a0a0b0',
    }

    icons = ['📋', '📝', '📷', '📅', '🔍', '💬']
    labels_th = ['คดีของฉัน', 'สร้างเอกสาร', 'ถ่ายรูปฎีกา', 'ตารางนัด', 'ค้นหากฎหมาย', 'ถามคำถาม']
    labels_en = ['My Cases', 'Create Doc', 'Capture', 'Schedule', 'Search Law', 'Ask AI']

    col_w = W // 3
    row_h = H // 2

    for i in range(6):
        col = i % 3
        row = i // 3
        x0 = col * col_w
        y0 = row * row_h
        x1 = x0 + col_w
        y1 = y0 + row_h

        # Background
        bg_colors = colors['row1_bg'] if row == 0 else colors['row2_bg']
        bg = bg_colors[col]
        draw.rectangle([x0, y0, x1, y1], fill=bg)

        # Border lines
        draw.line([x1, y0, x1, y1], fill='#2a2a4a', width=2)
        draw.line([x0, y1, x1, y1], fill='#2a2a4a', width=2)

        # Highlight "สร้างเอกสาร" button (index 1)
        if i == 1:
            draw.rectangle([x0, y0, x1, y1], fill='#0f3460')
            # Accent bar at top
            draw.rectangle([x0, y0, x1, y0 + 6], fill=colors['accent'])

        cx = x0 + col_w // 2
        cy = y0 + row_h // 2

        # Thai label
        try:
            bbox = draw.textbbox((0, 0), labels_th[i], font=font_large)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(labels_th[i]) * 30
        draw.text((cx - tw // 2, cy - 50), labels_th[i], fill=colors['text'], font=font_large)

        # English sublabel
        try:
            bbox2 = draw.textbbox((0, 0), labels_en[i], font=font_small)
            tw2 = bbox2[2] - bbox2[0]
        except Exception:
            tw2 = len(labels_en[i]) * 18
        draw.text((cx - tw2 // 2, cy + 60), labels_en[i], fill=colors['subtext'], font=font_small)

    img.save(output_path, 'PNG')
    print(f"   Saved: {output_path}")
    return output_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create LINE Lawyer Rich Menu')
    parser.add_argument('--image', help='Path to existing 2500x1686 PNG image')
    parser.add_argument('--generate-only', action='store_true', help='Only generate image, do not call LINE API')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_image = os.path.join(script_dir, 'lawyer_richmenu.png')

    if args.image:
        image_path = args.image
    else:
        image_path = generate_image(default_image)

    if args.generate_only:
        print("Done (generate only)")
        sys.exit(0)

    menu_id = create_rich_menu()
    upload_image(menu_id, image_path)

    print()
    print("=" * 60)
    print(f"NEW LAWYER RICH MENU ID: {menu_id}")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"1. Update Odoo System Parameter:")
    print(f"   line_integration.rich_menu_lawyer = {menu_id}")
    print()
    print("2. Or update code defaults in:")
    print("   line_integration/models/res_partner.py")
    print("   line_integration/controllers/line_webhook.py")
    print()
    print("3. Re-link existing lawyers:")
    print("   In Odoo shell: env['res.partner'].search([('line_role','=','lawyer')])._link_rich_menu_by_role()")
