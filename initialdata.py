import random
from tqdm import tqdm
from evlogger import Logger
import logging

logger = Logger()
global evlogger
evlogger = logger.initLogger(loglevel=logging.DEBUG)

def getConnection():
    import pymysql
    conn = pymysql.connect(host="rds-aurora-mysql-ev-charger-svc-instance-0.cnjsh2ose5fj.ap-northeast-2.rds.amazonaws.com",
                           user='evsp_usr', password='evspuser!!', db='evsp', charset='utf8', port=3306)

    return conn

lat_c , lng_c = 37.561253, 126.834329

def get_lat_lng(lat=37.561253, lng=126.834329):
    radius = random.randrange(1,1000)*0.0001
    return lat+radius, lng+radius


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

def createChrstns(region, start, end):

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
        '01011223344', 'hong@gmail.com', '01', '서울48로2424', '01' )")

def createCards(member = "cust01", card = "0000000000000000", sno=0):

    with conn.cursor() as cur:
        cur.execute(f" insert into mbr_card_isu_info(mbr_id, mbr_card_sno, mbr_card_no, grp_card_yn, card_isu_divs_cd, \
        card_stus_cd, aprv_yn_cd, rcip_nm, zpcd, send_stus_cd ) \
        values('{member}', '{sno}', '{card}', 'N', '01', \
        '01', 'Y', '홍길동', '12345', '01') ")

def createMbrAndCards(start, end):

    # 충전소 생성, 충전기 생성(M/C)

    for i in tqdm(range(start,end)):
        evlogger.info(f"회원 및 회원카드 생성: {i}")
        createMember(f"cust{str(i)}")
        for j in range(1,4):
            createCards(member = f"cust{str(i)}", card = random.randrange(1000000000000000,9999999999999999), sno=j)

        conn.commit()

if __name__ == "__main__":
    conn = getConnection()

    # createRegionChrstns(117, 118)
    createMbrAndCards(1,100)
    conn.close()
