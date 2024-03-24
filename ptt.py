from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import tools
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

target_box =["pchome","momo"]  # PTT搜索版爬蟲的目標
for search_target in target_box:
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("headless")  # 無痕 incognito 無頭 headless
    driver = webdriver.Chrome(service=service, options=options)
    
    page_count_max = None
    page = 1
    url_box = set()
   
    driver.get(f"https://www.pttweb.cc/ptt-search#gsc.tab=0&gsc.q={search_target}&gsc.sort=&gsc.page=1")
    time.sleep(5)  # 等待頁面加載

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.find_all('a', attrs={'data-ctorig': True})
    page_counts = soup.find_all('div', {'class': 'gsc-cursor-page'})

    for article in articles:
        article_url = article['data-ctorig']
        if article_url not in url_box:
            url_box.add(article_url)

    if page_counts:
        page_count_max = int(page_counts[-1].text)

    # -------------如果存在多頁，則迴圈瀏覽每一頁獲取網址--------------
    if page_count_max:
        for page_addr in range(2, page_count_max + 1):   # page_count_max + 1
            driver.get(f"https://www.pttweb.cc/ptt-search#gsc.tab=0&gsc.q={search_target}&gsc.sort=&gsc.page={page_addr}")
            time.sleep(3)  # 等待頁面加載
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            articles = soup.find_all('a', attrs={'data-ctorig': True})

            for article in articles:
                article_url = article['data-ctorig']
                if article_url not in url_box:
                    url_box.add(article_url)

    #-----------------------訪問爬取到的網址-----------------------------------------------------------------
    previous_user = None
    previous_user_text = ""
    for url in url_box:
        print("搜尋目標:",search_target,",網址:",url)
        driver.get(url)
    
        # 使用 WebDriverWait 等待頁面加載完成
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 安全地檢查是否存在年齡確認按鈕
        buttons_18x = driver.find_elements(By.CLASS_NAME, 'btn-big')
        if buttons_18x:
            # 假設按鈕存在，點擊按鈕
            buttons_18x[0].click()
            # 等待跳轉後的頁面加載完成
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            #跳轉後再次獲得頁面資訊
            soup = BeautifulSoup(driver.page_source, 'html.parser')
    
        # ------------------進入網頁後往下滾動讀取---------------------------------
        for x in range(1, 3):
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(2)
    
        #------------------------------找出文章標題-----------------------------------------
        metalines = soup.find_all('div', class_='article-metaline')

        # 選擇第二個 metaline div（索引為 1，因為索引從 0 開始）
        second_metaline = metalines[1] if len(metalines) > 1 else None

        #獲取文章標題
        if second_metaline:
            title = second_metaline.find('span', class_='article-meta-value').text
    
        #-----------------找出文章底下的留言-------------------------------------------------
        pushs = soup.find_all('div',{'class':'push'})
        previous_user = None       #上一個使用者的id
        previous_user_text = ""  #上一個使用者的text
        for push in pushs:
            #獲取此文本的使用者
            push_userid = push.find('span', {'class': 'f3 hl push-userid'})
            if push_userid:
                userid = push_userid.text
                # 对于每个 push，找到其内部的 push-content span
            
                push_content = push.find('span', {'class': 'f3 push-content'})
                if push_content:  # 确保找到了 push-content
                    content =push_content.text.strip(': ')#去除字串:跟空格
                
                    if userid == previous_user:
                        previous_user_text += " " + content
                    else:
                        # 當前用戶與上一個不同,先儲存資料再將現在的使用者資料放入previous變數
                        if previous_user is not None:
                            #文本進行情緒分析
                            text_sentiment = tools.analyze_sentiment_auto(previous_user_text)

                            #使用者id加上使用者po文,轉換成hash值
                            text_hash = tools.compute_hash(userid + previous_user_text)
                        
                        # 檢查文本是否重複並寫入為寫入的資料
                            tools.check_hash_and_insert_DB(search_target, title, previous_user_text, text_sentiment, text_hash)
                        
                        #寫入文件
                            tools.insert_intoJSON(search_target,title, previous_user_text, text_sentiment, text_hash)

                        previous_user = userid
                        previous_user_text = content
        # 循環結束後處理最後一個抓取的使用者的資料
        if previous_user is not None:
            text_sentiment = tools.analyze_sentiment_auto(previous_user_text)
            text_hash = tools.compute_hash(userid+previous_user_text)
            tools.check_hash_and_insert_DB(search_target,title, previous_user_text, text_sentiment, text_hash)
            tools.insert_intoJSON(search_target,title, previous_user_text, text_sentiment, text_hash)
    driver.quit()
    time.sleep(3)