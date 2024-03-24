from snownlp import SnowNLP
import pymysql
import json
import hashlib
import os
from dotenv import load_dotenv

#情緒分析
def analyze_sentiment_auto(text, length_threshold=200):
    """
    自動根據文本長度判斷是否需要分句進行情緒分析。
    
    :param text: 需要分析的文本
    :param length_threshold: 決定是否分句的文本長度閾值,默认為200個字符
    :return: 文本的情緒分數,值越接近1表示情緒越正面,越接近0表示情緒越負面。
    """
    if not text.strip():
       
        return 0.5
    else:
        if len(text) > length_threshold:
            # 文本較長，分句進行分析
            sentences = SnowNLP(text).sentences
            sentiments = [SnowNLP(sentence).sentiments for sentence in sentences]
            sentiment_score = sum(sentiments) / len(sentiments) if sentiments else 0.5
        else:
            # 文本較短，直接分析整個文本
            sentiment_score = SnowNLP(text).sentiments
        return sentiment_score


#寫入JSON檔
def insert_intoJSON(search_target,title, previous_user_text, text_sentiment, text_hash):
    masage_box ={"search_target":search_target,'Title':title,'text':previous_user_text,'sentiment':text_sentiment,'hash':text_hash}
    with open('backup.json','a') as file:
        json.dump(masage_box,file,ensure_ascii=False)
        file.write('\n')

#使用者+留言轉換成hash
def compute_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

#hash檢查重複文章
load_dotenv("your env path")
sql_user = os.getenv('SQL_USER')
sql_password = os.getenv('SQL_PASSWORD')

def check_hash_and_insert_DB(search_target,title, previous_user_text, text_sentiment, text_hash):
    db = pymysql.connect(host='localhost', user=sql_user, password=sql_password, database='name')
    cursor = db.cursor()
    sql_check = "SELECT COUNT(*) FROM ptt_get WHERE hash = (%s)"
    cursor.execute(sql_check, text_hash)
    result = cursor.fetchone()
    if result[0] == 0:
        sql = "INSERT INTO ptt_get (name, title, text, sentiment, hash) VALUES (%s, %s, %s, %s, %s)"
        val = (search_target,title, previous_user_text, text_sentiment, text_hash)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        # print("DB_success!!!!!")
    else:
        print("資料重複,略過寫入資料庫")
    db.close()