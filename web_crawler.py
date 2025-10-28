import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import logging
from tqdm import tqdm

# --- 匯入配置 (新增 CHECKED_EMPTY_LOG_FILE) ---
from config import (
    BASE_URL, ADDRESS_API_ENDPOINT, JIBN_API_ENDPOINT, DATA_API_ENDPOINT,
    HEADERS, CROP_TYPES_TO_CRAWL, TARGET_REGIONS,
    START_DATE, SLEEP_TIME, TEST_LIMIT_UMD, TEST_LIMIT_RI, TEST_LIMIT_JIBN,
    CSV_FILE_NAME, CSV_HEADER, LOG_FILE_NAME, LOG_LEVEL, ENABLE_RESUME,
    CHECKED_EMPTY_LOG_FILE
)

# ... [日誌設定和所有 API 請求函式保持不變] ...
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(LOG_FILE_NAME, encoding='utf-8'), logging.StreamHandler()])

def get_jibn_list(session, sgg_cd, umd_ri_cd_part):
    url = f"{BASE_URL}{JIBN_API_ENDPOINT}"
    params = {'mode': 'JIBN', 'sgg_cd': sgg_cd, 'umd_cd': umd_ri_cd_part, '_': int(time.time() * 1000)}
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        options = soup.find_all('option')
        jibn_list = []
        for option in options:
            value, text = option.get('value'), option.get_text(strip=True)
            if value and text:
                jibn_code = value.split(',')[0]
                jibn_name = text.split(']')[1].strip() if ']' in text else text
                jibn_list.append({'cd': jibn_code, 'cd_nm': jibn_name})
        return jibn_list
    except requests.exceptions.RequestException as e:
        logging.error(f"獲取 Jibn 列表失敗: {e}, 參數: {params}")
        return []
    except Exception as e:
        logging.error(f"解析 Jibn HTML 時發生未知錯誤: {e}")
        return []

def get_address_list(session, parent_code):
    url = f"{BASE_URL}{ADDRESS_API_ENDPOINT}"
    params = {'mode': 'ADDR', 'code': parent_code, 'full_yn': 'Y', '_': int(time.time() * 1000)}
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        raw_text = response.text.strip()
        if not raw_text: return []
        locations = []
        if not raw_text.endswith(','): raw_text += ',$'
        pairs = raw_text.split(',$')
        for pair in pairs:
            if '$:' in pair:
                parts = pair.split('$:')
                if len(parts) == 2:
                    name, code = parts
                    clean_code = ''.join(filter(str.isdigit, code))
                    if name and clean_code:
                        locations.append({'cd_nm': name.strip(), 'cd': clean_code})
        return locations
    except requests.exceptions.RequestException as e:
        logging.error(f"獲取地址列表失敗: {e}, 參數: {params}")
        return []

