# Bikara報刀機器人

![碧卡拉](bikara.webp)

## 關於Bikara
Bikara是手機遊戲《超異域公主連結☆Re：Dive》的Discord專用報刀機器人，會自動撈取報刀頻道內的成員訊息並計算王的剩餘血量。另外，也提供一些查看成員出刀紀錄等等的功能。

### 為什麼叫Bikara

因為作者在開發這支機器人的時候，台版的碧卡拉剛出。  
明明是公主連結的機器人，卻不是用公主連結的本家角色命名，可憐哪。

## 部署方法

目前僅支援機器人與伺服器1對1的部署方法，意即每個要使用此機器人的Discord頻道，都要自己部署一個機器人。  


### 前置條件

1. 先確定你已經到 [Discord Developer Portal](https://discord.com/developers/applications) 建立一支專屬於你的機器人。

2. 確認你的機器人有開啟對應的`Intent`：  

> 到Discord Developer Portal > Applications > 你的機器人 > Bot 頁籤下。  
> 把`PRESENCE INTENT`、`SERVER MEMBERS INTENT`、`MESSAGE CONTENT INTENT`三個選項都啟用。

3. 確認你頻道有開放以下權限給機器人：  

| 類型 | BOT PERMISSIONS |  
| --- | --- |
| GENERAL PERMISSIONS | Read Messages/View Channels |
| TEXT PERMISSIONS | Send Messages |
| TEXT PERMISSIONS | Manage Messages |
| TEXT PERMISSIONS | Read Message History |
| TEXT PERMISSIONS | Mention Everyone |

4. 確認你有一個可用的MongoDB環境。不想在自己的電腦安裝MongoDB的話，[MongoDB官方](https://www.mongodb.com/atlas/database)有免費的環境可以使用，只要辦帳號就好了。  
（如果沒有MongoDB環境可用的話，`broadcast`相關指令會不能使用，如果用不到也可以跳過此步驟。）

### 執行檔

#### Windows
1. 下載`bikara.exe`執行檔。
2. 在同一個目錄下建立`config.json`檔案。
3. 執行`bikara.exe`。

（註：防毒軟體可能會將`bikara.exe`視為病毒，有疑慮的話可以自行clone原始碼建置或執行，或不使用）

#### config.json

```json
{
    "botToken": "",
    "guildId": 0,
    "masterId": 0,
    "clans": [
        {
            "roleId": 0,
            "roleName": "",
            "bossChannels": [
                {
                    "id": 0,
                    "health": 0
                },
                // ...
            ]
        },
        // ...
    ],
    "mongo": {
        "protocol": "",
        "host": "",
        "port": 27017,
        "user": "",
        "password": ""
    }
}
```
| 欄位名稱 | 型別 | 描述 | 必填 |
| --- | --- | --- | --- |
| botToken | string | Discord機器人的Token | ✅ |
| guildId | number | 要啟用這個機器人Discord伺服器ID | ✅ |
| masterId | number | 該伺服器管理員的ID，若有使用`history`、`broadcast`等指令則須設定。 |  |
| clans | array | 戰隊資訊，若有多個戰隊共用同一個Discord伺服器，可在此設定多個戰隊 | ✅ |
| clans.roleId | number | 該戰隊成員的Discord身分組ID | ✅ |
| clans.roleName | number | 該戰隊成員的Discord身分組名稱 | ✅ |
| clans.bossChannels | array | 該戰隊的報刀頻道 | ✅ |
| clans.bossChannels.id | number | 該報刀頻道的ID | ✅ |
| clans.bossChannels.health | number | 該報刀頻道所對應的BOSS的滿血血量 | ✅ |
| mongo | object | MongoDB的連接設定，`broadcast`相關指令是將資料儲存在MongoDB，故如果沒有設定，將無法使用`broadcast`相關指令。 | |
| mongo.protocol | string | 僅支援`mongodb`或`mongodb+srv` | |
| mongo.host | string | MongoDB的主機名稱 | |
| mongo.port | number | MongoDB的通訊埠，預設是27017 | |
| mongo.user | string | MongoDB的使用者名稱 | |
| mongo.password | string | MongoDB的密碼 | |


## 相依套件

| 套件名稱 |
| --- |
| [discord.py](https://pypi.org/project/discord.py/) |
| [pytz](https://pypi.org/project/pytz/) |
| [pymongo](https://pypi.org/project/pymongo/)