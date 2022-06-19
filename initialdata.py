import concurrent.futures
import random
import string

from evlogger import Logger
import logging
import time, json, requests
from tqdm import tqdm
import multiprocessing
from multiprocessing import Pool

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

def getMaxChrstn(region):

    with conn.cursor() as cur:
        sql = f" select max(chrstn_id) " \
              " from chrstn_info " \
              f" where chrstn_id like '{region}%' "
        cur.execute(sql)
        if cur.row_count() > 0:
            return int(cur.fetchall()[0])
        else:
            return 0

def get_tel_no():
    return f"010{random.randrange(10000000, 99999999)}"

def get_email():
    return f"{random.choices(string.ascii_lowercase, 8)}"

def createChrstns(region, count):

    ilen = len(region)

    max_seq = 0 ## 수정해야 함
    region_juso = None
    with open("서울특별시_주소_위치300000-310000.csv", "r", encoding='utf-8') as f:
        alljuso = [j.split(sep=",") for j in f.readlines() ]
        region_juso = [j for j in alljuso if j[2][0:ilen]==region]
    """region_juso 요소
        [0] 우편번호
        [1] 주소명(Fullname)
        [2] 법정동코드
        [3] 건물명
        [4] 위도
        [5] 경도
    """
    chrs = random.sample(region_juso, count)
    with conn.cursor() as cur:
        for chr in chrs:
            lat, lot = get_lat_lng()
            max_seq += 1
            chrstn = f'{chr[2][0:5]}{max_seq:04}'
            cur.execute(f" insert into chrstn_info(chrstn_id, me_chrstn_id, chrstn_nm, chrstn_oprn_stus_cd, \
            chrstn_rcpt_path_cd, aplc_nm, aplc_hpno, aplc_emal_addr, cust_kd_cd, cust_detl_kd_cd, lat, lot) \
            values('{chrstn}', '{chrstn[3:]}', 'U+{chrs[3]}충전소', '{['04','05'][random.randrange(0,2)]}',\
             '01', '{get_name()}', '010{get_tel_no()}', '{get_email()}', '01', '01', {lat}, {lot} )")

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
        member_id = f"cust01{str(i)}"
        createMember(member= member_id)
        createMemberEtc(member= member_id)
        createMbrStlm(member=member_id)
        for j in range(1,2):
            createCards(member = member_id, card = f'4{random.randrange(100000000000000,999999999999999)}', sno=j)

        conn.commit()

def addr_to_lat_lon(addr):
    def get_lat_lon(addr):
        # 카카오
        # url = 'https://dapi.kakao.com/v2/local/search/address.json?query={address}'.format(address=addr)
        # headers = {"Authorization": "KakaoAK " + "b0435a9866eb210ded83544abae27f26"}
        # result = json.loads(str(requests.get(url, headers=headers).text))

        # result = json.load(str(requests.get(url, headers=headers).text))
        # print(result)
        # return result


        # 네이버
        #import urllib3 import parser
        import requests
        url = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={addr}'
        url_only = 'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode'
        headers = {'X-NCP-APIGW-API-KEY-ID':'bo9tbmia4k', 'X-NCP-APIGW-API-KEY':'oOGw0S6lI6ktapAFtHIgOFZSTNQ2pLaME1KNPM6g' }

        result = "", ""
        result_dict = None

        time.sleep(0.001)
        try :
            response = requests.get(url, headers=headers)
        except:
            from urllib.request import urlopen
            import urllib.request

            values ={'query':f'{addr}'}
            data = urllib.parse.urlencode(values).encode('utf-8')
            req = urllib.request.Request(url_only, data, headers)
            page = urlopen(req)

            doc = page.read().decode('utf-8')
            dic = json.loads(doc)
            result_dict = dic['addresses']

            result = result_dict[0]["x"], result_dict[0]["y"]
        else:
            if response.status_code == 200:
                response = json.loads(response.text)
                if "addresses" in response :
                    result_dict = response["addresses"]
                    if len(result_dict) > 0 :
                        result = result_dict[0]["x"], result_dict[0]["y"]
        return result

    return get_lat_lon(addr)

    # kakao
    # res = get_lat_lon(addr)
    # print(res)
    # time.sleep(0.001)
    # if len(res['documents'])==0:
    #     res = get_lat_lon(" ".join(addr.split(" ")[:-1]))
    #
    # match_first = res['documents'][0]['addreses']
    #
    # if match_first :
    #     return float(match_first['x']), float(match_first['y'])
    # else:
    #     return ("","")

#  AIzaSyDHfne4oASn_mSo5jLx60HN-3nPNmwYJVs

def geocoding(param):
    x, y = addr_to_lat_lon(param[2])
    param[0].append(x)
    param[1].append(y)

def convert_address(filename=None):
    import pandas as pd
    csv = pd.read_table(filename, sep="|", dtype={"우편번호": str, "건물번호본번":str})
    slice_from, slice_to = 290_000, 300_000
    csv = csv[slice_from:slice_to]

    address = csv['시도']+" "+csv['시군구']+" "+csv['도로명']+" "+csv['건물번호본번']

    manager = multiprocessing.Manager()
    lat = manager.list()
    lng = manager.list()


    with Pool(processes=4) as p:
        max_ = len(address)
        with tqdm(total=max_) as pbar:
            # for i, _ in enumerate(p.imap_unordered(geocoding, [(lat, lng, i) for i in address])):
            for i, _ in enumerate(p.imap(geocoding, [(lat, lng, i) for i in address])):
                pbar.update()


    address_df = pd.DataFrame({'우편번호': csv["우편번호"].astype(str), '주소':address, '법정동코드':csv['법정동코드'],
                               '건물명':csv['시군구용건물명'], '위도':list(lat), '경도':list(lng)})

    address_df.to_csv(f'{filename}_변환완료{slice_from}-{slice_to}.csv', index=False)


if __name__ == "__main__":

    convert_address("po/서울특별시.txt")
    # createChrstns("1165", 2)
    # conn = getConnection()
    #
    # # createRegionChrstns(117, 118)
    # createMbrAndCards(1,100)
    # conn.close()
