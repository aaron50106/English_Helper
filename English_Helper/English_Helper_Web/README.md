# English Master ─ 網頁版（Flask）

將原本的 PyQt5 桌面版英文單字訓練系統改為 **Flask 網頁應用**，透過瀏覽器操作，
後端訓練/資料邏輯沿用原本模組（`data_manager.py`、`training_engine.py`、`utils/`）。

## 專案結構
```
English_Helper_Web/
├── app.py                     # Flask 後端與 REST API
├── data_manager.py            # 資料管理層（沿用）
├── training_engine.py         # 訓練引擎（沿用）
├── utils/
│   ├── __init__.py
│   ├── app_logger.py          # 日誌工具（沿用）
│   └── input_new_vocabulary.py# 單字查詢服務（沿用）
├── templates/
│   └── index.html             # 網頁 UI
├── static/
│   ├── css/style.css          # 版面樣式（沿用桌面版淡藍配色）
│   └── js/app.js              # 前端邏輯（呼叫 API）
├── vocabulary_core.json       # 核心詞庫
├── vocabulary_custom.json     # 自訂詞庫
├── exam_questions.xlsx        # 歷屆試題
├── training_records.json      # 測驗紀錄
├── daily_vocab_stats.json     # 今日單字統計
└── requirements.txt
```

## 安裝與啟動
在本資料夾（`English_Helper_Web`）中執行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

啟動後開啟瀏覽器前往：<http://127.0.0.1:5000>

## 五大模組（對應網頁分頁）
1. **單字訓練**：中→英／英→中／混合，答對自動下一題，答錯顯示對照。
2. **歷屆題目練習**：依年份／題型出題，可選題序亂數，完成後寫入紀錄。
3. **隨機測驗**：自訂題數與題型組合，即時進度與正確率，結束產生成績。
4. **新增單字**：線上查詢單字（詞性／中文翻譯），一鍵加入並可於表格編輯自訂詞庫。
5. **測驗紀錄**：查閱所有測驗與練習紀錄，可依類型篩選。

## API 一覽
| 方法 | 路徑 | 說明 |
| --- | --- | --- |
| POST | `/api/vocab/question` | 取得單字訓練題 |
| POST | `/api/vocab/answer` | 提交單字訓練答案 |
| GET  | `/api/vocab/stats` | 今日單字統計 |
| POST | `/api/exam/start` | 開始歷屆練習 |
| POST | `/api/exam/answer` | 提交歷屆答案 |
| POST | `/api/exam/next` | 下一題／結算 |
| POST | `/api/quiz/start` | 開始隨機測驗 |
| POST | `/api/quiz/answer` | 提交測驗答案 |
| POST | `/api/quiz/next` | 下一題 |
| POST | `/api/quiz/end` | 結束並記錄 |
| POST | `/api/quiz/reset` | 重設測驗 |
| POST | `/api/lookup` | 線上查詢單字 |
| GET  | `/api/custom` | 取得自訂詞庫 |
| POST | `/api/custom/add` | 新增自訂單字 |
| POST | `/api/custom/save` | 覆寫自訂詞庫 |
| POST | `/api/custom/delete` | 刪除自訂單字 |
| GET  | `/api/records` | 取得測驗紀錄 |

## 備註
- 本程式為單機個人工具，後端使用全域共用狀態，建議單一使用者本機使用。
- 若要對外提供服務，請改用正式 WSGI 伺服器（如 gunicorn／waitress）並加上使用者隔離與驗證。
