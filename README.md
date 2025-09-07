![astrbot_plugin_akasha_terminal](https://socialify.git.ci/lqc-xhh/astrbot_plugin_akasha_terminal/image?description=1&font=Raleway&forks=1&issues=1&language=1&name=1&owner=1&pattern=Circuit%20Board&pulls=1&stargazers=1&theme=Auto)

# astrbot_plugin_akasha_terminal

[![GitHub](https://img.shields.io/badge/作者-Xinhaihai-FB7299)](https://github.com/Xinhaihai)
[![GitHub](https://img.shields.io/badge/作者-wbndm1234-FB7299)](https://github.com/wbndm1234)
[![GitHub](https://img.shields.io/badge/作者-MegSopern-FB7299)](https://github.com/MegSopern)

#
![:动态访问量](https://count.kjchmc.cn/get/@:astrbot_plugin_akasha_terminal)


一个功能丰富的astrbot插件，提供完整的游戏系统、JSON存储支持

## 🌟 主要功能

### 游戏系统
- **战斗系统**: 经验获取、等级提升、特权系统
- **情侣系统**: 表白、结婚、情侣任务、约会、决斗
- **商店系统**: 物品购买、背包管理
- **任务系统**: 每日任务、冒险任务
- **合成系统**: 物品合成、分解、工坊升级
- **家园系统**: 房屋建设、装饰

### 数据存储
- **JSON存储**: 传统文件存储方式
- **MySQL存储**: 高性能数据库存储
- **数据同步**: JSON与MySQL双向同步

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

## 🔧 配置说明

### 主配置 (config/cfg.js)
```javascript
export const cfg = {
  // 游戏配置
  game: {
    maxLevel: 100,
    expMultiplier: 1.0,
    cooldownEnabled: true
  }
}
```

## 🚨 注意事项

1. **安全性**
   - 定期备份数据库数据

2. **性能优化**
   - 定期清理过期的统计数据

3. **数据备份**
   - 定期备份JSON文件
   - 重要操作前建议先备份

## 📞 支持与反馈

如果遇到问题或有功能建议，请：
1. 检查日志文件获取详细错误信息
3. 验证依赖包是否正确安装

### 游戏说明🌈
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
  <h1 align="center" class="群友老婆"><i>分群游戏◧--娶群友❤?!</i></h1>
  <details><summary align="center">展开说明</summary>

  |功能   |描述   |
  |---|---|
  |随机娶群友   |随机娶一位群友,谁都可以   |
  |指定求婚   |娶指定的群友,不可以重婚   |
  |配合求婚   |愿意还是拒绝?   |
  |强娶指定群友   |强行掳走群友   |
  |抢老婆   |联动御前决斗进行抢婚决斗!!! 抢走群友的老婆!   |
  |主动分手,被动甩掉   |不要老婆或被老婆甩掉   |
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
  
  - 联系我们 Q群 1017886209或PR插件啦，球球了（修不动啊QAQ）
  </details>
   
   ## ❤️ 贡献
  - 这个是原[虚空插件](https://github.com/wbndm1234/trss-akasha-terminal-plugin) 仓库，感谢[倒霉](https://github.com/wbndm1234)许可他的插件让我们二改

  **提交 Bug 或建议**：
  - 通过 [GitHub Issues](https://github.com/lqc-xhh/astrbot_plugin_akasha_terminal/issues) 提交问题啦
  - 通过 [GitHub pull requests](https://github.com/lqc-xhh/astrbot_plugin_akasha_terminal/pulls) 提交PR啦
  - 可以来[QQ群](https://qm.qq.com/q/n0ewaCWIGk)玩玩来提点建议捏
  - astrbot的[帮助文档](https://astrbot.app)

   ## 📜 许可证
  - 本项目使用 AGPL-3.0 许可证开源
  
![Star History Chart](https://api.star-history.com/svg?repos=Xinhaihai-Xinhaihai/astrbot_plugin_akasha_terminal&type)
