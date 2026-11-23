# Look inside reports/regular_season_pmpm.xlsx: sheets, sizes, headers, first rows.
import openpyxl
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\basketball\reports\regular_season_pmpm.xlsx", read_only=True)
for ws in wb.worksheets:
    print("==", ws.title, ws.max_row, "x", ws.max_column)
    for k, row in enumerate(ws.iter_rows(values_only=True)):
        print("  ", row[:20])
        if k >= 4: break
