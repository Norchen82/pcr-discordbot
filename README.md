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

#### Linux
1. 根據你的處理器架構下載`bikara-linux-amd64`或`bikara-linux-arm64`。
2. 在同一個目錄下建立`config.json`檔案。
3. 執行下載下來的bikara執行檔。

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
            ]
        },
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

## 競技場通知

本功能可以偵測指定玩家於1v1或3v3競技場排名變動並通知，作者本人並無追求競技場之排名，其功能實作僅僅是作為研究學習之用途。  
本功能可能存在違反遊戲公平性之原則，請斟酌使用。

### 前置作業

本功能的底層程式碼引用自 [azmiao/pcrjjc_tw_new](https://github.com/azmiao/pcrjjc_tw_new) 以及 [Ice9Coffee/HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot) 兩個專案，以下操作說明也是移植過來，你也可以直接參照原始專案(pcrjjc_tw_new)。


1. 拿個沒有在用的帳號登入公主連結，取得`data/data/tw.sonet.princessconnect/shared_prefs/tw.sonet.princessconnect.v2.playerprefs.xml`檔案。

注意：每個帳號至少得開啟加好友功能。

2. 給你的`tw.sonet.princessconnect.v2.playerprefs.xml`加上前綴名稱，例如：
```
美食殿堂：
first_tw.sonet.princessconnect.v2.playerprefs.xml
合服（真步／破曉／甜心）：
other_tw.sonet.princessconnect.v2.playerprefs.xml
```

3. 安裝相依套件：
```bash
pip install -r requirements.txt
```

4. 修改`account.json`文件來設定代理，如果不需要就將內容改成：
```json
{
    "proxy": {}
}
```

## 戰隊戰排名通知

本功能將偵測指定戰隊於戰隊戰之排名，並於每日結算前的50分於指定頻道通報當日結算排名。  
同時也可以設定指定的頻道，會在每個20/50分結算排名時，更改該頻道的名稱以方便即時獲得戰隊排名資訊。

### 前置作業

同**競技場通知**功能。

### 設定

在`config.json`中加入以下設定：
```json
{
    "clanBattleNotification": {
        "clans": [
            {
                "leaderViewerId": "戰隊會長的玩家十碼ID",
                "guildId": "Discord伺服器ID",
                "channelId": "Discord頻道ID",
                "threadId": "Discord討論串ID",
                "pollingChannelId": "要作為排名看板的Discord頻道ID",
                "pollingChannelName": "要作為排名看板的Discord頻道名稱",
                "updateOnStart": "每次啟動時是否立即檢查",
                "cron": "每日通報功能的指定時間"
            }
        ]
    }
}
```
| 欄位名稱 | 說明 |
| --- | --- |
| leaderViewerId | 戰隊戰會長遊戲的玩家十碼ID，因為無法取得每個戰隊的ID，所以只能用會長的ID作為判斷依據 |
| guildId | 填入使用這個Bot的Discord伺服器ID |
| channelId / threadId | 每日定期通報之功能，可以選擇要通報在指定頻道或是討論串，根據你的需求來決定要填入哪一個參數（二擇一） |
| pollingChannelId | 看板頻道ID，機器人會於每個20/50分來更新此頻道的名稱 |
| pollingChannelName | 名稱格式，在要顯示排名數字的地方加上`{rank}`。例如：`"即時排名：{rank}名"`，如果當下排名為99，則機器人會將頻道名稱改為「即時排名：99名」
| updateOnStart | 因為目前記錄的最後執行時間，在每次重啟機器人後就會遺失，故每次啟動機器人都會是一次全新的程序。此參數的目的是用於告訴機器人，啟動時的第一回檢查是否要馬上更新排名。 |
| cron | 指定每日要於什麼時候通報排名，格式為`小時 分鐘`，例如：`"04 50"`





## 相依套件

| 套件名稱 |
| --- |
| [discord.py](https://pypi.org/project/discord.py/) |
| [pytz](https://pypi.org/project/pytz/) |
| [pymongo](https://pypi.org/project/pymongo/) |