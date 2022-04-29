import configparser
import time
import os
import sys
import errno
import datetime
import json

sys.path.append(os.path.join(os.path.dirname(__file__), './lib'))

from selenium import webdriver
from selenium.webdriver.chrome import service as fs
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_binary


config_ini = configparser.ConfigParser()
config_ini_path = "config.ini"

def main():
    """
    参加表明ボタン連打用
    指定時刻までボタンを連打します。
    """
    # 変数初期化
    current = datetime.datetime.now().strftime("%y/%m")

    # 設定ファイル存在チェック
    if not os.path.exists(config_ini_path):
        # 存在しない場合はエラーで終了
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)

    # 設定ファイル読み込み
    config_ini.read(config_ini_path, encoding='utf-8')

    # 定数取得
    mail = config_ini['DEFAULT']['Mail']
    password = config_ini['DEFAULT']['Password']
    login = config_ini['DEFAULT']['Login']
    entry = config_ini['DEFAULT']['Entry']
    event_name = config_ini['DEFAULT']['EventName']
    event_date = config_ini['DEFAULT']['EventDate']
    format_ini = config_ini['DEFAULT']['Format']
    reception_date = config_ini['DEFAULT']['ReceptionDate']
    search  = config_ini['DEFAULT']['Search']
    
    local_list = {
        # 北海道・東北
        "tohoku": ["PrefCheckbox1", "PrefCheckbox2", "PrefCheckbox3", "PrefCheckbox4", "PrefCheckbox5", "PrefCheckbox6", "PrefCheckbox7"],
        # 関東
        "kanto": ["PrefCheckbox8", "PrefCheckbox9", "PrefCheckbox10", "PrefCheckbox11", "PrefCheckbox12", "PrefCheckbox13", "PrefCheckbox14"],
        # 中部
        "tyubu": ["PrefCheckbox15", "PrefCheckbox16", "PrefCheckbox17", "PrefCheckbox18", "PrefCheckbox19", "PrefCheckbox20", "PrefCheckbox21", "PrefCheckbox22", "PrefCheckbox23"],
        # 近畿
        "kinki": ["PrefCheckbox24", "PrefCheckbox25", "PrefCheckbox26", "PrefCheckbox27", "PrefCheckbox28", "PrefCheckbox29", "PrefCheckbox30"],
        # 中国
        "tyugoku": ["PrefCheckbox31", "PrefCheckbox32", "PrefCheckbox33", "PrefCheckbox34", "PrefCheckbox35"],
        # 四国
        "shikoku": ["PrefCheckbox36", "PrefCheckbox37", "PrefCheckbox38", "PrefCheckbox39"],
        # 九州
        "kyusyu": ["PrefCheckbox40", "PrefCheckbox41", "PrefCheckbox42", "PrefCheckbox43", "PrefCheckbox44", "PrefCheckbox45", "PrefCheckbox46", "PrefCheckbox47"],
    }

    options = Options()
    options.add_argument('--headless')

    for prefecture_key in local_list.keys():
        result = {}
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        
        # DMPランキングページに遷移
        driver.get("https://www.dmp-ranking.com/login.asp")
        
        # 認証情報入力
        # メールアドレス入力
        driver.find_element(by=By.NAME, value="Mail").send_keys(mail)
        # パスワードを入力
        driver.find_element(by=By.NAME, value="Password").send_keys(password)
        # ログインボタン押下
        driver.find_element(by=By.CSS_SELECTOR, value=login).click()

        # スケジュールページに遷移
        driver.get("https://www.dmp-ranking.com/schedule.asp")
    
        driver.find_element(by=By.XPATH, value='//*[@id="PrefCheckboxLayerButton"]').click()
        for prefecture_item in local_list[prefecture_key]:
            driver.find_element(by=By.ID, value=prefecture_item).click()
        driver.find_element(by=By.XPATH, value=search).click()
        
        for i in range(1, len(driver.find_element(by=By.ID, value="main").find_elements(by=By.TAG_NAME, value="tr"))):
            item = {}
            prefecture = driver.find_element(by=By.ID, value="main").find_elements(by=By.TAG_NAME, value="tr")[i].find_elements(by=By.TAG_NAME, value="td")[2].text
            if "リモート" in prefecture:
                continue
            
            driver.find_element(by=By.ID, value="main").find_elements(by=By.TAG_NAME, value="tr")[i].click()
            item_reception_date = driver.find_element(by=By.XPATH, value=reception_date).text
            if item_reception_date != "※参加を希望される方は必ず参加表明を行ってください":
                reception_datetime = datetime.datetime.strptime(item_reception_date.split(" ")[1] + " " + item_reception_date.split(" ")[2], "%Y/%m/%d %H:%M")
                
                item = {
                    "url": driver.current_url,
                    "prefecture": prefecture,
                    "event_name": driver.find_element(by=By.XPATH, value=event_name).text,
                    "event_date": driver.find_element(by=By.XPATH, value=event_date).text.split("：")[1],
                    "format": driver.find_element(by=By.XPATH, value=format_ini).text.split("：")[1],
                    "reception_date": reception_datetime.strftime("%Y/%m/%d") if reception_datetime.hour != 0 else (reception_datetime - datetime.timedelta(days=1)).strftime("%Y/%m/%d"),
                    "reception_time": reception_datetime.strftime("%H:%M") if reception_datetime.hour != 0 else "24:" + reception_datetime.strftime("%M"),
                }
                if item["reception_date"] in result.keys():
                    result[item["reception_date"]].append(item)
                else:
                    result[item["reception_date"]] = [item]
                
            driver.back()
    
        # ブラウザを閉じる
        driver.close()
    
        if os.path.exists("./cs-info/cs-info_" + prefecture_key + ".json"):
            os.remove("./cs-info/cs-info_" + prefecture_key + ".json")
            
        with open("./cs-info/cs-info_" + prefecture_key + ".json", "a", encoding="shift_jis") as f:
            f.write(json.dumps(result))
        
    # with open("./cs-info.json", "r", encoding="shift_jis") as f:
    #     print(json.loads(f.read()))

if __name__ == "__main__":
    main()
