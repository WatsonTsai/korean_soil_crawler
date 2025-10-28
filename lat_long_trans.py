import csv
import io
from geopy.geocoders import ArcGIS
import time
import os

# --- 檔案名稱設定 ---
INPUT_FILE = 'soil_data_FULL.csv'
OUTPUT_FILE = 'processed.csv'
PROCESSED_LOG_FILE = 'processed_rows.log' # 用於記錄已處理行的檔案

def get_starting_serial_number(output_filename):
    """
    檢查輸出檔案，確定下一個可用的流水號。
    如果檔案不存在，從 1 開始。
    否則，讀取檔案行數並從 '行數' 開始 (因為第一行為標頭)。
    """
    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            # -1 是為了減去標頭行。如果檔案為空或只有標頭，結果為 0 或 -1。
            num_data_rows = sum(1 for row in f) - 1
            # max(0, ...) 確保不會有負數。下一個流水號是 '現有資料行數 + 1'。
            return max(0, num_data_rows) + 1
    except FileNotFoundError:
        # 檔案不存在，這是第一次，從 1 開始
        return 1

def convert_som_to_soc(som_g_per_kg):
    """
    使用 Van Bemmelen factor 將土壤有機物 (SOM) 轉換為土壤有機碳 (SOC)。
    """
    try:
        som_value = float(som_g_per_kg)
        soc_percent = (som_value / 1.724) / 10
        return f"{soc_percent:.3f}"
    except (ValueError, TypeError):
        return ''

def process_incremental_data():
    """
    主處理函式，支持增量更新，並將唯一的流水號填入 'description' 欄位。
    """
    print("--- 開始增量資料處理 ---")
    
    # 1. 載入已處理記錄
    processed_fingerprints = set()
    try:
        with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f_log:
            processed_fingerprints = {line.strip() for line in f_log}
        print(f"成功從 '{PROCESSED_LOG_FILE}' 載入 {len(processed_fingerprints)} 筆已處理記錄。")
    except FileNotFoundError:
        print(f"'{PROCESSED_LOG_FILE}' 不存在，將會建立新檔案。")

    # 2. 確定起始流水號
    current_serial_number = get_starting_serial_number(OUTPUT_FILE)
    if current_serial_number > 1:
        print(f"'{OUTPUT_FILE}' 已存在。新資料將從流水號 {current_serial_number} 開始。")
    
    # 3. 準備地理編碼器和計數器
    geolocator = ArcGIS(timeout=10)
    new_rows_processed = 0
    skipped_rows = 0

    # 4. 檢查輸出檔案是否存在
    output_exists = os.path.exists(OUTPUT_FILE)

    # 5. 以 '追加' 模式打開檔案
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8', newline='') as f_in, \
             open(OUTPUT_FILE, 'a', encoding='utf-8', newline='') as f_out, \
             open(PROCESSED_LOG_FILE, 'a', encoding='utf-8') as f_log:

            csv_reader = csv.DictReader(f_in)
            
            # 修改: 恢復 'description' 欄位，移除 'id'
            header_new = [
                'researcher', 'longitude', 'latitude', 'description', 'date_str', 'depth',
                'sand_rate', 'silt_rate', 'clay_rate', 'soil_temperature', 'soil_moisture',
                'hydraulic_conductivity', 'ph', 'ec', 'bulk_density', 'soc', 'cec',
                'chloride', 'nitrogen', 'phosphorus', 'kalium', 'cu', 'cd', 'pb', 'zn',
                'ni', 'fe', 'cr', 'as', 'hg'
            ]
            csv_writer = csv.DictWriter(f_out, fieldnames=header_new)

            if not output_exists:
                csv_writer.writeheader()

            for i, row in enumerate(csv_reader):
                if not row: continue

                row_fingerprint = "|".join(str(val) for val in row.values())

                if row_fingerprint in processed_fingerprints:
                    skipped_rows += 1
                    continue
                
                new_rows_processed += 1
                header_original = list(row.keys())
                address = row[header_original[0]]
                print(f"發現新資料 (原始行號 {i+1}): {address}，正在處理...")

                latitude, longitude = '', ''
                try:
                    location = geolocator.geocode(address)
                    if location:
                        latitude = f"{location.latitude:.6f}"
                        longitude = f"{location.longitude:.6f}"
                        print(f" -> 經緯度轉換成功")
                    else:
                         print(" -> 經緯度轉換失敗")
                except Exception as e:
                    print(f" -> 地理編碼時發生錯誤: {e}")
                
                time.sleep(0.5)

                new_row_dict = {key: '' for key in header_new}
                new_row_dict.update({
                    'researcher': 'rda_kr',
                    'depth': '0-15',
                    'description': current_serial_number, # 修改: 將流水號賦予 description
                    'longitude': longitude,
                    'latitude': latitude,
                    'date_str': row.get(header_original[3], '').replace('.', '-'),
                    'ph': float(row.get(header_original[4])) if row.get(header_original[4]) else '',
                    'ec': float(row.get(header_original[10])) if row.get(header_original[10]) else '',
                    'phosphorus': float(row.get(header_original[6])) if row.get(header_original[6]) else '',
                    'kalium': float(row.get(header_original[7])) if row.get(header_original[7]) else '',
                    'soc': convert_som_to_soc(row.get(header_original[5]))
                })
                
                csv_writer.writerow(new_row_dict)
                f_log.write(row_fingerprint + '\n')
                processed_fingerprints.add(row_fingerprint)
                
                # 為下一筆資料準備流水號
                current_serial_number += 1

    except FileNotFoundError:
        print(f"錯誤：找不到輸入檔案 '{INPUT_FILE}'。請確認檔案存在於相同目錄下。")
        return
    except Exception as e:
        print(f"處理過程中發生未預期的錯誤: {e}")
        return

    print("\n--- 處理完畢 ---")
    print(f"新增了 {new_rows_processed} 筆新的資料。")
    print(f"跳過了 {skipped_rows} 筆已處理過的舊資料。")
    print(f"完整結果已更新至 '{OUTPUT_FILE}'。")

# --- 主程式入口 ---
if __name__ == "__main__":
    process_incremental_data()