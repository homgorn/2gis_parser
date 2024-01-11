from ast import literal_eval

import pandas as pd
from openpyxl.styles import Alignment


async def get_excel(city, search_query):
    df = pd.read_csv(
        f"result_output/{city}_{search_query}.csv", converters={"outputs": literal_eval}
    )
    df = df.dropna(subset=["title"])
    result_df = pd.DataFrame(columns=["title", "link", "phone", "social", "rating", "count"])

    for index, row in df.iterrows():
        title = row["title"]
        link = row["link"]
        phones = (
            "".join(map(str, row["phone"])).replace("'", "").replace("{", "").replace("}", "")
            if not pd.isna(row["phone"]) and row["phone"] != ""
            else None
        )
        socials = (
            "\n".join(map(str, row["socials"])).replace("'", "").replace("[", "").replace("]", "")
            if not pd.isna(row["socials"]) and row["socials"] != ""
            else None
        )

        rating = str(row["rating"])
        count = df[df["title"] == title].shape[0]

        result_df = pd.concat(
            [
                result_df,
                pd.DataFrame(
                    {
                        "title": [title],
                        "link": [link],
                        "phone": [phones],
                        "social": [socials],
                        "rating": [rating],
                        "count": [count],
                    }
                ),
            ]
        )

    result_df = result_df.drop_duplicates(subset="title")

    with pd.ExcelWriter(f"files/{city}_{search_query}.xlsx", engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="Sheet1", engine="openpyxl")
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
            for cell in column:
                cell.alignment = Alignment(wrap_text=True)


# asyncio.run(get_excel("samara", "Вкусно и точка"))
