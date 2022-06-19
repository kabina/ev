import random
from tqdm import tqdm
from evlogger import Logger
import logging
import time, json, requests
from tqdm import tqdm

logger = Logger()
global evlogger
evlogger = logger.initLogger(loglevel=logging.DEBUG)
conn = None

def getConnection():
    import pymysql
    conn = pymysql.connect(host="rds-aurora-mysql-ev-charger-svc-instance-0.cnjsh2ose5fj.ap-northeast-2.rds.amazonaws.com",
                           user='evsp_usr', password='evspuser!!', db='evsp', charset='utf8', port=3306)

    return conn

lat_c , lng_c = 37.561253, 126.834329

last_name = ['김','이', '박', '최', '안', '장',  '윤','구','차', '정','주','진', '추','임','강']
name_first = ['주', '하', '창', '희', '수', '경', '혜', '지', '서', '현', '주', '진', '광', \
              '천', '선', '경','철', '영', '기', '정', '우', '도', '윤', '강']

def get_lat_lng(lat=37.561253, lng=126.834329):
    radius = random.randrange(1,1000)*0.0001
    return lat+radius, lng+radius

def get_name():
    return f'{random.choice(last_name)}{"".join(random.sample(name_first, 2))}'

def getCards():

    with conn.cursor() as cur:
        cur.execute(" select b.mbr_card_no "+
                    " from mbr_info a "+
                    " inner join mbr_card_isu_info b "+
                    " on a.mbr_id = b.mbr_id "+
                    " where b.card_stus_cd = '01'")
        return cur.fetchall()


def getCrgrs(chrstn_id = None):

    with conn.cursor() as cur:
        sql = " select b.crgr_cid " \
              " from crgr_mstr_info a " \
              " inner join crgr_info b " \
              " on a.crgr_mid = b.crgr_mid " \
              " where a.crgr_stus_cd = '04' and b.crgr_cid like '%A'"

        if chrstn_id :
            sql = sql + f" and a.chrstn_id = '{chrstn_id}' "
        cur.execute(sql)

        return cur.fetchall()

def getMaxChrstn(region):

    with conn.cursor() as cur:
        sql = f" select max(chrstn_id) " \
              " from chrstn_info " \
              f" where chrstn_id like '{region}%' "
        cur.execute(sql)
        if cur.row_count() > 0:
            return cur.fetchall()[0]
        else:
            return 0

def getMCrgrs(chrstn_id = None):

    with conn.cursor() as cur:
        sql = " select crgr_mid " \
              " from crgr_mstr_info "

        if chrstn_id :
            sql = sql + f" where chrstn_id = '{chrstn_id}' "
        cur.execute(sql)

        return cur.fetchall()

def createCrgrMsts(chrstn_id = "115000001"):
    existCrgrMsts = [crgr[0] for crgr in getMCrgrs(chrstn_id)]
    # print(existCrgrMsts)
    # print(set([chrstn_id+'{0:02d}'.format(i) for i in range(1,100)]) - set(existCrgrMsts))

    with conn.cursor() as cur:
        for crgr in list(set([chrstn_id+'{0:02d}'.format(i) for i in range(1,100)]) - set(existCrgrMsts)):
            cur.execute(f" insert into crgr_mstr_info(chrstn_id, crgr_mid, crgr_stus_cd, etfn_chrg_crgd_yn) \
            values('{chrstn_id}', '{crgr}', '04', 'Y')")

def createCrgrs(chrstn_id = "115000001"):

    with conn.cursor() as cur:
        for crgr in list(set([chrstn_id+'{0:02d}'.format(i) for i in range(1,100)])):
            cur.execute(f" insert into crgr_info(crgr_mid, crgr_cid, chrstn_id, me_crgr_id, crgr_open_yn) \
            values('{crgr}', '{crgr+['0A','0B','0C'][random.randrange(0,3)]}', '{chrstn_id}', '{crgr[9:]}', 'Y' )")

def createChrstns(region, count):
    import fileinput as f
    ilen = len(region)
    region_juso = None
    with open("서울특별시_주소_위치300000-310000.csv", "r", encoding='utf-8') as f:
        alljuso = [j.split(sep=",") for j in f.readlines() ]
        region_juso = [j for j in alljuso if j[2][0:ilen]==region]
    print(len(region_juso))
    print(random.sample(region_juso, count))
    with conn.cursor() as cur:
        for chrstn_id in list(set([region+'{0:06d}'.format(i) for i in range(start,end)])):
            lat, lot = get_lat_lng()
            cur.execute(f" insert into chrstn_info(chrstn_id, me_chrstn_id, chrstn_nm, chrstn_oprn_stus_cd, \
            chrstn_rcpt_path_cd, aplc_nm, aplc_hpno, aplc_emal_addr, cust_kd_cd, cust_detl_kd_cd, lat, lot) \
            values('{chrstn_id}', '{chrstn_id[3:]}', '충전소_{chrstn_id}', '{['04','05'][random.randrange(0,2)]}',\
             '01', '안창선', '01023023866', 'changsan@lgcns.com', '01', '01', {lat}, {lot} )")