# --- 【關鍵變更1】函式現在需要接收 checked_empty_items 集合 ---
def scrape_and_save_data(session, sgg_cd, umd_cd, jibn, location_name, crop_name, exam_type, gubun):
    url = f"{BASE_URL}{DATA_API_ENDPOINT}"
    payload = {'sgg_cd': sgg_cd, 'umd_cd': umd_cd, 'jibn': jibn, 'exam_type': exam_type, 'gubun': gubun, 'rowNum': '1', 'exam_day_str': START_DATE, 'exam_day_end': datetime.now().strftime('%Y%m%d')}
    try:
        response = session.post(url, data=payload)
        response.raise_for_status()

        # 檢查是否是「無數據」的提示
        if "데이터가 존재하지 않습니다" in response.text:
            # 【關鍵變更2】如果無數據，則將其 unique_id 寫入日誌檔
            unique_id = f"{location_name}|{crop_name}"
            with open(CHECKED_EMPTY_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(unique_id + '\n')
            return # 直接返回

        soup = BeautifulSoup(response.text, 'lxml')
        data_table = soup.find('table', class_='item_b')
        if not data_table: return
        
        rows = data_table.find_all('tr')
        with open(CSV_FILE_NAME, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            for i, row in enumerate(rows):
                if i > 0:
                    all_cols = [ele.get_text(strip=True) for ele in row.find_all('td')]
                    if all_cols:
                        cols = all_cols[:-2]
                        writer.writerow([location_name, crop_name] + cols)
        logging.info(f"已儲存: {location_name} ({crop_name})")
    except requests.exceptions.RequestException as e:
        logging.error(f"爬取最終資料失敗: {e}, Payload: {payload}")
    except Exception as e:
        logging.error(f"處理最終資料時發生未知錯誤: {e}, 地點: {location_name}")

# --- 主執行流程 (修改斷點續爬邏輯) ---
def main():
    processed_items = set()
    if ENABLE_RESUME:
        # 讀取已成功儲存的資料
        try:
            with open(CSV_FILE_NAME, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) > 1:
                        unique_id = f"{row[0]}|{row[1]}"
                        processed_items.add(unique_id)
            logging.info(f"從 CSV 檔案中載入了 {len(processed_items)} 條已處理的記錄。")
        except FileNotFoundError:
            logging.info("未找到 CSV 檔案，將創建新檔案。")
            with open(CSV_FILE_NAME, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADER)

        # 【關鍵變更3】讀取已檢查為空的地點日誌
        try:
            with open(CHECKED_EMPTY_LOG_FILE, 'r', encoding='utf-8') as f:
                # 使用 set comprehension 快速讀取
                empty_items = {line.strip() for line in f}
                initial_count = len(processed_items)
                processed_items.update(empty_items)
                logging.info(f"從日誌中載入了 {len(empty_items)} 條已檢查為空的記錄。總跳過項目: {len(processed_items)}")
        except FileNotFoundError:
            logging.info("未找到已檢查為空的日誌檔，將在運行中創建。")

    else:
        with open(CSV_FILE_NAME, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)

    # ... [後面的主流程程式碼保持不變] ...
    logging.info(f"自動化爬蟲開始... 資料將儲存至: {CSV_FILE_NAME}")
    start_time = time.time()
    for crop_name, exam_type_val, gubun_val in CROP_TYPES_TO_CRAWL:
        logging.info(f"================== 開始處理作物類型: {crop_name} ==================")
        session = requests.Session()
        session.headers.update(HEADERS)
        logging.info("正在初始化 Session...")
        try:
            response = session.get(f"{BASE_URL}/sibi/sibiMain.do")
            response.raise_for_status()
            if 'JSESSIONID' in session.cookies:
                 logging.info("新 Session 初始化完成。")
            else:
                logging.warning("未能獲取新的 JSESSIONID。")
        except requests.exceptions.RequestException:
            logging.warning("新 Session 初始化失敗。")
        perform_single_test(session, crop_name, exam_type_val, gubun_val, processed_items)
    end_time = time.time()
    logging.info(f"爬取完畢！總耗時: {end_time - start_time:.2f} 秒。")

# perform_single_test 函式也需要修改以傳遞 checked_empty_items
def perform_single_test(session, crop_name, exam_type_val, gubun_val, processed_items):
    # ... [外層迴圈保持不變] ...
    for sido_name, sido_code in TARGET_REGIONS.items():
        logging.info(f"--- 正在處理省份: {sido_name} ---")
        sigungu_list = get_address_list(session, sido_code)
        if not sigungu_list:
            logging.warning(f"未能獲取 {sido_name} 的下級列表，跳過。")
            continue
        for sigungu in tqdm(sigungu_list, desc=f"處理 {sido_name} 的市/郡/區", unit="個"):
            sigungu_short_code, sigungu_name = sigungu['cd'], sigungu['cd_nm']
            sigungu_full_code = sido_code + sigungu_short_code
            umd_list = get_address_list(session, sigungu_full_code)
            for umd in umd_list:
                umd_short_code, umd_name = umd['cd'], umd['cd_nm']
                umd_full_code = sigungu_full_code + umd_short_code
                ri_list = get_address_list(session, umd_full_code)
                for ri in ri_list:
                    ri_short_code, ri_name = ri['cd'], ri['cd_nm']
                    umd_ri_combined_code = umd_short_code + ri_short_code
                    jibn_list = get_jibn_list(session, sigungu_full_code, umd_ri_combined_code)
                    for jibn in jibn_list:
                        jibn_code, jibn_name = jibn['cd'], jibn['cd_nm']
                        full_location_name = f"{sido_name} {sigungu_name} {umd_name} {ri_name} {jibn_name}"
                        unique_id = f"{full_location_name}|{crop_name}"
                        
                        # 【關鍵變更4】在這裡檢查是否需要跳過
                        if ENABLE_RESUME and unique_id in processed_items:
                            continue

                        # 傳遞 checked_empty_items 集合
                        scrape_and_save_data(session, sigungu_full_code, umd_ri_combined_code, jibn_code, full_location_name, crop_name, exam_type_val, gubun_val)
                        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()