import random
from evlogger import Logger
import logging
import time, json, datetime
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

last_name = ['김','이', '박', '최', '안', '장', '윤','구','차', '정','주','진', '추','임','강']
name_first = ['주', '하', '창', '희', '수', '경', '혜', '지', '서', '현', '주', '진', '광', \
              '천', '선', '경','철', '영', '기', '정', '우', '도', '윤', '강', '성', '중', '나', '용','이']

alljuso = None
with open("서울특별시_변환완료.csv", "r", encoding='utf-8') as f:
    alljuso = [j.strip().split(sep=",") for j in f.readlines()]

def get_lat_lng(lat=37.561253, lng=126.834329):
    radius = random.randrange(1,1000)*0.0001
    return lat+radius, lng+radius

def get_name():
    return f'{random.choice(last_name)}{"".join(random.sample(name_first, 2))}'

def get_car_no():
    return f"{random.randrange(111,999)}{random.choice(['가','나','다','라,','마','수'])}{random.randrange(1111,9999)}"

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

def getMaxChrstn(region):

    with conn.cursor() as cur:
        sql = f" select max(chrstn_id) " \
              " from chrstn_info " \
              f" where chrstn_id like '{region}%' "
        cur.execute(sql)

        result = cur.fetchone()

        if result[0] == None:
            return 0
        else:
            return int(result[0])

def get_eng_names():
    from urllib.request import Request, urlopen
    # url="https://svnweb.freebsd.org/csrg/share/dict/words?revision=61569&view=co"
    # req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    #
    # web_byte = urlopen(req).read()

    words = [line.rstrip() for line in open("words.txt").readlines()]
    random.shuffle(words)

    return words

eng_names = get_eng_names()

def get_tel_no():
    return f"010{random.randrange(10000000, 99999999)}"

def get_email():
    return random.choice(eng_names)+"@gmail.com"

def createChrstns(filename, region, chrstn_count=0, crgr_count=0):

    with open(filename, "r", encoding='utf-8') as f:
        alljuso = [j.strip().split(sep=",") for j in f.readlines()]

    max_seq = getMaxChrstn(region)%10000 ## 수정해야 함(지역별 최대 충전소 시퀀스)
    region_juso = [j for j in alljuso if j[2].startswith(region)]
    """region_juso 요소
        [0] 우편번호
        [1] 주소명(Fullname)
        [2] 법정동코드
        [3] 건물명
        [4] 위도
        [5] 경도
    """

    chrs = random.sample(region_juso, chrstn_count)
    print(f'{region}지역 {chrstn_count}개 충전소별 {crgr_count}개의 충전기 등록')
    with conn.cursor() as cur:
        for chr in tqdm(chrs):
            lat, lot = chr[4], chr[5]
            max_seq += 1
            chrstn = f'{chr[2][0:5]}{max_seq:04}'
            juso = chr[1].split()

            sql = f" insert into chrstn_info(chrstn_id, me_chrstn_id, chrstn_nm, chrstn_oprn_stus_cd, \
            cust_nm, area_ctdo, area_ccw, zpcd, badr, dadr, \
            chrstn_rcpt_path_cd, aplc_nm, aplc_hpno, aplc_emal_addr, cust_kd_cd, cust_detl_kd_cd, lat, lot, opn_stle_cd) \
            values('{chrstn}', '{chrstn[4:]:06}', 'U+{chr[3]}충전소', '{['04','05'][random.randrange(0,2)]}',\
            '{get_name()}', '{chrstn[0:2]}', '{chrstn[0:5]}', '{chr[0]}', '{chr[1]}', '{chr[1]}', \
             '01', '{get_name()}', '{get_tel_no()}', '{get_email()}', '01', '01', '{lot}', '{lat}', '02' )"
            cur.execute(sql)
            createCntcInfo(chrstn_id=chrstn)
            connector = random.choice(['A', 'C'])
            createCrgrMsts(chrstn_id=chrstn, crgr_count=crgr_count, connector=connector)
            createCrgrs(chrstn_id = chrstn, crgr_count=crgr_count, connector=connector)
        conn.commit()

