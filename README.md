# 內科臨床指引索引（Internal Medicine Guideline Index）

單一自帶檔的臨床指引索引網站。9 大次專科、71 個疾病，67 個鎖定學會權威來源
（KDIGO、ESC、ACC/AHA、ATA、EULAR、ACR、IDSA、AASLD、ACG、Surviving Sepsis…），
每次開啟即時向 PubMed（NCBI E-utilities）查詢，學會出新版自動帶入最新版。
純前端、無伺服器；PMC 有公開全文者標綠並直連全文。

## 用 GitHub Pages 上線（約 2 分鐘）

1. 到 github.com 右上「+」→ **New repository**。
   - Repository name 例如 `internal-med-guidelines`
   - 設 **Public**（Pages 免費版需公開）
   - 建立後進入該 repo。

2. 上傳檔案（兩種擇一）：
   - **網頁拖曳**：repo 首頁 → **Add file ▸ Upload files** → 把 `index.html` 與
     `.nojekyll` 一起拖進去 → **Commit changes**。
   - **命令列**：
     ```bash
     git init
     git add index.html .nojekyll
     git commit -m "init guideline index"
     git branch -M main
     git remote add origin https://github.com/<你的帳號>/internal-med-guidelines.git
     git push -u origin main
     ```

3. 開啟 Pages：repo → **Settings ▸ Pages** → Source 選 **Deploy from a branch**
   → Branch 選 **main**、資料夾 **/ (root)** → **Save**。

4. 等約 1 分鐘，網址為
   `https://<你的帳號>.github.io/internal-med-guidelines/`
   （Settings ▸ Pages 上方會顯示綠色 "Your site is live at …"）。

## 更新內容
改 `index.html` 內 `DISEASES` 陣列即可：
- 新增疾病：加一列 `{ sub:'endo', zh:'中文名', en:'English', gq:'鎖定學會的檢索式' }`
- 調整鎖定來源：改該疾病的 `gq`（學會關鍵字 + 旗艦期刊 `[ta]`）
- `ds:1` 旗標＝改用日期排序抓最新版（適合每年更新的報告，如 GOLD）
改完 commit/push，Pages 會自動重新佈署。

## 備註
- 指引清單為瀏覽器端即時抓取（NCBI E-utilities，CORS 開放），故不需後端。
- PubMed 有速率限制，程式已用佇列節流；如需更穩，可到 NCBI 申請免費 API key。
- `.nojekyll` 讓 GitHub Pages 略過 Jekyll 處理，確保檔案原樣輸出。
