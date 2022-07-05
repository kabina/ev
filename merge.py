import os
import pandas as pd

csvlist = []

filename = "강원도"

for file in os.listdir("po"):
    if file.startswith(f"{filename}.txt_변환완료") :
        df = pd.read_table(f"po/{file}", sep=",", dtype={"우편번호": str, "위도":str, "경도":str})
        df['경도'] = df['경도'].replace(r'\\n', '', regex=True)
        del_idx = df[df['건물명'].isnull()].index
        df = df.drop(del_idx)
        csvlist.append(df)

dfs = pd.concat(csvlist)
dfs.to_csv(f"{filename}_변환완료.csv", index=False)