def createCntcInfo(chrstn_id = "115000001"):
    """충전소 계약정보 등록
    """
    with conn.cursor() as cur:
        cur.execute(f" insert into chrstn_cntc_info(chrstn_id, cntc_sno, cntc_pgrs_stus_cd, chrstn_rcpt_path_cd,"
                    f" estb_rqst_rcpt_no, cntc_divs_cd, invt_divs_cd, cntc_dt, cntc_strt_dt, cntc_end_dt ) "
                    f" values ( '{chrstn_id}', 1, '01', '01',"
                    f" '{datetime.datetime.now().strftime('%Y%m%d')}001', '01', '01', '{datetime.datetime.now().isoformat()}', "
                    f" '{datetime.datetime.now().isoformat()}', '{datetime.datetime.now().isoformat()}' ) ")

def createCrgrMsts(chrstn_id = "115000001", crgr_count=1, connector="A"):
    existCrgrMsts = [crgr[0] for crgr in getMCrgrs(chrstn_id)]
    # print(existCrgrMsts)
    # print(set([chrstn_id+'{0:02d}'.format(i) for i in range(1,100)]) - set(existCrgrMsts))

    with conn.cursor() as cur:
        for idx, crgr in enumerate(list(set([chrstn_id+'{0:02d}'.format(i) for i in range(1,crgr_count)])
                                        - set(existCrgrMsts))):
            reserved = ((idx%2)==0)
            cur.execute(f" insert into crgr_mstr_info(chrstn_id, crgr_mid, crgr_stus_cd, etfn_chrg_crgd_yn, estb_year, "
                        f" estb_mm, lte_rotr_entityid, crgr_rsv_mode_cd, chrg_divs_cd  ) " 
                        f" values('{chrstn_id}', '{crgr}', '04', 'Y', '2022', '06', "
                        f" 'ASN_CSE-D-{random.randrange(111111111,999999999)}d-EVSP', "
                        f" {'02' if reserved else '01'}, '{connector}' )")


def createCrgrs(chrstn_id = "115000001", crgr_count=0, connector="A"):

    with conn.cursor() as cur:
        for idx, crgr in enumerate(list(set([chrstn_id+'{0:02d}'.format(i) for i in range(1,crgr_count)]))):
            reserved = ((idx%2)==0)
            cntr = "0"+connector
            cur.execute(f" insert into crgr_info(crgr_mid, crgr_cid, chrstn_id, me_crgr_id, crgr_open_yn) \
            values('{crgr}', '{crgr+cntr}', '{chrstn_id}', '{crgr[9:]}', 'Y')")

            if reserved :
                cur.execute(f" insert into rsv_crgr_choc_info(rsv_plcy_uuid, crgr_cid) "                
                            f" values('1, {crgr}', '{crgr + cntr}' )")


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
        juso = [random.choice(alljuso)][0]
        juso_adr = juso[1].split()
        cur.execute(f" insert into mbr_info(mbr_id, mbr_stus_cd, mbr_nm, indv_id, lgin_mthd_cd, pswd, emal_addr, \
        mbr_divs_cd, mbsp_grd_cd ,zpcd, badr, dadr, hpno, area_ctdo, area_ccw, reg_dttm ) \
        values('{member}', '01', '{get_name()}', '{member}', '01', \
        '48000d754ed116dfc5719bf5b037dd7245fc9272b822f68c892a1ef30d37079b', \
        '{get_email()}', '01', '00', '{juso[0]}', '{juso[1]}', \
        '{juso[1]}', '{get_tel_no()}', '{juso_adr[0]}', '{juso_adr[1]}', '{datetime.datetime.now()}')")


