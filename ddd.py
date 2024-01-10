# import asyncio
# from ast import literal_eval
#
# import pandas as pd
# from openpyxl.styles import Alignment
#
#
# async def read_csv(query):
#     df = pd.read_csv(
#         f"result_output/{query}_outputs.csv", converters={"outputs": literal_eval}
#     )
#     return df
#
#
# async def process_data(df):
#     df = df.dropna(subset=["name"])
#     result_df = pd.DataFrame(
#         columns=["name", "website", "phones", "social", "count", "rating", "ypage"]
#     )
#
#     for index, row in df.iterrows():
#         name = row["name"]
#         website = row["website"]
#         phones = "\n".join(literal_eval(row["phone"])).replace("Показать телефон", "")
#         social = "\n".join(literal_eval(row["social"]))
#         count = df[df["name"] == name].shape[0]
#         rating = row["rating"]
#         ypage = row["ypage"]
#
#         result_df = pd.concat(
#             [
#                 result_df,
#                 pd.DataFrame(
#                     {
#                         "name": [name],
#                         "website": [website],
#                         "phones": [phones],
#                         "social": [social],
#                         "count": [count],
#                         "rating": [rating],
#                         "ypage": ypage,
#                     }
#                 ),
#             ]
#         )
#     result_df["rating"] = result_df["rating"].str.replace(",", ".")
#     result_df["rating"] = result_df["rating"].astype(float)
#     result_df = result_df.drop_duplicates(subset="name")
#
#     return result_df
#
#
# async def rename_columns(result_df):
#     column_mapping = {
#         "name": "Имя",
#         "website": "Сайт",
#         "phones": "Телефоны",
#         "social": "Соц. сети",
#         "count": "Количество",
#         "rating": "Райтинг",
#         "ypage": "Страница на картах",
#     }
#
#     result_df = result_df.rename(columns=column_mapping)
#     return result_df
#
#
# async def write_to_excel(city, query, result_df):
#     with pd.ExcelWriter(f"{city}_{query}.xlsx", engine="openpyxl") as writer:
#         result_df.to_excel(
#             writer, index=False, sheet_name="Страница1", engine="openpyxl"
#         )
#         worksheet = writer.sheets["Страница1"]
#         for column in worksheet.columns:
#             max_length = 0
#             column = [cell for cell in column]
#             for cell in column:
#                 try:
#                     if len(str(cell.value)) > max_length:
#                         max_length = len(cell.value)
#                 except:
#                     pass
#             adjusted_width = max_length + 2
#             worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
#             for cell in column:
#                 cell.alignment = Alignment(wrap_text=True)
#
#
# async def get_excel(city, query):
#     df = await read_csv(query)
#     result_df = await process_data(df)
#     result_df = await rename_columns(result_df)
#     await write_to_excel(city, query, result_df)
#
#
# # asyncio.run(get_excel("Самара", "Магазин снегоходов"))
import asyncio
from ast import literal_eval
import pandas as pd


async def get_excel(city, query):
    df = pd.read_csv(
        f"result_output/{query}_outputs.csv", converters={"outputs": literal_eval}
    )
    df = df.dropna(subset=["name"])
    result_df = pd.DataFrame(columns=["name", "website", "phones", "social", "count"])
    for index, row in df.iterrows():
        name = row["name"]
        website = row["website"]
        phones = (
            "".join(map(str, row["phone"]))
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
            .replace("Показать телефон", "")
        )

        social = (
            "".join(map(str, row["social"]))
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
        )

        count = df[df["name"] == name].shape[0]

        result_df = pd.concat(
            [
                result_df,
                pd.DataFrame(
                    {
                        "name": [name],
                        "website": [website],
                        "phones": [phones],
                        "social": [social],
                        "count": [count],
                    }
                ),
            ]
        )

    # Заменить запятые на точки в столбце "rating"
    result_df["rating"] = result_df["rating"].str.replace(",", ".")

    # Преобразование столбца "rating" в числовой тип
    result_df["rating"] = (
        result_df["rating"].astype(float) if result_df["rating"] != "" else 0.0
    )

    result_df = result_df.drop_duplicates(subset="name")

    with pd.ExcelWriter(f"{city}_{query}.xlsx", engine="openpyxl") as writer:
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
