# SRT Check — 字幕檢查工具

試用版 0.1.0。讀取 SRT、找出需要處理的問題，方便在字幕燒錄或交付前檢查。只使用 Python 標準函式庫；不需要 API Key、GPU 或 FFmpeg。

[English guide](README.en.md) · [MIT 授權](LICENSE) · [貢獻說明](CONTRIBUTING.md) · [更新紀錄](CHANGELOG.md)

## 快速使用

需要 Python 3.10 或更新版本。從 GitHub 的 Code → Download ZIP 下載後，先解壓縮整個資料夾，再於此資料夾執行：

```sh
python srt_check.py examples/clean.srt --strict
python srt_check.py examples/review-needed.srt
python srt_check.py "你的字幕.srt" --duration 1440.102
python srt_check.py "你的字幕.srt" --json --output report.json
```

不需 pip 安裝依賴。Windows 可執行 `Run-Demo.cmd` 查看自製範例，或把一個／多個 SRT 拖曳到它上面檢查。啟動器會尋找 Python，找不到時提供安裝提示；不會自行下載軟體。

Windows 若使用 `py` 啟動 Python，可將範例命令中的 `python` 換成 `py -3`。尚未安裝 Python 時，請從 [python.org](https://www.python.org/downloads/) 安裝。請勿直接在 ZIP 預覽內執行啟動器。

執行預設範例時，應看到：

```text
clean.srt: 2 cues, 0 errors, 0 warnings
review-needed.srt: 4 cues, 1 errors, 3 warnings
```

第二個範例故意含錯誤，exit 1 是預期結果。一般字幕的 warning 是待人工查看的提示，並不一定要修改。

## 檢查項目

| 代碼 | 等級 | 意義 |
|---|---|---|
| EMPTY_FILE / EMPTY_TEXT | error | 空檔案或沒有可見文字 |
| INVALID_INDEX / INVALID_TIMESTAMP | error | 缺少合法序號或時間格式 |
| MISSING_SEPARATOR | error | 字幕文字中疑似包含下一段序號與時間軸，可能漏了空白分隔行 |
| INVALID_DURATION | error | 結束時間小於或等於開始時間 |
| BEYOND_MEDIA | error | 超出使用者提供的影片長度 |
| INDEX_SEQUENCE / OUT_OF_ORDER | warning | 序號不連續或開始時間倒序 |
| OVERLAP | warning | 時間重疊；多人對話可能是刻意安排，請人工確認 |
| READING_SPEED | warning | 超過每秒字數設定 |
| LINE_WIDTH / LINE_COUNT | warning | 行寬或行數超過設定 |
| INPUT_ERROR | error | 檔案無法讀取或解碼 |

預設 `--max-cps 15 --max-width 42 --max-lines 2` 只是初始檢查設定，不是通用字幕規範，也不代表品質保證。可依語言與使用場合調整。

- 每秒字數：NFC 正規化後，排除空白、組合標記與控制字元，保留標點；移除常見 `b/i/u/font` 標籤並解碼 HTML entities。
- 行寬：Unicode Wide/Fullwidth 算 2，其他一般字元算 1；這是粗略估計，不等於實際字型像素寬度。組合 emoji 的計數仍有侷限。
- 支援有序號、以空白行分隔、逗號毫秒的普通 SRT，以及 UTF-8 / UTF-8 BOM、LF / CRLF。其他編碼請明確指定，例如 `--encoding utf-16` 或 `--encoding cp950`。
- 不支援 VTT、ASS、SRT 座標延伸格式，也不判斷翻譯正確性、漏譯或聲畫同步。
- 影片長度由 `--duration` 手動提供，只允許單一輸入檔。工具不讀影片。

## 檔案與回傳碼

輸入檔只讀取，不自動修正。`--output` 只建立新的 JSON 報告；路徑已存在就拒絕，包含原始字幕本身。JSON 包含檔名、SHA-256、檢查設定與問題位置，不包含字幕全文。未設定 `--output` 時不建立報告檔。

- `0`：沒有 error；warning 仍需人工查看。
- `1`：存在 error，或使用 `--strict` 時存在 warning。
- `2`：參數、輸入讀取或輸出報告失敗。

## 驗證與回報

```sh
python -I -m unittest discover -s tests -t . -v
```

範例與測試皆為本專案自製，未包含節目字幕或影片。回報問題請附工具版本、Python / 作業系統版本、執行指令、預期／實際結果，以及最小的自製 SRT 範例。請勿附憑證或不適合公開的內容。

已在 Windows / Python 3.12.14 通過 20 項測試，涵蓋實際 CMD 啟動、中文含空格路徑、多檔傳入與 Python 探測備援。GUI 拖曳未做視覺驗證。Ubuntu / macOS 與 Python 3.10 的 GitHub Actions 測試設定已提供，結果以實際 Actions 執行為準。

請到本程式碼庫的 Issues → New issue 選擇「錯誤回報」或「試用回饋」。目前尚未建立外部使用者採用證據。
