from datetime import datetime

import pandas as pd


async def save_on_excel(table, city, search_query):
    day_now = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")
    with pd.ExcelWriter(
        f"./files/{city}-{search_query}-{day_now}.xlsx", engine="openpyxl"
    ) as writer:
        table.to_excel(writer, index=False, sheet_name="Sheet1", engine="openpyxl")
        worksheet = writer.sheets["Sheet1"]
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
