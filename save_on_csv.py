import os

import pandas as pd


def create_dirs():
    if not os.path.exists("result_output"):
        os.makedirs("result_output")
    if not os.path.exists("files"):
        os.makedirs("files")


def save_data_to_csv(data_in_memory, city, search_query):
    df = pd.DataFrame(
        data_in_memory, columns=["title", "link", "phone", "real_email", "socials", "rating"]
    )
    df.to_csv(
        f"result_output/{city}_{search_query}.csv",
        mode="a",
        header=not os.path.isfile(f"result_output/{city}_{search_query}.csv"),
        index=False,
    )
