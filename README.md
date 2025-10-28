# Korean Soil Data Crawler

這個專案是一個自動化爬蟲工具，用於從韓國農村振興廳（Rural Development Administration, RDA）的土壤資料庫中收集土壤參數數據。

## 功能特點

- 自動抓取韓國各地區的土壤參數數據
- 支持多種農作物類型的數據收集
- 自動地理編碼（地址轉換為經緯度座標）
- 數據清理和格式轉換
- 輸出為標準化的 Excel 格式
- 具有斷點續爬功能
- 完整的日誌記錄系統

## 專案結構

- `web_crawler.py` - 主要的爬蟲程式
- `config.py` - 配置文件，包含所有可調整的參數
- `lat_long_trans.py` - 地理編碼轉換工具
- `output.py` - 數據清理和輸出處理

## 安裝需求

```bash
pip install requests
pip install beautifulsoup4
pip install pandas
pip install geopy
pip install tqdm
```

## 使用方法

1. 配置設定：
   - 在 `config.py` 中設定目標地區、作物類型和其他參數

2. 執行爬蟲：
   ```bash
   python web_crawler.py
   ```
   
3. 進行地理編碼轉換：
   ```bash
   python lat_long_trans.py
   ```

4. 輸出最終結果：
   ```bash
   python output.py
   ```

## 輸出文件

- `soil_data_FULL.csv` - 原始爬取數據
- `processed.csv` - 經過地理編碼處理的數據
- `soil_parameter_record_rda_kr_YYYYMMDD.xlsx` - 最終清理後的 Excel 文件
- `crawler_full.log` - 完整的爬蟲日誌
- `processed_rows.log` - 地理編碼處理進度日誌

## 注意事項

1. 請遵守目標網站的使用條款和爬蟲規則
2. 建議設定適當的 `SLEEP_TIME` 以避免對目標伺服器造成過大負擔
3. 對於大量數據抓取，建議開啟 `ENABLE_RESUME` 功能以支援斷點續爬

## 配置說明

在 `config.py` 中可以調整的主要參數：

- `TARGET_REGIONS` - 目標地區列表
- `CROP_TYPES_TO_CRAWL` - 目標作物類型
- `SLEEP_TIME` - 請求間隔時間
- `TEST_LIMIT_*` - 測試模式的限制數量
- `ENABLE_RESUME` - 是否啟用斷點續爬功能

## 授權

本專案僅供學術研究使用。