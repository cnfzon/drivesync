# DriveSync

DriveSync 是一個 **即時賽車模擬儀表板系統**，透過 **UART** 從微控制器接收車輛遙測資料，使用 **Pygame** 進行視覺化顯示，並透過 **vGamepad** 將資料轉換為虛擬 Xbox 360 控制器輸出。

本專案適用於 **自製方向盤 / 油門 / 煞車硬體**、嵌入式系統整合，以及賽車模擬實驗。

---

## 功能特色

- UART 即時資料解碼（檔位、轉速、速度、油門、煞車、轉向角）
- 賽車風格即時儀表板（Pygame）
- 虛擬 Xbox 360 控制器輸出（vGamepad）
- 無硬體時可使用鍵盤模式測試

---

## UART 封包格式

每筆資料封包長度為 **16 bytes**：
0xAB . gear . rpm(2B) . speed(2B) . throttle . brake . steering(2B)
- 使用 `0x2E (.)` 作為欄位分隔符
- 轉向角度以 **角度 ×10** 傳輸，解碼後再除以 10 還原

---

## 環境需求

- Python 3.9 以上
- Windows（vGamepad 需求）

安裝套件：

```bash
pip install pygame pyserial vgamepad
