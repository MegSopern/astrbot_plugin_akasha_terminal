# astrbot_plugin_akasha_terminal

![astrbot_plugin_akasha_terminal](https://socialify.git.ci/MegSopern/astrbot_plugin_akasha_terminal/image?description=1&font=Raleway&forks=1&issues=1&language=1&name=1&owner=1&pattern=Circuit%20Board&pulls=1&stargazers=1&theme=Auto)

[![GitHub Author](https://img.shields.io/badge/作者-MegSopern-FB7299)](https://github.com/MegSopern)
[![GitHub Author](https://img.shields.io/badge/作者-Xinhaihai-FB7299)](https://github.com/Xinhaihai)
[![GitHub Author](https://img.shields.io/badge/作者-wbndmqaq-FB7299)](https://github.com/wbndmqaq)
[![License](https://img.shields.io/badge/license-GPL--3.0-green)](LICENSE)
![动态访问量](https://count.kjchmc.cn/get/@:astrbot_plugin_akasha_terminal)


## 🌟 项目简介

一个功能丰富的`astrbot`插件，提供完整的游戏系统与JSON存储支持，包含战斗、社交、任务等多样化玩法，适配社群互动场景。


## 🚀 核心功能

### 基础游戏系统
- **战斗系统**：经验获取、等级提升、特权解锁、战力对决
- **情侣系统**：表白、结婚、情侣任务、约会互动、离婚机制
- **商店系统**：物品购买、背包管理、道具使用
- **任务系统**：每日任务、冒险任务、成就达成与奖励
- **合成系统**：物品合成、分解、工坊升级
- **家园系统**：房屋建设、装饰个性化

## 📋 命令列表

### 游戏命令
| 命令 | 说明 |
|------|------|
| `#战斗` | 进行战斗获取经验 |
| `#我的信息` | 查看个人信息 |
| `#表白 @用户` | 向其他用户表白 |
| `#结婚 @用户` | 与其他用户结婚 |
| `#离婚` | 解除婚姻关系 |
| `#商店` | 查看商店物品 |
| `#购买 物品名` | 购买物品 |
| `#背包` | 查看背包物品 |
| `#任务` | 查看可用任务 |
| `#冒险` | 进行冒险任务 |
| `#合成 物品名` | 合成物品 |
| `#分解 物品名` | 分解物品 |

### 🌈老虚空说明
  游戏说明
  使用#虚空帮助 查看具体说明

  <h1 align="center"><i>游戏管理⚙</i></h1>
  <details><summary align="center">展开说明</summary>

  |功能   |描述   |
  |---|---|
  |时间管理   |重置群内或指定人被计入的时间     |
  |权限管理   |设置或移除指定人的特殊权限   |
  |功能管理   |手动开启一些预先设定好的功能计划   |
  |存档管理   |一键删除错误的存档   |

  </details>
  <h1 align="center" class="群友伴侣"><i>分群游戏◧--娶群友❤?!</i></h1>
  <details><summary align="center">展开说明</summary>

  |功能   |描述   |
  |---|---|
  |随机娶群友   |随机娶一位群友,谁都可以   |
  |指定求婚   |娶指定的群友,不可以重婚   |
  |配合求婚   |愿意还是拒绝?   |
  |强娶指定群友   |强行掳走群友   |
  |抢伴侣   |联动御前决斗进行抢婚决斗!!! 抢走群友的伴侣!   |
  |主动分手,被动甩掉   |不要伴侣或被伴侣甩掉   |
  |获取金币   |凡是都是需要付出的   |
  |花金币   |钱不能白赚   |
  |随机事件   |处处有惊喜   |
  |查看家庭   |看看和群友构建的家   |
  |开银啪   |牛牛冲!   |
  |更多功能   |敬请期待。或提交Issues   |

  </details>

  <h1 align="center"><i>全局游戏⚪--御前决斗🗡!</i></h1>
  <details><summary align="center">展开说明</summary>

  |功能   |描述   |
  |---|---|
  |决斗系统   |与一名群友开始决斗     |
  |经验系统   |通过各种方式提升经验,突破境界   |
  |战力系统   |战斗时根据战力决定胜率   |
  |签到&委托系统   |做做日常,签个到领取奖励   |
  |抽武器   |抽取武器 后续将加入战力   |
  |更多功能   |敬请期待。或提交Issues   |

  </details>

  <h1 align="center"><i>测试插件😜!</i></h1>
  <details><summary align="center">展开说明</summary>

  |将实现   |描述   |
  |---|---|
  |随机生成cp文   |奇妙的cp文？()     |

  </details>

  - 上述方法未能解决或我有其他问题!
  
  - 联系我们或PR插件啦，球球了（修不动啊QAQ）
  </details>

## 📝 更新日志
### v2.1.1
[2025.10.19]
- 📌用 fcntl/msvcrt 原生锁替换 filelock，消除 .lock 文件并保证跨平台原子读写
- 🛠️修复多个更新至v2.1.0后浮现出的新bug

### v2.1.0
[2025.10.18]
- ✨核心功能新增：
  - 全新决斗系统上线，支持玩家间发起对决，新增/决斗（别名：发起决斗、御前决斗等）命令，可通过@用户/qq号指定对手
  - 新增/设置战斗力系数命令，支持调整决斗战力计算参数
- 🛠️ 系统优化与重构：
  - 全面重构用户数据管理模块，提升数据处理效率与稳定性
  - 清理抽卡模块中冗余重复逻辑，减少代码冗余
  - 整体优化代码结构，增强项目可维护性与运行性能
- 📌作者信息更新：原作者wbndm1234调整为wbndmqaq

### v2.0.5
[2025.10.16]
- ✨新增功能
  - 新增管理员命令 “刷新商城”（别名：刷新商店、刷新虚空商店、刷新虚空商城）：支持管理员手动刷新商城物品列表，便于及时更新商店内容
  - “道具详情” 命令（别名：道具详细、物品详情、物品详细）：支持用户查询指定道具的详细信息，使用方法为/道具详情 物品名称，提升道具信息透明度
- ⚡️优化：“赠送道具” 命令的内部参数处理逻辑，增强命令执行的稳定性与兼容性
### v2.0.1
[2025.10.15]
- ✨功能增强：
  - 实现道具增益效果与神秘盒子机制，包括爱情加成、随机金钱奖励、保护状态、运气 / 工作增益等
  - 扩展命令别名：为 "十连抽武器" 和 "# 我的信息" 增加更多易用别名

- 🔧 问题修复：修复抽卡冷却配置异常问题，确保抽卡冷却机制准确生效

### v2.0.0
[2025.10.2]
- ✨新增家园系统：支持房屋建设与装饰
- 🛠️优化武器系统：战力计算逻辑调整，新增等级特权
- 🔧扩展任务系统：增加周常任务与成就体系
- 🔧修复已知BUG：解决部分场景下数据存储异常问题

### v1.0.0
[2025.9.19]
- 🚀初始版本发布，包含核心功能：
  - 用户、商店、任务基础系统
  - 基础游戏管理工具与数据存储支持

  ## 📞 支持与反馈

若遇到问题或有功能建议，请按以下步骤操作：
1. 检查日志文件获取详细错误信息
2. 验证依赖包是否正确安装
3. astrbot的[帮助文档](https://astrbot.app)
4. 上述方法未解决？通过以下方式联系我们：
   - 提交 [GitHub Issues](https://github.com/MegSopern/astrbot_plugin_akasha_terminal/issues)
   - 提交 [GitHub PR](https://github.com/MegSopern/astrbot_plugin_akasha_terminal/pulls)
   - 加入 [QQ群](https://qm.qq.com/q/9rouZu1qog) 交流建议

  ## ❤️ 贡献指南
本项目基于 [原虚空插件](https://github.com/wbndmqaq/trss-akasha-terminal-plugin) 二次开发，感谢 [倒霉](https://github.com/wbndmqaq) 的许可支持。

欢迎通过以下方式贡献：
- 报告BUG或提出功能建议（见「支持与反馈」）
- 提交代码PR，参与功能开发
- 完善文档或翻译内容

---

## 🌟 贡献者

感谢所有为 astrbot_plugin_akasha_terminal 项目做出贡献的朋友们！

[![GitHub Contributors](https://img.shields.io/github/contributors/MegSopern/astrbot_plugin_akasha_terminal?style=flat-square)](https://github.com/MegSopern/astrbot_plugin_akasha_terminal/graphs/contributors)

<a href="https://github.com/MegSopern/astrbot_plugin_akasha_terminal/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=MegSopern/astrbot_plugin_akasha_terminal" alt="Contributor List" />
</a>

---

## 📜 许可证

本项目采用 [GPL-3.0 许可证](LICENSE) 开源，详情请查阅许可证文件
  
![Star History Chart](https://api.star-history.com/svg?repos=MegSopern/astrbot_plugin_akasha_terminal&type)
