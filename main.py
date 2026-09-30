import ezdxf
from ezdxf import units
import math

# --- Параметры подиума ---
DIAMETER = 2600.0
HEIGHT = 150.0
THICKNESS = 15.0
SEGMENTS = 6
GAP = 4.0

# --- Параметры листа ---
SHEET_W = 1220.0
SHEET_H = 2440.0

# --- Расчёт сегментов ---
radius = DIAMETER / 2.0
angle_step = 2 * math.pi / SEGMENTS
chord = 2 * radius * math.sin(angle_step / 2)
sagitta = radius - radius * math.cos(angle_step / 2)

# Габариты одной детали (с припуском на стык)
seg_len = chord + 20.0  # небольшой запас
seg_width = sagitta + 10.0

# Габариты ребра жёсткости
rib_len = radius - THICKNESS
rib_h = HEIGHT - THICKNESS

# --- Функция раскладки деталей на листах ---
def layout_parts(parts, sheet_w, sheet_h, gap):
    sheets = []
    current_sheet = []
    current_x = 0
    current_y = 0
    row_height = 0

    for (w, h, name) in parts:
        if current_x + w > sheet_w:
            # новая строка
            current_y += row_height + gap
            current_x = 0
            row_height = 0

        if current_y + h > sheet_h:
            # новый лист
            sheets.append(current_sheet)
            current_sheet = []
            current_x = 0
            current_y = 0
            row_height = 0

        current_sheet.append((current_x, current_y, w, h, name))
        current_x += w + gap
        row_height = max(row_height, h)

    if current_sheet:
        sheets.append(current_sheet)

    return sheets

# --- Формируем список деталей ---
parts = []
# 6 сегментов крышки
for i in range(SEGMENTS):
    parts.append((seg_len, seg_width, f"TOP_{i+1}"))
# 6 сегментов боковины
for i in range(SEGMENTS):
    parts.append((seg_len, HEIGHT, f"SIDE_{i+1}"))
# 6 рёбер жёсткости
for i in range(SEGMENTS):
    parts.append((rib_len, rib_h, f"RIB_{i+1}"))

# --- Раскладываем ---
sheets = layout_parts(parts, SHEET_W, SHEET_H, GAP)

print(f"Всего деталей: {len(parts)}")
print(f"Листов фанеры: {len(sheets)}")

# --- Создаём DXF ---
doc = ezdxf.new("R2010")
doc.units = units.MM
msp = doc.modelspace()

for sheet_idx, sheet in enumerate(sheets):
    offset_x = sheet_idx * (SHEET_W + 200.0)  # сдвигаем листы по X
    # Рисуем контур листа
    msp.add_lwpolyline([
        (offset_x, 0),
        (offset_x + SHEET_W, 0),
        (offset_x + SHEET_W, SHEET_H),
        (offset_x, SHEET_H),
        (offset_x, 0)
    ], dxfattribs={"layer": "SHEET"})

    # Рисуем детали
    for (x, y, w, h, name) in sheet:
        msp.add_lwpolyline([
            (offset_x + x, y),
            (offset_x + x + w, y),
            (offset_x + x + w, y + h),
            (offset_x + x, y + h),
            (offset_x + x, y)
        ], dxfattribs={"layer": "CUT"})
        msp.add_text(name, dxfattribs={
            "layer": "TEXT", "height": 20
        }).set_placement((offset_x + x + w/2, y + h/2))

doc.saveas("podium_layout.dxf")
print("Файл podium_layout.dxf создан.")
