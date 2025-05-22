# DFMarketBot
三角洲行动交易行自动补卡、补子弹，通过OCR+模拟鼠标点击实现自动购买。
### 功能特点
- 自动监控并购买指定钥匙卡和弹药
- 基于价格智能判断是否购买
- 适配不同分辨率(16:9)及多显示器
- 详细日志记录购买历史

### 效果预览
![功能演示](./img/preveiw.gif)

### DFMarketBot 项目目录结构

#### 根目录

- 📂 `config/` - 配置文件目录

- 📂 `img/` - 图像资源目录

- 📂 `log/` - 日志文件目录

- 📄 `.gitignore` - Git忽略文件配置

- 📄 `.python-version` - Python版本配置

- 📄 `debug.py` - 调试工具（获取鼠标坐标）

- 📄 `main.py` - 主程序

- 📄 `pyproject.toml` - 依赖

- 📄 `README.md` - 说明文档

- 📄 `uv.lock` - 依赖锁定文件

### 快速开始
#### 安装步骤
1. 初始化
```bash
   uv venv -p 3.12
   uv sync
```
2. ~~安装 [tesseract](https://github.com/tesseract-ocr/tesseract ):~~

    - ~~下载地址：https://digi.bib.uni-mannheim.de/tesseract/~~
    - ~~安装时可以选择需要的语言包：~~
      
      ~~![Image](https://github.com/user-attachments/assets/53a513f1-34a1-45bf-a7f9-cfd5b5b74a07)~~

3. ~~修改 Tesseract 路径~~
```bash
# 在 main.py 中更新为您的安装路径
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```



### 运行
```bash
python main.py
```
- F8: 开始自动购买
- F9: 停止自动购买

### 注意
- 开始运行前，需要保证交易行按钮无遮挡鼠标能点到
- 运行期间屏幕切勿有其他窗口遮挡，会影响鼠标点击

![Image](https://github.com/user-attachments/assets/19dd5e96-c969-4d5c-bed1-7497e79f87ca)

### 配置
编辑 config/buy_items_info.json 文件，根据需要配置要购买的钥匙卡和弹药。

### 配置文件说明
需要购买的物品信息，配置文件示例如下：
```json
{
   "key_cards": {
    "ling_hao_da_ba": [
      {
        "name": "变电站宿舍",          // 名称，需与游戏保持一致
        "ideal_price": 35700,         // 理想购买价格
        "position": "1-2",            // 物品在商城的位置，第一行第二列
        "want_to_buy": "true",        // 是否加入监控
        "one_time_buy_num": "low",    // 单次购买数量设置，low:1,medium:2,high:3
        "buy_times_limit": 1,         // 购买次数限制
        "buyed_times": 0              // 已购买次数
      }
    ]
  },
  "bullets": {
	  "9x19mm": [
	      {
	        "name": "9x19mm PSO",
	        "ideal_price": 30,
	        "position": "2-2",
	        "want_to_buy": "true",
	        "one_time_buy_num": "low",    // 单次购买数量设置，low:10,medium:100,high:200
	        "buy_times_limit": 5,
	        "buyed_times": 0
	      }
	    ]
  }
}
```
![Image](https://github.com/user-attachments/assets/3c06b194-6040-4efb-94ec-3410a0f4de49)
![Image](https://github.com/user-attachments/assets/b826c458-548b-47ac-8293-b27cdb06872b)
### 价格判断说明

DFMarketBot采用智能价格判断系统，确保以最优价格购买物品。

#### 核心参数

- 理想价格：您期望购买的最佳价格

- 当前价格：系统实时识别到的市场价格

- 最高溢价比例：允许高于参考价格的最大比例（默认10%）

#### 溢价计算方式
溢价公式（%）：((当前价格 / 理想价格) - 1) * 100

系统会根据您设置的理想价格计算基准：

- 以理想价格为基准计算溢价

- 允许的最高价格为理想价格上浮10%


#### 购买条件

系统在满足以下任一条件时会执行购买：

- 优惠价格：当前价格低于您设定的理想价格

- 负溢价：当前价格低于计算基准

- 合理溢价：当前价格溢价不超过设定的最高溢价（默认10%）

#### 运作流程

- 系统识别市场中物品的实时价格

2. 计算价格溢价率并与最高可接受价格比较

- 记录详细价格信息到日志以便追踪

- 根据购买条件自动决定是否购买

- 购买成功后更新交易记录


### 调试工具

运行 debug.py 可实时获取鼠标坐标，帮助您配置新的钥匙卡位置:

```bash
python debug.py
```

~~如获取坐标 58.21%,21.25%，则在配置文件中填写 [0.5821,0.2125]。~~
现已支持坐标映射，非必要不需要修改


### 更新
#### 2025-5-21
1. tesseract识别中文效果一般，ocr库替换为更轻量级的ddddocr（把项目下的.venv文件夹删除，重新初始化,2025-5-21之后忽略）
2. 支持购买子弹
3. 新增支持坐标映射，详见==配置文件说明==
4. 购买逻辑优化，详见==购买逻辑==
5. 购买物品信息记录到excel，如下图：
![购买物品信息](https://github.com/user-attachments/assets/b4e0ada0-efde-443d-acae-dfe8c1d10cc8)

#### 2025-5-22
1. 新增支持单次购买数量设置，详见==配置文件说明==
2. 优化购买逻辑，去掉基准价格，详见==购买逻辑==

### 常见问题
1.截图区域不正确
> 确认屏幕分辨率为16:9比例

2.点击无效/无法获取截图
> 使用管理员权限运行命令提示符(CMD)

### ==免责声明==
==本脚本仅供学习和研究目的使用，作者不对因使用该脚本而导致的任何后果负责。使用风险完全由用户自行承担。==
- ==脚本设计为非侵入性,但使用第三方工具可能违反游戏平台使用条款==
- ==使用可能导致账号被封禁或其他形式的处罚==
- ==作者不保证脚本的稳定性、安全性或合法性==
==本脚本基于@sheldon1998大佬基础上进行修改：https://github.com/sheldon1998/DeltaForceKeyBot==
