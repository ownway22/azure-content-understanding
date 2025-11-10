import os
import requests
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# 載入環境變數
load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")
KEY = os.getenv("KEY")
VIDEO_ANALYZER_ID = os.getenv("VIDEO_ANALYZER_ID")
VIDEO_FILE_URL = os.getenv("VIDEO_FILE_URL")

def analyze_video():
    """傳送影片進行分析"""
    url = f"{ENDPOINT}contentunderstanding/analyzers/{VIDEO_ANALYZER_ID}:analyze?api-version=2025-05-01-preview"
    
    headers = {
        "Ocp-Apim-Subscription-Key": KEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "url": VIDEO_FILE_URL
    }
    
    print("=" * 60)
    print("Step 1: Sending video for analysis...")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Analyzer ID: {VIDEO_ANALYZER_ID}")
    print(f"File URL: {VIDEO_FILE_URL}")
    print("=" * 60)
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 202:
        print("✓ Video submitted successfully!")
        # 從 response headers 中取得 request-id
        request_id = response.headers.get("apim-request-id") or response.headers.get("x-ms-request-id")
        print(f"Request ID: {request_id}")
        return request_id
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_analysis_result(request_id):
    """使用 request-id 取得分析結果"""
    url = f"{ENDPOINT}contentunderstanding/analyzerResults/{request_id}?api-version=2025-05-01-preview"
    
    headers = {
        "Ocp-Apim-Subscription-Key": KEY
    }
    
    print("\n" + "=" * 60)
    print("Step 2: Retrieving analysis result...")
    print(f"Request ID: {request_id}")
    print("=" * 60)
    
    # 輪詢取得結果（可能需要幾秒鐘）
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown").lower()
            
            print(f"Attempt {attempt + 1}: Status = {status}")
            
            if status == "succeeded":
                print("✓ Analysis completed successfully!")
                return result
            elif status == "failed":
                print("✗ Analysis failed!")
                return result
            elif status in ["running", "notstarted"]:
                # 仍在處理中，等待後重試
                time.sleep(2)
            else:
                # 未知的狀態，仍然回傳結果
                print(f"⚠ Unknown status: {status}, returning result")
                return result
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    print("✗ Timeout: Analysis did not complete in time")
    return None

def save_result(result):
    """將結果儲存為 JSON 檔案"""
    # 如果 output 資料夾不存在則建立
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 產生帶有時間戳記的檔名
    date_stamp = datetime.now().strftime("%Y%m%d")
    time_stamp = datetime.now().strftime("%H%M%S")
    filename = f"video_result_{date_stamp}_{time_stamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # 儲存檔案
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"✓ Result saved to: {filepath}")
    print("=" * 60)
    
    return filepath

def main():
    print("\n🎬 Azure Content Understanding - Video Analysis")
    print("=" * 60)
    
    # 步驟 1: 分析影片
    request_id = analyze_video()
    
    if not request_id:
        print("\n❌ Failed to submit video for analysis")
        return
    
    # 步驟 2: 取得結果
    result = get_analysis_result(request_id)
    
    if not result:
        print("\n❌ Failed to retrieve analysis result")
        return
    
    # 步驟 3: 格式化輸出結果
    print("\n" + "=" * 60)
    print("Analysis Result (Pretty Print):")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 步驟 4: 儲存至檔案
    filepath = save_result(result)
    
    print("\n✅ Process completed successfully!")
    print(f"📄 Result file: {filepath}")

if __name__ == "__main__":
    main()
