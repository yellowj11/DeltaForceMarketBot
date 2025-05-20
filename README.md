# DFMarketBot
三角洲行动交易行自动钥匙卡、弹药，通过OCR+模拟鼠标点击实现自动购买。
### 功能特点
- 自动监控并购买指定钥匙卡和弹药
- 基于价格智能判断是否购买
- 支持多地图切换
- 适配不同分辨率(16:9)及多显示器
- 详细日志记录购买历史

### 快速开始
#### 安装步骤
1. 初始化
```bash
   uv venv -p 3.12
   uv sync
```
2. 安装 [tesseract](https://github.com/tesseract-ocr/tesseract ):

    - 下载地址：https://digi.bib.uni-mannheim.de/tesseract/
    - 安装时可以选择需要的语言包：
      
      ![Image](https://github.com/user-attachments/assets/53a513f1-34a1-45bf-a7f9-cfd5b5b74a07)

3. 修改 Tesseract 路径
```bash
# 在 main.py 中更新为您的安装路径
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 配置
编辑 config/buy_items_info.json 文件，根据需要配置要购买的钥匙卡和弹药。

### 运行
```bash
python main.py
```
- F8: 开始自动购买
- F9: 停止自动购买

### 界面预览
开始运行前，需要保证交易行按钮无遮挡鼠标能点到

![Image](https://github.com/user-attachments/assets/19dd5e96-c969-4d5c-bed1-7497e79f87ca)

### 配置文件说明
```json
{
   "key_cards": {
    "ling_hao_da_ba": [
      {
        "name": "变电站宿舍",          // 名称，需与游戏保持一致
        "position_id": "5-1",         // 记录坐标位置为第一行第二个，后续支持映射position
        "base_price": 39337,          // 目标卡牌参考价格
        "ideal_price": 35700,         // 理想购买价格
        "position": [0.3477,0.8035],  // 屏幕坐标比例
        "want_to_buy": "true",        // 是否加入监控
        "buy_max_one_time": "false",  // 点击购买前拉满数量
        "buy_times_limit": 1,         // 购买次数限制
        "buyed_times": 0              // 已购买次数
      }
    ]
  },
  "bullets": {}  // 弹药配置
}
```

### 购买逻辑
1. 程序会在以下情况自动购买:
2. 当前价格低于理想购买价格
3. 溢价低于10%
4. 负溢价(当前价格低于基准价格)

### 调试工具

运行 debug.py 可实时获取鼠标坐标，帮助您配置新的钥匙卡位置:

```bash
python debug.py
```

如获取坐标 58.21%,21.25%，则在配置文件中填写 [0.5821,0.2125]。

### 常见问题
1.截图区域不正确
> 确认屏幕分辨率为16:9比例

2.点击无效/无法获取截图
> 使用管理员权限运行命令提示符(CMD)

### 免责声明
本脚本仅供学习和研究目的使用，作者不对因使用该脚本而导致的任何后果负责。使用风险完全由用户自行承担。
- 脚本设计为非侵入性,但使用第三方工具可能违反游戏平台使用条款
- 使用可能导致账号被封禁或其他形式的处罚
- 作者不保证脚本的稳定性、安全性或合法性
本脚本基于@sheldon1998大佬基础上进行修改：https://github.com/sheldon1998/DeltaForceKeyBot
