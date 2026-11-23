# How is "A Games" in v13 styled? Fonts, fills, widths, merges, freeze, conditional formats, number formats.
import openpyxl
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\tournament_workbook v13.xlsx")
ws = wb["A Games"]
print("dims", ws.dimensions, "freeze", ws.freeze_panes, "merged", list(ws.merged_cells.ranges)[:5], "autofilter", ws.auto_filter.ref)
print("cond formats:", [(str(r.sqref), [x.type for x in r.rules]) for r in ws.conditional_formatting])
print("widths:", {k: d.width for k, d in list(ws.column_dimensions.items())[:20]})
print("row heights:", {k: d.height for k, d in list(ws.row_dimensions.items())[:6]})
def show(c):
    f = c.fill.fgColor.rgb if c.fill and c.fill.fill_type else None
    print(f"  {c.coordinate:6} {str(c.value)[:30]:30} font={c.font.name},{c.font.sz},b={c.font.b},i={c.font.i},col={c.font.color.rgb if c.font.color else None} "
          f"fill={f} fmt={c.number_format} align={c.alignment.horizontal},{c.alignment.wrap_text} border={c.border.bottom.style}")
for coord in ["A1", "A2", "A4", "D4", "N4", "A5", "B5", "C5", "D5", "E5", "H5", "I5", "J5", "K5", "L5", "M5", "N5", "O5", "AA5", "AZ5", "BA5", "A6", "N6", "AA6", "A7"]:
    show(ws[coord])
print("header row:", [c.value for c in ws[4]])
print("row5:", [c.value for c in ws[5]][:20]); print("row6:", [c.value for c in ws[6]][:20])
import collections
fills = collections.Counter()
for row in ws.iter_rows(min_row=5, max_row=200, min_col=14, max_col=53):
    for c in row:
        if isinstance(c.value, (int, float)): fills[(c.value, c.fill.fgColor.rgb)] += 1
for v in (-20, -10, -5, -1, 0, 1, 5, 10, 20):
    print(v, [k[1] for k in fills if k[0] == v][:3])