def createRegionChrstns(start, end):

    # 충전소 생성, 충전기 생성(M/C)

    for i in tqdm(range(start,end)):
        evlogger.info(f"충전소/충전기 생성 중: {i}")
        # createChrstns(str(i), 1, 100)
        for j in tqdm(range(1,100)):
            # createCrgrMsts(chrstn_id = f'{i:03d}{j:06d}')
            createCrgrs(chrstn_id = f'{i:03d}{j:06d}')

        conn.commit()

def createMember(member = "cust01"):

    with conn.cursor() as cur:
        cur.execute(f" insert into mbr_info(mbr_id, mbr_stus_cd, mbr_nm, indv_id, lgin_mthd_cd, pswd, hpno, emal_addr, \
        mbr_divs_cd, rep_cars_no, mbsp_grd_cd ) \
        values('{member}', '01', '홍길동', '{member}', '01', 'e52e5b9c1e8c3356d2baa451511131818cbc06e949213b6e4f49cd3589e86712', \
        '01011223344', 'hong@gmail.com', '01', '서울48로2424', '00' )")

def createMemberEtc(member = "cust01"):

    with conn.cursor() as cur:
        cur.execute(f" insert into mbr_etc_info(mbr_id, pp_entr_yn, pp_kd_cd, pp_sno) \
        values('{member}', 'N', '01', 1,)")

def createCards(member = "cust01", card = "0000000000000000", sno=0):

    with conn.cursor() as cur:
        cur.execute(f" insert into mbr_card_isu_info(mbr_id, mbr_card_sno, mbr_card_no, grp_card_yn, card_isu_divs_cd, \
        card_stus_cd, aprv_yn_cd, rcip_nm, zpcd, send_stus_cd ) \
        values('{member}', '{sno}', '{card}', 'N', '01', \
        '01', 'Y', '{get_name()}', '12345', '01') ")

def createMbrStlm(member = "cust01"):
    with conn.cursor() as cur:
        for j in range(1,2):
            cur.execute(f" insert into mbr_stlm_card_info(mbr_id, tos_key, brand_pay_yn, card_divs_cd, rep_stlm_card_yn, \
            stop_yn, poca_asgn_yn ) \
            values('{member}', 'HWSxOqggbb6Hlrb4GiMx', 'Y', '01', 'Y', \
            'N', 'Y') ")

def getMemberInfo():
    stlm = {"brand_pay_yn":['Y', 'N'], "rep_stlm_card_yn":['Y', 'N'], "stop_yn":['Y', 'N'], "poca_asgn_yn":['Y','N']}
    etc = {"pp_entr_yn":['Y','N'], "pp_kd_cd":['01','02'], "pp_sno":1}


def createMbrAndCards(start, end):

    # 충전소 생성, 충전기 생성(M/C)

    for i in tqdm(range(start,end)):
        evlogger.info(f"회원 및 회원카드 생성: {i}")
        createMember(f"cust{str(i)}")
        createMemberEtc(f"cust{str(i)}")
        for j in range(1,2):
            createCards(member = f"cust{str(i)}", card = f'4{random.randrange(100000000000000,999999999999999)}', sno=j)

        conn.commit()

def addr_to_lat_lon(addr):
    def get_lat_lon(addr):
        url = 'https://dapi.kakao.com/v2/local/search/address.json?query={address}'.format(address=addr)
        headers = {"Authorization": "KakaoAK " + "b0435a9866eb210ded83544abae27f26"}
        result = json.loads(str(requests.get(url, headers=headers).text))
        return result
    res = get_lat_lon(addr)
    if len(res['documents'])==0:
        res = get_lat_lon(" ".join(addr.split(" ")[:-1]))

    match_first = res['documents'][0]['address']
    if match_first :
        return float(match_first['x']), float(match_first['y'])
    else:
        return ("","")


address = None

def convert_address(filename=None):
    import pandas as pd
    csv = pd.read_table(filename, sep="|")
    start = 340_000
    end = 360_000
    csv = csv[start:end]
    csv.astype(str)

    address = csv['시도']+" "+csv['시군구']+" "+csv['도로명']+" "+csv['건물번호본번'].astype(str)
    # 위도, 경도 반환하는 함수
    def geocoding(address):

        return addr_to_lat_lon(address)


    #####주소를 위,경도 값으로 변환하기 #####
    latitude = []
    longitude =[]

    for i in tqdm(address):
        geo = geocoding(i)
        time.sleep(0.001)
        latitude.append(geo[0])
        longitude.append(geo[1])

    print(len(address), len(latitude), len(longitude))
    #####Dataframe만들기######
    address_df = pd.DataFrame({'우편번호': csv["우편번호"], '주소':address, '법정동코드':csv['법정동코드'], '건물명':csv['시군구용건물명'], '위도':latitude,'경도':longitude})

    #df저장
    address_df.to_csv(f'서울특별시_주소_위치{start}-{end}.csv', index=False)


if __name__ == "__main__":

    # convert_address("po/서울특별시.txt")
    createChrstns("1165", 10)
    # conn = getConnection()
    #
    # # createRegionChrstns(117, 118)
    # createMbrAndCards(1,100)
    # conn.close()
