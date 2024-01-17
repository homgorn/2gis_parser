import asyncio
from ast import literal_eval

import pandas as pd
from openpyxl.styles import Alignment


async def get_excel(city, search_query):
    df = pd.read_csv(
        f"result_output/{city}_{search_query}.csv", converters={"outputs": literal_eval}
    )
    df = df.dropna(subset=["title"])
    result_df = pd.DataFrame(
        columns=[
            "title",
            "phone",
            "link",
            "social",
            "rating",
            "count",
        ]
    )

    for index, row in df.iterrows():
        title = row["title"]
        link = "\n".join(literal_eval(row["link"]))
        phones = ""
        if not isinstance(row["phone"], float) and ".." not in str(row["phone"]):
            phones = "\n".join(literal_eval(row["phone"]))
        socials = "\n".join(literal_eval(row["socials"]))

        rating = str(row["rating"]) if str(row["rating"]) != "nan" else ""
        count = df[df["title"] == title].shape[0]
        result_df = pd.concat(
            [
                result_df,
                pd.DataFrame(
                    {
                        "title": [title],
                        "phone": [phones],
                        "link": [link],
                        "rating": [rating],
                        "count": [count],
                        "social": [socials],
                    }
                ),
            ]
        )

    result_df = result_df.drop_duplicates(subset="title")

    with pd.ExcelWriter(f"files/{city}_{search_query}.xlsx", engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="Sheet1", engine="openpyxl")
        worksheet = writer.sheets["Sheet1"]

        # Устанавливаем ширину для каждой колонки под её содержимое
        for column in worksheet.columns:
            max_length = 7
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length * 3:
                        max_length = len(cell.value) / 2
                except:
                    pass
            adjusted_width = max_length + 2
            for cell in column:
                cell.alignment = Alignment(wrap_text=True)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width


# asyncio.run(get_excel("самара", "Магазин%20техники"))
