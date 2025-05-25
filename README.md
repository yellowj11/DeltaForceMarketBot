# DFMarketBot
三角洲行动交易行自动补卡、补子弹，通过OCR+模拟鼠标点击实现自动购买。


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
2. 安装 [tesseract](https://github.com/tesseract-ocr/tesseract ):

    - 下载地址：https://digi.bib.uni-mannheim.de/tesseract/
    - 安装时可以选择需要的语言包：
      
      ![Image](https://github.com/user-attachments/assets/53a513f1-34a1-45bf-a7f9-cfd5b5b74a07)

3. 修改 Tesseract 路径
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
- 运行前，请手动调节游戏显示模式到窗口模式（适配了无窗口模式，但是为了较高识别率，请使用窗口模式），脚本已调整分辨率适配方案，会将游戏窗口调整至1920*1080

![Image](https://github.com/user-attachments/assets/07674b92-a3c8-4c61-babc-9685e080a789)
- 运行期间，需要保证交易行按钮无遮挡鼠标能点到
- 运行期间屏幕切勿有其他窗口遮挡，会影响鼠标点击


![Image](https://github.com/user-attachments/assets/19dd5e96-c969-4d5c-bed1-7497e79f87ca)

### 配置
- 运行前请编辑 config/buy_items_info.json 文件，根据需要配置要购买的钥匙卡和弹药。
- 非必要，请不要修改config/sys_info.json文件

### 配置文件说明
1. 需要购买的物品信息，buy_items_info.json示例如下：
```json
{
   "key_cards": {
    "ling_hao_da_ba": [               // 房卡、子弹类型，房卡用拼音，子弹直接照抄
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
以下为坐标映射示例：
```json
"position_mapping": {
        "1-1": [0.3,0.2],
        "1-2": [0.6,0.2],
        "1-3": [0.8,0.2],
        "2-1": [0.3,0.35],
        "2-2": [0.6,0.35],
        "2-3": [0.8,0.35],
        "3-1": [0.3,0.5],
        "3-2": [0.6,0.5],
        "3-3": [0.8,0.5],
        "4-1": [0.3,0.65],
        "4-2": [0.6,0.65],
        "4-3": [0.8,0.65],
        "5-1": [0.3,0.8],
        "5-2": [0.6,0.8],
        "5-3": [0.8,0.8],
        "6-1": [0.3,0.9],
        "6-2": [0.6,0.9],
        "6-3": [0.8,0.9]
    },
```
![Image](https://github.com/user-attachments/assets/b826c458-548b-47ac-8293-b27cdb06872b)
2. sys_info.json示例如下：
```json
{
    "windows_resize": [1920, 1080],   // 游戏窗口分辨率，锁定1080p
    "position_mapping": {             // 坐标映射，非必要，请不要修改
        "1-1": [0.3,0.2],
        "1-2": [0.6,0.2],
        "1-3": [0.8,0.2],
        "2-1": [0.3,0.35],
        "2-2": [0.6,0.35],
        "2-3": [0.8,0.35],
        "3-1": [0.3,0.5],
        "3-2": [0.6,0.5],
        "3-3": [0.8,0.5],
        "4-1": [0.3,0.65],
        "4-2": [0.6,0.65],
        "4-3": [0.8,0.65],
        "5-1": [0.3,0.8],
        "5-2": [0.6,0.8],
        "5-3": [0.8,0.8],
        "6-1": [0.3,0.9],
        "6-2": [0.6,0.9],
        "6-3": [0.8,0.9]
    },
    "item_name_region":{             // 物品名称截图区域坐标映射
        "window":{                    // 窗口模式
            "left": 0.758,
            "top": 0.165,
            "width": 0.17,
            "height": 0.035
        },
        "borderless_window":{          // 无窗口模式
            "left": 0.768,
            "top": 0.145,
            "width": 0.17,
            "height": 0.035
        }
    },
    "item_price_region":{             // 物品价格截图区域坐标映射
        "window":{                    // 窗口模式
            "left": 0.165,
            "top": 0.175,
            "width": 0.08,
            "height": 0.04
        },
        "borderless_window":{          // 无窗口模式
            "left": 0.153,
            "top": 0.153,
            "width": 0.08,
            "height": 0.04
        }   
    },
    "buy_button_position":{             // 购买按钮位置坐标映射
        "key_card":{                    // 房卡
            "window":{                  // 窗口模式
                "high": [0.8948,0.772],
                "medium": [0.8365,0.772],
                "low": [0.7835,0.772],
                "buy": [0.85,0.85]
            },
            "borderless_window":{          // 无窗口模式
                "high": [0.91,0.772],
                "medium": [0.85,0.772],
                "low": [0.7935,0.772],
                "buy": [0.85,0.85]
            }
        },
        "bullet":{                      // 子弹
              "window":{                  // 窗口模式
                "high": [0.8948,0.72],
                "medium": [0.8365,0.72],
                "low": [0.7865,0.72],
                "buy": [0.85,0.8]
            },
            "borderless_window":{          // 无窗口模式
                "high": [0.91,0.72],
                "medium": [0.8493,0.72],
                "low": [0.7975,0.72],
                "buy": [0.85,0.8]
            }
        }
    },
    "one_time_buy_num_mapping" :{        // 单次购买数量映射
        "key_card": {                    // 房卡
            "low": 1, 
            "medium": 2,
            "high": 3
        },
        "bullet": {                      // 子弹
            "low": 10,
            "medium": 100,
            "high": 200
        }
    },
    "name_cn_mapping": {                // 房卡名称映射
        "chang_gong_xi_gu": "长工溪谷",
        "ling_hao_da_ba": "零号大坝",
        "hang_tian_ji_di": "航天基地",
        "ba_ke_shi": "巴克什"
    },
    "menu_button_img_path_mapping":{    // 菜单按钮图片路径映射
        "yaoshi": "img/yaoshi.png",
        "danyao": "img/danyao.png",
        "jiaoyihang": "img/jiaoyihang.png",
        "buy_menu": "img/buy_menu.png",
        "buy_succeed": "img/buy_succeed.png",
        "buy_failed": "img/buy_failed.png"
    },
    "max_time_per": 600,
    "max_premium_percent": "10%"
}
```

### 价格判断说明

DFMarketBot采用智能价格判断系统，确保以最优价格购买物品。
如下图所示，ocr会识别物品名称和价格，然后根据配置文件中的理想价格、当前价格、最高溢价比例进行判断是否购买。
![Image](https://github.com/user-attachments/assets/9c8eebe1-f155-4348-9eb3-d945cb3096cd)
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

- 计算价格溢价率并与最高可接受价格比较

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

#### 2025-5-25
1. 修复物品一次购买数量映射错误问题（high low ，购买却用的是min和max）
2. 修复分辨率不适配1080p问题
3. 修复1080p下ocr准确度低

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

脚本是闲暇写的娱乐脚本，功能尚未完善，当前为demo版本，有很多漏洞等待修复，敬请见谅.

### 画饼
- 增加ui界面
