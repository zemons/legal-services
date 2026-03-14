"""แปลงตัวเลขเป็นตัวหนังสือไทย / บาทไทย"""

_DIGITS = ('', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า')
_POSITIONS = ('', 'สิบ', 'ร้อย', 'พัน', 'หมื่น', 'แสน', 'ล้าน')


def _chunk_to_text(n):
    """แปลงตัวเลข 1-999999 เป็นตัวหนังสือไทย"""
    if n == 0:
        return 'ศูนย์'

    s = str(int(n))
    length = len(s)
    parts = []

    for i, ch in enumerate(s):
        digit = int(ch)
        pos = length - i - 1  # position from right (0=หน่วย, 1=สิบ, ...)

        if digit == 0:
            continue

        if pos == 1 and digit == 2:
            parts.append('ยี่สิบ')
        elif pos == 1 and digit == 1:
            parts.append('สิบ')
        elif pos == 0 and digit == 1 and length > 1:
            parts.append('เอ็ด')
        else:
            parts.append(_DIGITS[digit] + _POSITIONS[pos])

    return ''.join(parts)


def number_to_thai_text(value):
    """แปลงตัวเลขเป็นตัวหนังสือไทย

    Examples:
        0 → "ศูนย์"
        1 → "หนึ่ง"
        21 → "ยี่สิบเอ็ด"
        1500 → "หนึ่งพันห้าร้อย"
        1000000 → "หนึ่งล้าน"
        1500000 → "หนึ่งล้านห้าแสน"
    """
    try:
        num = float(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return str(value)

    if num < 0:
        return 'ลบ' + number_to_thai_text(-num)

    integer_part = int(num)

    if integer_part == 0:
        return 'ศูนย์'

    # Split into groups of 6 digits (each group up to ล้าน)
    result = []
    millions = 0

    while integer_part > 0:
        chunk = integer_part % 1000000
        integer_part //= 1000000

        if chunk > 0:
            text = _chunk_to_text(chunk)
            if millions > 0:
                text += 'ล้าน' * millions
            result.append(text)

        millions += 1

    result.reverse()
    return ''.join(result)


def baht_text(value):
    """แปลงตัวเลขเป็นบาทไทย

    Examples:
        1500 → "หนึ่งพันห้าร้อยบาทถ้วน"
        1500.50 → "หนึ่งพันห้าร้อยบาทห้าสิบสตางค์"
        0.25 → "ยี่สิบห้าสตางค์"
    """
    try:
        num = float(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return str(value)

    if num < 0:
        return 'ลบ' + baht_text(-num)

    # Split integer and satang
    integer_part = int(num)
    satang = round((num - integer_part) * 100)

    # Handle rounding overflow
    if satang >= 100:
        integer_part += 1
        satang = 0

    parts = []
    if integer_part > 0:
        parts.append(number_to_thai_text(integer_part))
        parts.append('บาท')

    if satang > 0:
        parts.append(number_to_thai_text(satang))
        parts.append('สตางค์')
    elif integer_part > 0:
        parts.append('ถ้วน')
    else:
        return 'ศูนย์บาทถ้วน'

    return ''.join(parts)
