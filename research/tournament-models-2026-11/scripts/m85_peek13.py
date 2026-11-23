# Sheets of tournament_workbook v13.xlsx: name, size, header, first rows.
import openpyxl
wb = openpyxl.load_workbook(r"C:\Users\crtra\Downloads\tournament_workbook v13.xlsx", read_only=True)
for ws in wb.worksheets:
    print("==", ws.title, ws.max_row, "x", ws.max_column)
    for k, row in enumerate(ws.iter_rows(values_only=True)):
        print("  ", row[:16])
        if k >= 3: break
