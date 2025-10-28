# --- 1. API and URL Settings ---
BASE_URL = "https://soil.rda.go.kr"
ADDRESS_API_ENDPOINT = "/cmm/common/ajaxCall.do"
JIBN_API_ENDPOINT = "/sibi/sibiPrescriptProc.do"
DATA_API_ENDPOINT = "/sibi/multiSibiAvgChemical.do"

# --- 2. Request Headers ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Referer': f"{BASE_URL}/sibi/sibiMain.do",
    'X-Requested-With': 'XMLHttpRequest'
}

# --- 3. Crawling Target Settings ---

# 3.1. 目標作物類型
CROP_TYPES_TO_CRAWL = [
    ('논 (水田)', '1', 'P')
    # ('밭 (旱田)', '2', 'P'),
    # ('과수 (果樹)', '4', 'P')
]

# 3.2. 目標地理範圍
ALL_KOREA_REGIONS = {
    '강원특별자치도': '42', '경기도': '41', '경상남도': '48', '경상북도': '47',
    '전라남도': '46', '전북특별자치도': '45', '제주특별자치도': '50', '충청남도': '44',
    '충청북도': '43'
}

TARGET_REGIONS = ALL_KOREA_REGIONS


# --- 4. Crawling Parameters ---
# 查詢的開始日期
START_DATE = '20220801'

# 請求之間的延遲時間（秒）
SLEEP_TIME = 0.3 # 建議保持一個較小的延遲，以對伺服器友好

# --- 【關鍵變更2】解除數量限制 ---
# 將所有限制設為 0 或負數，表示不啟用限制
TEST_LIMIT_UMD = 0
TEST_LIMIT_RI = 0
TEST_LIMIT_JIBN = 0

# --- 5. Output Settings ---
# 建議為全量爬取使用一個新的檔名
CSV_FILE_NAME = 'soil_data_FULL.csv'
CSV_HEADER = [
    '地點名稱', '작물유형(作物類型)', '번호(編號)', '검정일자(檢測日期)', 'pH (1:5)', '유기물(有機物)',
    '유효인산(有效磷酸)', '칼륨(鉀)', '칼슘(鈣)', '마그네슘(鎂)',
    '전기전도도(EC)', '유효규산(有效矽酸)'
]

# --- 6. Logging and Error Handling ---
LOG_FILE_NAME = 'crawler_full.log' # 為全量爬取使用獨立的日誌檔案
LOG_LEVEL = 'INFO'

# --- 7. Resumable Crawling ---
ENABLE_RESUME = True
# 【新增】用於記錄已檢查但無數據的地點的日誌檔名
CHECKED_EMPTY_LOG_FILE = 'checked_empty.log'