import os
import pandas as pd


dflist = []

for file in os.listdir("po"):
    if file.startswith("서울특별시.txt_변환완료") :
        df = pd.read_table(f"po/{file}", sep=",", dtype={"우편번호": str, "위도":str, "경도":str})
        df['경도'] = df['경도'].replace(r'\\n', '', regex=True)
        dflist.append(df)

dfs = pd.concat(dflist)
dfs.to_csv("서울특별시_변환완료.csv", index=False)