def createMemberEtc(member = "cust01"):
    """요금제 : 고정요금제 기준
        - aply_chrg_nm : '고정요금제'
        - aply_chrg_grd : 1
        - aply_chrg : 300 (kw당 요금(원))
    """
    with conn.cursor() as cur:
        cur.execute(f" insert into mbr_etc_info(mbr_id, stlm_mthd_cd, toss_blng_key, pp_entr_yn, pp_kd_cd, pp_uuid, \
        pp_sno, pp_divs_cd, chrg_aply_divs_cd, aply_chrg_base_cd, sscb_chrg_exmt_yn, aply_chrg_nm, aply_chrg_grd, aply_chrg ) \
        values('{member}', '01', 'TOSS_BLING_KEY', 'N', '01', 1, 1, '01', '01', '01', 'Y', '고정요금제', 300, 300 )")

def createCards(member = "cust01", card = "0000000000000000", sno=0):

    with conn.cursor() as cur:

        cur.execute(f" insert into mbr_card_isu_info(mbr_id, mbr_card_sno, mbr_card_no, grp_card_yn, card_isu_divs_cd, \
        card_stus_cd, aprv_yn_cd, rcip_nm,  send_stus_cd ) \
        values('{member}', '{sno}', '{card}', 'N', '01', \
        '01', 'Y', '{get_name()}',  '01') ")

def createMbrStlm(member = "cust01"):
    with conn.cursor() as cur:
        for j in range(1,2):
            cur.execute(f" insert into mbr_stlm_card_info(mbr_id, toss_key, card_divs_cd, rep_stlm_card_yn, \
            ccrd_cmpy_nm, cdco_cd, card_no, card_nm, card_id, card_kd, ownr_kd, stop_yn, poca_asgn_yn ) \
            values('{member}', 'HWSxOqggbb6Hlrb4GiMx', '01', 'Y', \
            '롯데', '51', '513223******4432', '롯데카드', 'c_213123j3jk23jk2k', '신용', '개인', 'N', 'Y') ")

def createMbrAndCards(start, end):

    # 충전소 생성, 충전기 생성(M/C)

    for i in tqdm(range(start,end)):
        evlogger.info(f"회원 및 회원카드 생성: {i}")
        member_id = f"{random.choice(eng_names).lower()}{random.randrange(1,99)}@voltup.com"
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
    slice_from, slice_to = 0, 1_000_000
    csv = csv[slice_from:slice_to]

    del_idx = csv[csv['시군구용건물명'].isnull()].index
    csv = csv.drop(del_idx)
    #print(csv['시군구용건물명'])
    address = csv['시도']+" "+csv['시군구']+" "+csv['도로명']+" "+csv['건물번호본번']

    manager = multiprocessing.Manager()
    lat = manager.list()
    lng = manager.list()

    with Pool(processes=2) as p:
        max_ = len(address)
        with tqdm(total=max_) as pbar:
            # for i, _ in enumerate(p.imap_unordered(geocoding, [(lat, lng, i) for i in address])):
            for i, _ in enumerate(p.imap(geocoding, [(lat, lng, i) for i in address])):
                pbar.update()

    address_df = pd.DataFrame({'우편번호': csv["우편번호"].astype(str), '주소':address, '법정동코드':csv['법정동코드'],
                               '건물명':csv['시군구용건물명'], '위도':list(lat), '경도':list(lng)})

    address_df.to_csv(f'{filename}_변환완료{slice_from}-{slice_to}.csv', index=False)


if __name__ == "__main__":

    conn = getConnection()
    # convert_address("po/강원도.txt")

    # createChrstns("충청북도_변환완료.csv", "43", chrstn_count=1000, crgr_count=10)
    createChrstns("서울특별시_변환완료.csv", "1126", chrstn_count=1, crgr_count=10)
    # createChrstns("충청남도_변환완료.csv", "44", chrstn_count=1000, crgr_count=10)
    # createChrstns("경기도_변환완료.csv", "414", chrstn_count=100, crgr_count=10)
    # createChrstns("강원도_변환완료.csv", "42", chrstn_count=1000, crgr_count=20)
    #
    # createRegionChrstns(112, 118)
    # createMbrAndCards(1,1000)
    conn.close()