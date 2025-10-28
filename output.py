import pandas as pd
from datetime import date
import os

# --- 設定 ---
# 您想要清理的檔案名稱
INPUT_FILENAME = 'processed.csv'

def clean_and_export_to_excel(input_file):
    """
    讀取一個 CSV 檔案，移除 'longitude' 或 'latitude' 欄位為空的資料行，
    並將結果儲存到一個以當天日期命名的 Excel (.xlsx) 檔案中。
    """
    print(f"準備處理檔案: '{input_file}'...")

    # 步驟 1: 產生動態的輸出檔名
    # 格式: soil_parameter_record_rda_kr_YYYYMMDD.xlsx
    today_str = date.today().strftime("%Y%m%d")
    output_filename = f"soil_parameter_record_rda_kr_{today_str}.xlsx"
    
    try:
        # 步驟 2: 使用 pandas 讀取 CSV 檔案
        # read_csv 讀取時，空的欄位會被自動辨識為 'NaN' (Not a Number)
        df = pd.read_csv(input_file, encoding='utf-8')

        # 記錄原始資料筆數
        initial_row_count = len(df)
        print(f"原始檔案共有 {initial_row_count} 筆資料。")
        
        # 檢查必要的經緯度欄位是否存在
        if 'longitude' not in df.columns or 'latitude' not in df.columns:
            print("錯誤: 檔案中找不到 'longitude' 或 'latitude' 欄位。")
            return

        # 步驟 3: 移除 'longitude' 或 'latitude' 為空值的資料行
        # dropna 會移除任何在指定欄位(subset)中包含 NaN 值的資料行
        cleaned_df = df.dropna(subset=['longitude', 'latitude'])
        
        # 記錄清理後的資料筆數
        final_row_count = len(cleaned_df)
        
        # 步驟 4: 將清理後的資料寫入 Excel 檔案
        # index=False 表示在寫入 Excel 時不要包含 pandas 的索引欄 (0, 1, 2...)
        cleaned_df.to_excel(output_filename, index=False, engine='openpyxl')
        
        print("\n--- 處理完成 ---")
        print(f"成功將結果寫入新檔案: '{output_filename}'")
        print(f"保留了 {final_row_count} 筆擁有完整經緯度的資料。")
        print(f"移除了 {initial_row_count - final_row_count} 筆經緯度不完整的資料。")

    except FileNotFoundError:
        print(f"錯誤: 找不到輸入檔案 '{input_file}'。請確認檔案名稱和路徑是否正確。")
    except Exception as e:
        print(f"處理過程中發生未預期的錯誤: {e}")

# --- 主程式入口 ---
if __name__ == "__main__":
    clean_and_export_to_excel(INPUT_FILENAME)