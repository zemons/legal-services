#!/usr/bin/env python3
"""
Full setup: Create LIFF app + Lawyer Rich Menu + Upload image.

Usage:
    export LINE_CHANNEL_ACCESS_TOKEN="your-token"
    export ODOO_BASE_URL="https://law.zemons.com"
    python3 scripts/setup_lawyer_menu.py

Steps:
1. Create LIFF app (full size, pointing to Odoo base URL)
2. Create Lawyer Rich Menu (2x3 grid with LIFF URLs)
3. Generate & upload Rich Menu image
4. Print all IDs for configuration
"""

import json
import os
import sys

import requests

ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
ODOO_BASE_URL = os.environ.get('ODOO_BASE_URL', 'https://law.zemons.com')

if not ACCESS_TOKEN:
    print("ERROR: Set LINE_CHANNEL_ACCESS_TOKEN environment variable")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: Create LIFF app
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def list_liff_apps():
    """List existing LIFF apps."""
    resp = requests.get(
        'https://api.line.me/liff/v1/apps',
        headers=HEADERS,
    )
    if resp.status_code != 200:
        print(f"   Failed to list LIFF apps: {resp.status_code} {resp.text}")
        return []
    return resp.json().get('apps', [])


def create_liff_app():
    """Create a LIFF app (full size) pointing to Odoo."""
    print("Step 1: Creating LIFF app...")

    # Check existing LIFF apps first
    existing = list_liff_apps()
    if existing:
        print(f"   Found {len(existing)} existing LIFF app(s):")
        for app in existing:
            liff_id = app.get('liffId', '')
            view = app.get('view', {})
            print(f"   - {liff_id} ({view.get('type', '?')}) → {view.get('url', '?')}")

        # Check if there's already one pointing to our Odoo
        for app in existing:
            url = app.get('view', {}).get('url', '')
            if ODOO_BASE_URL in url:
                liff_id = app['liffId']
                print(f"   Reusing existing LIFF: {liff_id}")
                return liff_id

        print(f"   None pointing to {ODOO_BASE_URL}, creating new...")

    resp = requests.post(
        'https://api.line.me/liff/v1/apps',
        headers=HEADERS,
        json={
            'view': {
                'type': 'full',
                'url': ODOO_BASE_URL,
            },
            'description': 'Legal Services LIFF',
            'features': {
                'ble': False,
            },
            'permanentLinkPattern': 'concat',
        },
    )

    if resp.status_code in (200, 201):
        liff_id = resp.json().get('liffId', '')
        print(f"   OK: LIFF ID = {liff_id}")
        return liff_id
    else:
        print(f"   FAILED: {resp.status_code} {resp.text}")
        sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: Create Rich Menu
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_rich_menu(liff_id):
    """Create Lawyer Rich Menu with 2x3 grid."""
    print("Step 2: Creating Lawyer Rich Menu...")

    liff_url = f'https://liff.line.me/{liff_id}'
    COL_W = 2500 // 3  # 833
    ROW_H = 1686 // 2  # 843

    body = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Lawyer Menu v2 - Document Creation",
        "chatBarText": "เมนูทนาย",
        "areas": [
            # Row 1: คดีของฉัน | สร้างเอกสาร | ถ่ายรูปฎีกา
            {
                "bounds": {"x": 0, "y": 0, "width": COL_W, "height": ROW_H},
                "action": {"type": "uri", "label": "คดีของฉัน",
                           "uri": f"{liff_url}/liff/cases"}
            },
            {
                "bounds": {"x": COL_W, "y": 0, "width": COL_W, "height": ROW_H},
                "action": {"type": "uri", "label": "สร้างเอกสาร",
                           "uri": f"{liff_url}/liff/document/create"}
            },
            {
                "bounds": {"x": COL_W * 2, "y": 0, "width": 2500 - COL_W * 2, "height": ROW_H},
                "action": {"type": "uri", "label": "ถ่ายรูปฎีกา",
                           "uri": f"{liff_url}/liff/capture"}
            },
            # Row 2: ตารางนัด | ค้นหากฎหมาย | ถามคำถาม
            {
                "bounds": {"x": 0, "y": ROW_H, "width": COL_W, "height": 1686 - ROW_H},
                "action": {"type": "uri", "label": "ตารางนัด",
                           "uri": f"{liff_url}/liff/schedule"}
            },
            {
                "bounds": {"x": COL_W, "y": ROW_H, "width": COL_W, "height": 1686 - ROW_H},
                "action": {"type": "postback", "label": "ค้นหากฎหมาย",
                           "data": "action=legal_search"}
            },
            {
                "bounds": {"x": COL_W * 2, "y": ROW_H, "width": 2500 - COL_W * 2, "height": 1686 - ROW_H},
                "action": {"type": "postback", "label": "ถามคำถาม",
                           "data": "action=ask_question_lawyer"}
            },
        ]
    }

    resp = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        headers=HEADERS,
        json=body,
    )

    if resp.status_code != 200:
        print(f"   FAILED: {resp.status_code} {resp.text}")
        sys.exit(1)

    menu_id = resp.json().get('richMenuId')
    print(f"   OK: Rich Menu ID = {menu_id}")
    return menu_id


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: Generate & upload image
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_image(output_path):
    """Generate Rich Menu image (2500x1686 PNG)."""
    print("Step 3a: Generating Rich Menu image...")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("   ERROR: pip install Pillow")
        sys.exit(1)

    W, H = 2500, 1686
    img = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(img)

    # Load Thai font
    font_large = font_small = None
    for fp in [
        '/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansThai-Bold.ttf',
        '/usr/share/fonts/truetype/tlwg/Sawasdee-Bold.ttf',
    ]:
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

    labels_th = ['คดีของฉัน', 'สร้างเอกสาร', 'ถ่ายรูปฎีกา', 'ตารางนัด', 'ค้นหากฎหมาย', 'ถามคำถาม']
    labels_en = ['My Cases', 'Create Doc', 'Capture', 'Schedule', 'Search Law', 'Ask AI']
    bg_row1 = ['#16213e', '#0f3460', '#1a1a40']
    bg_row2 = ['#1b2838', '#162447', '#1b1b3a']

    col_w, row_h = W // 3, H // 2

    for i in range(6):
        col, row = i % 3, i // 3
        x0, y0 = col * col_w, row * row_h
        x1, y1 = x0 + col_w, y0 + row_h

        bg = (bg_row1 if row == 0 else bg_row2)[col]
        draw.rectangle([x0, y0, x1, y1], fill=bg)
        draw.line([x1, y0, x1, y1], fill='#2a2a4a', width=2)
        draw.line([x0, y1, x1, y1], fill='#2a2a4a', width=2)

        # Highlight "สร้างเอกสาร"
        if i == 1:
            draw.rectangle([x0, y0, x1, y1], fill='#0f3460')
            draw.rectangle([x0, y0, x1, y0 + 6], fill='#e94560')

        cx, cy = x0 + col_w // 2, y0 + row_h // 2

        # Center Thai text
        try:
            bbox = draw.textbbox((0, 0), labels_th[i], font=font_large)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(labels_th[i]) * 30
        draw.text((cx - tw // 2, cy - 50), labels_th[i], fill='#ffffff', font=font_large)

        # Center English text
        try:
            bbox2 = draw.textbbox((0, 0), labels_en[i], font=font_small)
            tw2 = bbox2[2] - bbox2[0]
        except Exception:
            tw2 = len(labels_en[i]) * 18
        draw.text((cx - tw2 // 2, cy + 60), labels_en[i], fill='#a0a0b0', font=font_small)

    img.save(output_path, 'PNG')
    print(f"   Saved: {output_path}")
    return output_path


def upload_image(menu_id, image_path):
    """Upload Rich Menu image to LINE."""
    print("Step 3b: Uploading image to LINE...")
    with open(image_path, 'rb') as f:
        resp = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{menu_id}/content',
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Setup LINE LIFF + Lawyer Rich Menu')
    parser.add_argument('--image', help='Use existing PNG image instead of generating')
    parser.add_argument('--liff-id', help='Use existing LIFF ID instead of creating new')
    parser.add_argument('--skip-liff', action='store_true', help='Skip LIFF creation')
    args = parser.parse_args()

    print(f"Odoo Base URL: {ODOO_BASE_URL}")
    print()

    # Step 1: LIFF
    if args.liff_id:
        liff_id = args.liff_id
        print(f"Step 1: Using provided LIFF ID: {liff_id}")
    elif args.skip_liff:
        liff_id = '0000000000-xxxxxxxx'
        print("Step 1: Skipped (using placeholder)")
    else:
        liff_id = create_liff_app()

    print()

    # Step 2: Rich Menu
    menu_id = create_rich_menu(liff_id)
    print()

    # Step 3: Image
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if args.image:
        image_path = args.image
    else:
        image_path = os.path.join(script_dir, 'lawyer_richmenu.png')
        generate_image(image_path)

    upload_image(menu_id, image_path)
    print()

    # ── Summary ──────────────────────────────────────────
    print("=" * 60)
    print("  SETUP COMPLETE")
    print("=" * 60)
    print()
    print(f"  LIFF ID:       {liff_id}")
    print(f"  LIFF URL:      https://liff.line.me/{liff_id}")
    print(f"  Rich Menu ID:  {menu_id}")
    print()
    print("  Odoo System Parameters to set:")
    print(f"    line_integration.liff_id          = {liff_id}")
    print(f"    line_integration.rich_menu_lawyer  = {menu_id}")
    print()
    print("  Re-link existing lawyers (Odoo shell):")
    print("    env['res.partner'].search([('line_role','=','lawyer')])._link_rich_menu_by_role()")
    print()
