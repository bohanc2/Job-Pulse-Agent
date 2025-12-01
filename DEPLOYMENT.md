# Render 部署指南

本指南將幫助您將 Ascendo AI Community Jobs 部署到 Render.com。

## 部署前準備

### 1. 確保所有文件已準備

✅ 已創建的文件：
- `Procfile` - Render 啟動命令
- `runtime.txt` - Python 版本指定
- `requirements.txt` - 已包含 gunicorn 和 psycopg2-binary
- `models/database.py` - 已支持 PostgreSQL
- `app.py` - 已支持生產環境配置

### 2. 準備 Git 倉庫

```bash
# 初始化 Git（如果還沒有）
git init

# 確保 .gitignore 包含以下內容
# .env
# __pycache__/
# *.db
# *.pyc

# 提交所有文件
git add .
git commit -m "Prepare for Render deployment"

# 推送到 GitHub
git remote add origin https://github.com/yourusername/ascendo-jobs.git
git branch -M main
git push -u origin main
```

## Render 部署步驟

### 步驟 1: 創建 Render 帳號

1. 訪問 https://render.com
2. 使用 GitHub 帳號登錄（推薦）
3. 授權 Render 訪問您的 GitHub 倉庫

### 步驟 2: 創建 PostgreSQL 數據庫

1. 在 Render Dashboard，點擊 **"New +"**
2. 選擇 **"PostgreSQL"**
3. 配置：
   - **Name**: `ascendo-db`（或您喜歡的名稱）
   - **Database**: `ascendo`（可選，使用默認也可以）
   - **User**: 自動生成
   - **Region**: 選擇離您最近的區域
   - **Plan**: Free（或選擇付費計劃）
4. 點擊 **"Create Database"**
5. 記下數據庫的連接信息（但通常不需要手動配置，Render 會自動處理）

### 步驟 3: 創建 Web Service

1. 在 Render Dashboard，點擊 **"New +"**
2. 選擇 **"Web Service"**
3. 連接您的 GitHub 倉庫：
   - 如果已授權，選擇您的倉庫
   - 如果沒有，點擊 "Connect GitHub" 並授權
4. 選擇 `Ascendo` 倉庫
5. 配置服務：

   **基本設置：**
   - **Name**: `ascendo-jobs`（或您喜歡的名稱）
   - **Region**: 選擇與數據庫相同的區域（推薦）
   - **Branch**: `main`（或您的主分支）
   - **Root Directory**: 留空（如果項目在根目錄）

   **構建和啟動：**
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

   **計劃：**
   - **Plan**: Free（或選擇付費計劃）

### 步驟 4: 配置環境變量

在 Web Service 的設置頁面，找到 **"Environment"** 部分，添加以下變量：

```
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
OPENAI_API_KEY=your_openai_key (可選)
FLASK_ENV=production
```

**重要**: `DATABASE_URL` 會自動從 PostgreSQL 服務提供，無需手動添加。

### 步驟 5: 鏈接數據庫

1. 在 Web Service 設置頁面，找到 **"Connections"** 部分
2. 點擊 **"Link Database"**
3. 選擇您創建的 PostgreSQL 數據庫
4. Render 會自動將 `DATABASE_URL` 添加到環境變量中

### 步驟 6: 部署

1. 點擊 **"Create Web Service"**
2. Render 會開始構建和部署：
   - 克隆倉庫
   - 安裝依賴（約 2-3 分鐘）
   - 構建應用
   - 啟動服務
3. 等待部署完成（通常 3-5 分鐘）
4. 部署成功後，您會看到綠色的 "Live" 狀態

### 步驟 7: 訪問應用

部署完成後，您的應用將在以下 URL 可用：
```
https://your-service-name.onrender.com
```

## 部署後操作

### 1. 驗證部署

1. 訪問您的應用 URL
2. 檢查頁面是否正常加載
3. 檢查 Admin Settings 是否可以訪問
4. 查看 Render Dashboard → Logs 確認沒有錯誤

### 2. 首次數據收集

- 應用啟動後，調度器會自動開始工作
- 首次收集可能需要 10-30 分鐘
- 可以通過 Admin Settings → "🔄 Refresh Now" 手動觸發

### 3. 監控和日誌

- **日誌**: Render Dashboard → Your Service → Logs
- **指標**: Render Dashboard → Your Service → Metrics
- **事件**: Render Dashboard → Your Service → Events

## 常見問題

### Q: 部署失敗，構建錯誤
**A**: 檢查：
- `Procfile` 是否存在且格式正確
- `requirements.txt` 是否包含所有依賴
- Python 版本是否正確（runtime.txt）
- 查看構建日誌中的具體錯誤信息

### Q: 應用啟動後立即崩潰
**A**: 檢查：
- 所有環境變量是否已設置
- `DATABASE_URL` 是否正確（應該自動提供）
- 查看應用日誌中的錯誤信息

### Q: 數據庫連接失敗
**A**: 檢查：
- PostgreSQL 服務是否已創建並運行
- Web Service 是否已鏈接到數據庫
- `DATABASE_URL` 環境變量是否存在

### Q: 免費層服務休眠
**A**: 
- Render 免費層在 15 分鐘不活動後會休眠
- 首次訪問休眠的服務需要 30-60 秒喚醒
- 考慮使用付費計劃以保持服務始終運行
- 或使用外部服務定期 ping 您的 URL 以保持活躍

## 升級到付費計劃

如果需要：
- 始終在線的服務（無休眠）
- 更快的響應時間
- 更多資源
- 優先支持

可以升級到 Render 的付費計劃（$7/月起）。

## 自定義域名

1. 在 Web Service 設置中，找到 **"Custom Domains"**
2. 點擊 **"Add Custom Domain"**
3. 輸入您的域名
4. 按照指示配置 DNS 記錄
5. Render 會自動提供 SSL 證書

## 備份數據庫

1. 在 PostgreSQL 服務設置中
2. 找到 **"Backups"** 部分
3. 可以手動創建備份或設置自動備份
4. 付費計劃包含自動每日備份

## 更新應用

當您推送新代碼到 GitHub 時：
1. Render 會自動檢測更改
2. 自動觸發新的部署
3. 零停機時間部署（藍綠部署）

## 回滾部署

如果需要回滾到之前的版本：
1. 在 Render Dashboard → Your Service → Events
2. 找到之前的成功部署
3. 點擊 "Redeploy"

## 成本估算

### 免費層
- Web Service: 免費（有休眠限制）
- PostgreSQL: 免費（90 天後需要升級或導出數據）
- 總計: $0/月

### 入門計劃
- Web Service: $7/月
- PostgreSQL: $0/月（免費層可用）
- 總計: $7/月

## 安全建議

1. **環境變量**: 永遠不要將 API 密鑰提交到 Git
2. **數據庫**: 使用強密碼（Render 自動生成）
3. **HTTPS**: Render 自動提供 SSL 證書
4. **備份**: 定期備份數據庫
5. **監控**: 定期檢查日誌和指標

## 支持

如果遇到問題：
1. 查看 Render 文檔: https://render.com/docs
2. 檢查應用日誌
3. 查看 Render 社區論壇
4. 聯繫 Render 支持（付費用戶）

---

**部署完成後，您的應用將可以通過互聯網訪問，無需用戶自行安裝！**

