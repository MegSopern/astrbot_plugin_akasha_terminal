//随便写的,大佬勿喷 初版@鸢:随机娶群友，指定娶群友
import { BotApi, AlemonApi, plugin } from '../../model/api/api.js'
import fs from 'fs'
import Config from '../../model/Config.js'
import cfg from '../../../../lib/config/config.js'
import moment from "moment"
import command from '../../components/command.js'
import dataManager from '../../components/data_manager.js'
import { QuestSystem } from '../../components/quest_system.js'

// 兼容
if (!global.segment) {
    try {
        global.segment = (await import("icqq")).segment
    } catch {
        global.segment = {
            at: (qq) => `[CQ:at,qq=${qq}]`,
            image: (url) => `[CQ:image,file=${url}]`
        }
    }
}

// 检查Redis可用性
function isRedisAvailable() {
    return global.redis && typeof global.redis.get === 'function'
}

// 获取redis实例
function getRedis() {
    return global.redis
}

const dirpath2 = "plugins/trss-akasha-terminal-plugin/data/UserData";//文件夹路径
let Magnification = await command.getConfig("duel_cfg", "Magnification");

const giftpath = `plugins/trss-akasha-terminal-plugin/resources/qylp/giftthing.json`
const housepath = `plugins/trss-akasha-terminal-plugin/resources/qylp/house.json`
const lotterypath = `plugins/trss-akasha-terminal-plugin/resources/qylp/lottery.json`
const inpapath = `plugins/trss-akasha-terminal-plugin/resources/qylp/inpa.json`
const workpath = `plugins/trss-akasha-terminal-plugin/resources/qylp/work.json`
const currentTime = moment(new Date()).format('YYYY-MM-DD HH:mm:ss')
let cdTime = Number(await command.getConfig("wife_cfg", "sjcd")) * 60;//随机娶群友冷却
let cdTime2 = Number(await command.getConfig("wife_cfg", "qqcd")) * 60;//强娶冷却
let cdTime3 = Number(await command.getConfig("wife_cfg", "dgcd")) * 60;//打工冷却
let cdTime4 = Number(await command.getConfig("wife_cfg", "bbcd")) * 60;//抱抱冷却
let cdTime5 = Number(await command.getConfig("wife_cfg", "ggcd")) * 60;//逛街冷却
let cdTime6 = Number(await command.getConfig("wife_cfg", "qlpcd")) * 60;//抢老婆冷却
let cdTime7 = Number(await command.getConfig("wife_cfg", "poorcd")) * 60;//低保冷却
let cdTime8 = Number(await command.getConfig("wife_cfg", "RBBgetcd")) * 60;//获取虚空彩球的cd
let qqwife = await command.getConfig("wife_cfg", "qqwife");//强娶概率
let sjwife = await command.getConfig("wife_cfg", "sjwife");//随机概率
let gifttime = await command.getConfig("wife_cfg", "gifttime");//逛街换地上限
export class qqy extends plugin {
    constructor() {
        super({
            name: '娶群友',
            dsc: '娶群友',
            event: 'message',
            priority: 66,
            rule: [{
                reg: "^#?(娶群友|娶老婆|娶群友老婆|娶群主|找老公)(.*)$",
                fnc: 'wife'
            },
            {
                reg: '^#?抢老婆$',
                fnc: 'ntr'
            },
            {
                reg: '^#?(抢劫|抢银行)$',
                fnc: 'Robbery'
            },
            {
                reg: '^#?我愿意$',
                fnc: 'yy'
            },
            {
                reg: '^#?我拒绝$',
                fnc: 'jj'
            },
            {
                reg: '^#?(闹离婚|甩掉|分手)$',
                fnc: 'breakup'
            },
            {
                reg: '^#?踢出银啪$',
                fnc: 'nofuck'
            },
            {
                reg: '^#?退出银啪$',
                fnc: 'fuckno'
            },
            {
                reg: '^#?(家庭信息|我的(老婆|老公|对象))(.*)$',
                fnc: 'read'
            },
            {
                reg: '^#?(打工赚钱|打工)(.*)$',
                fnc: 'getmoney'
            },
            {
                reg: '^#?(工作状态|打工状态)$',
                fnc: 'workstatus'
            },
            {
                reg: '^#?(工作记录|打工记录)$',
                fnc: 'workhistory'
            },
            {
                reg: '^#?住所改名',
                fnc: 'namedhouse'
            },
            {
                reg: '^#?看房$',
                fnc: 'gethouse'
            },
            {
                reg: '^#?买房[0-9]{1,}$',
                fnc: 'buyhouse'
            },
            {
                reg: '^#?逛街$',
                fnc: 'gift'
            },
            {
                reg: '^#?进去看看$',
                fnc: 'gift_continue'
            },
            {
                reg: '^#?去下一个地方$',
                fnc: 'gift_over'
            },
            {
                reg: '^#?回家$',
                fnc: 'gohome'
            },
            {
                reg: '^#?获取虚空彩球([0-9][0-9](?:\\s)){6}[0-9][0-9]$',
                fnc: 'lottery1'
            },
            {
                reg: '^#?我的彩票$',
                fnc: 'readRBB'
            },
            {
                reg: '^#?虚空彩球兑换$',
                fnc: 'useRBB'
            },
            {
                reg: '^#?(拥抱|抱抱)(.*)$',
                fnc: 'touch'
            },
            {
                reg: '^#?开始银啪$',
                fnc: 'fk'
            },
            {
                reg: '^#?领取低保$',
                fnc: 'poor'
            },
            {
                reg: '^#?上交存款[0-9]{1,}$',
                fnc: 'Transfer_money'
            },
            {
                reg: '^#?(虚空)(时间重置|重置时间)$',
                fnc: 'delREDIS'
            },
            {
                reg: '^#?虚空清除无效存档$',
                fnc: 'delerrdata'
            },
{
            reg: "^#?去城市$",
            fnc: "goToCity"
        },
        {
            reg: "^#?去商业区$",
            fnc: "goToBusiness"
        },
        {
            reg: "^#?去银行$",
            fnc: "goToBank"
        },
        {
            reg: "^#?回家$",
            fnc: "goHome"
        },
        {
            reg: "^#?(查看|当前)位置$",
            fnc: "checkLocation"
        }
            ]
        })
        this.dataManager = dataManager
    }
    
   
    //银啪
    async fk(e){
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var inpajson = await dataManager.getUserxiaoqie(id)
        var inpathing = await dataManager.loadJsonData(inpapath);//读取位置资源文件
        if(!homejson[id].s) return e.reply(`你没有老婆,也没有小妾,你隔这开什么inpact??导管吗`)
        
        // 安全检查：确保inpajson和用户数据存在
        if (!inpajson || !inpajson[id]) {
            return e.reply(`数据异常，请稍后再试`)
        }
        
        // 安全检查：确保inpajson和用户数据存在
        if (inpajson && inpajson[id] && inpajson[id].fuck) {
            if(homejson[id].s && !inpajson[id].fuck.includes(homejson[id].s))
              inpajson[id].fuck.push(homejson[id].s)
            var ren = inpajson[id].fuck.length
            let msg = []
            if(!inpajson[id].kun){
              inpajson[id].kun = Math.round(Math.random()*11 + 1)
              msg.push(`你还没有牛牛,让神赐予你吧`)
              msg.push(`恭喜你,你的牛牛初始值为${inpajson[id].kun}cm`)
            }
            let kunup = ren * (Math.round(Math.random()*1 + 1)/10)
            inpajson[id].kun += kunup
            inpajson[id].fucktime = (inpajson[id].fucktime || 0) + 1
             let wifename = await this.people(e, "nickname", homejson[id].s)
             let username = await this.people(e, "nickname", id)
             let inpajq = await inpathing.test[Object.keys(inpathing.test)[Math.round(Math.random() * ((Object.keys(inpathing.test)).length - 1) + 1)]]
             console.log(inpathing.test)
             console.log(Object.keys(inpathing.test))
             console.log(inpajq)
             inpajq = await inpajq.replace(/user/g, username)
             inpajq = await inpajq.replace(/wife1/g, wifename)
             msg.push(inpajq)
             msg.push(`你本次邀请了${ren}位群友参加银啪,\n牛牛长长了${kunup}cm,\n目前为${inpajson[id].kun}cm`)
             await dataManager.saveUserxiaoqie(id, inpajson[id])
             Config.getforwardMsg(msg, e)
         } else {
             e.reply(`数据异常，请稍后再试`)
             return
         }
}
    //抢老婆
    async ntr(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var targetId = e.at
        
        if (e.atme || e.atall) {
            e.reply(`6🙂`)
            return
        }
        
        if (!targetId) {
            e.reply(`请at你想抢夺老婆的人！`)
            return
        }
        
        // 检查是否被禁闭或死亡
        if (await this.is_killed(e, 'ntr', true) == true) return
        
        // 获取各种数据
        var homejson = await this.dataManager.getUserHome(id)
        var targetHomejson = await this.dataManager.getUserHome(targetId)
        var battlejson = await this.dataManager.getUserBattle(id)
        var targetBattlejson = await this.dataManager.getUserBattle(targetId)
        var placejson = await this.dataManager.getUserPlace(id)
        var housejson = await this.dataManager.getUserHouse(id)
        
        // 检查目标是否有老婆
        if (!targetHomejson[targetId] || targetHomejson[targetId].s === 0) {
            e.reply([global.segment.at(id), "\n目标还是单身，没有老婆可以抢夺！"])
            return
        }
        
        // 检查自己是否已有老婆
        if (homejson[id].s !== 0 && homejson[id].s !== undefined && homejson[id].s !== null && homejson[id].s !== '') {
            e.reply([global.segment.at(id), "\n你已经有老婆了，不能再抢夺别人的老婆！"])
            return
        }
        
        // 检查冷却时间
        let UserPAF = battlejson[id].Privilege
        if (isRedisAvailable()) {
            const redisClient = getRedis();
            let lastTime = await redisClient.ttl(`akasha:wife-ntr-cd:${e.group_id}:${id}`);
            if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
                e.reply([global.segment.at(id), "\n", `你的牛头人冷却时间还有${lastTime}秒哦~`])
                return true
            }
        } else if (!UserPAF && !this.checkDevPermission(e)) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查冷却时间"])
            return true
        }
        
        // 位置影响成功率
        let userPlace = placejson[id] || { place: 'home' }
        let locationBonus = 0
        if (userPlace.place === 'city' || userPlace.place === 'business') {
            locationBonus = 0.1 // 在城市或商业区更容易成功
        }
        
        // 计算成功率：基于金币、战力、房屋、好感度
        let attackerPower = battlejson[id].attack + battlejson[id].defense
        let defenderPower = targetBattlejson[targetId].attack + targetBattlejson[targetId].defense
        let moneyRatio = homejson[id].money / (targetHomejson[targetId].money + 1)
        let loveInfluence = Math.max(0, (1000 - targetHomejson[targetId].love) / 1000)
        let houseBonus = housejson[id] ? housejson[id].loveup * 0.05 : 0
        let powerRatio = attackerPower / (defenderPower + 1)
        
        let successRate = Math.min(0.8, Math.max(0.1, 
            0.3 + (moneyRatio * 0.2) + (loveInfluence * 0.3) + 
            (powerRatio * 0.15) + houseBonus + locationBonus
        ))
        
        let isSuccess = Math.random() < successRate
        
        if (isSuccess) {
            // 抢夺成功
            let wifeId = targetHomejson[targetId].s
            let wifeName = await this.people(e, 'nickname', wifeId)
            
            // 转移老婆关系
            homejson[id].s = wifeId
            homejson[id].love = Math.round(targetHomejson[targetId].love * 0.3) // 继承部分好感度
            targetHomejson[targetId].s = 0
            targetHomejson[targetId].love = 0
            
            // 更新老婆的数据
            var wifeHomejson = await this.dataManager.getUserHome(wifeId)
            if (wifeHomejson[wifeId]) {
                wifeHomejson[wifeId].s = id
                wifeHomejson[wifeId].love = homejson[id].love
                await this.dataManager.saveUserHome(wifeId, wifeHomejson[wifeId])
            }
            
            // 获得经验和金币奖励
            battlejson[id].experience += 100
            homejson[id].money += 500
            
            await this.dataManager.saveUserHome(id, homejson[id])
            await this.dataManager.saveUserHome(targetId, targetHomejson[targetId])
            await this.dataManager.saveUserBattle(id, battlejson[id])
            
            e.reply([
                global.segment.at(id), "\n",
                `🎉 牛头人成功！你抢走了 ${wifeName}！\n`,
                `💖 继承好感度: ${homejson[id].love}\n`,
                `💰 获得奖励: 500金币\n`,
                `✨ 获得经验: 100点`
            ])
            
            const redisClient2 = getRedis();
            await redisClient2.setex(`akasha:wife-ntr-cd:${e.group_id}:${id}`, 7200, "1") // 2小时冷却
            return
        } else {
            // 抢夺失败，触发惩罚
            await this.ntrF(e, id, targetId, 'ntr')
            const redisClient3 = getRedis();
            await redisClient3.setex(`akasha:wife-ntr-cd:${e.group_id}:${id}`, 3600, "1") // 失败冷却1小时
            return
        }
    }
    //打劫或者抢银行
    async Robbery(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var targetId = e.at
        
        if (e.atme || e.atall) {
            e.reply(`6🙂`)
            return
        }
        
        // 检查是否被禁闭或死亡
        if (await this.is_killed(e, 'Robbery', true) == true) return
        
        // 获取各种数据
        var homejson = await this.dataManager.getUserHome(id)
        var battlejson = await this.dataManager.getUserBattle(id)
        var placejson = await this.dataManager.getUserPlace(id)
        var housejson = await this.dataManager.getUserHouse(id)
        
        // 检查位置限制
        let userPlace = placejson[id] || { place: 'home' }
        if (userPlace.place === 'prison') {
            e.reply([global.segment.at(id), "\n你在监狱里，无法进行抢劫！"])
            return
        }
        
        // 银行抢劫模式
        if (!targetId) {
            return await this.robberyBank(e, id, homejson, placejson, battlejson, housejson)
        }
        
        // 抢劫玩家模式
        return await this.robberyPlayer(e, id, targetId, homejson, placejson, battlejson, housejson)
    }
    
    async robberyBank(e, id, homejson, placejson, battlejson, housejson) {
        // 银行抢劫需要在城市或商业区
        let userPlace = placejson[id] || { place: 'home' }
        if (!['city', 'business', 'bank'].includes(userPlace.place)) {
            e.reply([global.segment.at(id), "\n你需要在城市、商业区或银行才能抢银行！使用[去城市]或[去商业区]移动位置。"])
            return
        }
        
        // 检查冷却时间
        let UserPAF = battlejson[id].Privilege
        if (isRedisAvailable()) {
            const redisClient4 = getRedis();
            let lastTime = await redisClient4.ttl(`akasha:wife-Robbery-cd:${e.group_id}:${id}`);
            if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
                e.reply([global.segment.at(id), "\n", `你的抢夺冷却时间还有${lastTime}秒哦~`])
                return true
            }
        } else if (!UserPAF && !this.checkDevPermission(e)) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查冷却时间"])
            return true
        }
        
        // 战斗力和装备影响成功率和收益
        let battlePower = battlejson[id].attack + battlejson[id].defense
        let successRate = Math.min(0.8, 0.3 + (battlePower / 1000))
        let isSuccess = Math.random() < successRate
        
        if (!isSuccess) {
            // 失败被抓，关进监狱
            if (!placejson[id]) {
                placejson[id] = { place: "home" };
            }
            placejson[id].place = 'prison'
            await this.dataManager.saveUserPlace(id, placejson[id])
            const redisClient5 = getRedis();
            await redisClient5.setex(`akasha:wife-prison:${e.group_id}:${id}`, 1800, "1") // 30分钟监禁
            
            // 罚款
            let fine = Math.round(homejson[id].money * 0.2)
            homejson[id].money = Math.max(0, homejson[id].money - fine)
            await this.dataManager.saveUserHome(id, homejson[id])
            
            e.reply([
                global.segment.at(id), "\n",
                `🚔 抢银行失败！被警察抓住了！\n`,
                `💰 罚款: ${fine}金币\n`,
                `⛓️ 监禁: 30分钟\n`,
                `📍 位置已变更为: 监狱`
            ])
            return
        }
        
        // 成功抢劫
        let baseMoney = Math.round(Math.random() * 1000 + 500)
        let battleBonus = Math.round(battlePower / 10)
        let houseBonus = housejson[id] ? Math.round(housejson[id].loveup * 50) : 0
        let locationBonus = userPlace.place === 'bank' ? 200 : 0 // 在银行内抢劫额外奖励
        let totalMoney = baseMoney + battleBonus + houseBonus + locationBonus
        
        homejson[id].money += totalMoney
        battlejson[id].experience += 50 // 获得经验
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserBattle(id, battlejson[id])
        
        e.reply([
            global.segment.at(id), "\n",
            `🏦 银行抢劫成功！\n`,
            `💰 基础收益: ${baseMoney}金币\n`,
            `⚔️ 战力加成: ${battleBonus}金币\n`,
            `🏠 房屋加成: ${houseBonus}金币\n`,
            `📍 位置加成: ${locationBonus}金币\n`,
            `📈 总收益: ${totalMoney}金币\n`,
            `✨ 获得经验: 50点`
        ])
        
        // 触发报警机制
        await this.triggerPoliceChase(e, id, totalMoney)
        
        const redisClient6 = getRedis();
         await redisClient6.setex(`akasha:wife-Robbery-cd:${e.group_id}:${id}`, 3600, "1")
        return true
    }
    
    async robberyPlayer(e, id, targetId, homejson, placejson, battlejson, housejson) {
        let targetHomejson = await this.dataManager.getUserHome(targetId)
        let targetBattlejson = await this.dataManager.getUserBattle(targetId)
        let targetPlacejson = await this.dataManager.getUserPlace(targetId)
        
        // 检查目标是否存在
        if (!targetHomejson[targetId]) {
            e.reply([global.segment.at(id), "\n目标用户数据不存在！"])
            return
        }
        
        // 检查冷却时间
        let UserPAF = battlejson[id].Privilege
        if (isRedisAvailable()) {
            const redisClient7 = getRedis();
            let lastTime = await redisClient7.ttl(`akasha:wife-Robbery-cd:${e.group_id}:${id}`);
            if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
                e.reply([global.segment.at(id), "\n", `你的抢夺冷却时间还有${lastTime}秒哦~`])
                return true
            }
        } else if (!UserPAF && !this.checkDevPermission(e)) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查冷却时间"])
            return true
        }
        
        // 检查目标是否在监狱（无法抢劫）
        let targetPlace = targetPlacejson[targetId] || { place: 'home' }
        if (targetPlace.place === 'prison') {
            e.reply([global.segment.at(id), "\n目标在监狱里，无法抢劫！"])
            return
        }
        
        // 位置影响成功率
        let userPlace = placejson[id] || { place: 'home' }
        let locationBonus = 0
        if (userPlace.place === 'city' || userPlace.place === 'business') {
            locationBonus = 0.1
        } else if (userPlace.place === 'home' && targetPlace.place === 'home') {
            locationBonus = -0.1 // 在家抢劫更困难
        }
        
        // 战斗力对比决定成功率
        let attackerPower = battlejson[id].attack + battlejson[id].defense
        let defenderPower = targetBattlejson[targetId].attack + targetBattlejson[targetId].defense
        let powerRatio = attackerPower / (defenderPower + 1)
        let houseBonus = housejson[id] ? housejson[id].loveup * 0.02 : 0
        let successRate = Math.min(0.9, Math.max(0.1, powerRatio * 0.6 + locationBonus + houseBonus))
        
        let isSuccess = Math.random() < successRate
        
        if (!isSuccess) {
            // 抢劫失败，反被教训
            let penalty = Math.round(homejson[id].money * 0.15)
            homejson[id].money = Math.max(0, homejson[id].money - penalty)
            targetHomejson[targetId].money += penalty
            
            // 降低攻击者经验
            battlejson[id].experience = Math.max(0, battlejson[id].experience - 20)
            
            await this.dataManager.saveUserHome(id, homejson[id])
            await this.dataManager.saveUserHome(targetId, targetHomejson[targetId])
            await this.dataManager.saveUserBattle(id, battlejson[id])
            
            e.reply([
                global.segment.at(id), "\n",
                `💥 抢劫失败！反被对方教训！\n`,
                `💰 损失金币: ${penalty}\n`,
                `📉 损失经验: 20点\n`,
                `⚔️ 战力差距让你处于劣势！`
            ])
            
            const redisClient8 = getRedis();
            await redisClient8.setex(`akasha:wife-Robbery-cd:${e.group_id}:${id}`, 1800, "1") // 失败冷却更短
            return
        }
        
        // 抢劫成功
        if (targetHomejson[targetId].money <= 0) {
            e.reply([global.segment.at(id), "\n对方没钱，你抢了个寂寞"])
            return
        }
        
        let maxSteal = Math.round(targetHomejson[targetId].money * 0.4)
        let stolenMoney = Math.round(Math.random() * maxSteal + 100)
        stolenMoney = Math.min(stolenMoney, targetHomejson[targetId].money)
        
        homejson[id].money += stolenMoney
        targetHomejson[targetId].money -= stolenMoney
        battlejson[id].experience += 30 // 获得经验
        
        // 如果目标有老婆，降低好感度
        if (targetHomejson[targetId].s && targetHomejson[targetId].s !== 0 && targetHomejson[targetId].s !== undefined && targetHomejson[targetId].s !== null && targetHomejson[targetId].s !== '') {
            targetHomejson[targetId].love = Math.max(0, targetHomejson[targetId].love - 50)
        }
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserHome(targetId, targetHomejson[targetId])
        await this.dataManager.saveUserBattle(id, battlejson[id])
        
        e.reply([
            global.segment.at(id), "\n",
            `💰 抢劫成功！获得${stolenMoney}金币！\n`,
            `✨ 获得经验: 30点\n`,
            `⚔️ 战力优势让你占据上风！\n`,
            `📍 位置: ${userPlace.place} → 影响成功率`
        ])
        
        // 触发报警机制
        await this.triggerPoliceChase(e, id, stolenMoney)
        
        await redisClient8.setex(`akasha:wife-Robbery-cd:${e.group_id}:${id}`, 3600, "1")
        return true
    }
    
    async triggerPoliceChase(e, id, amount) {
        // 30%概率触发报警
        if (Math.random() < 0.3) {
            let fine = Math.round(amount * 1.5)
            
            setTimeout(async () => {
                let homejson = await this.dataManager.getUserHome(id)
                
                if (homejson[id].money >= fine) {
                    homejson[id].money -= fine
                    await this.dataManager.saveUserHome(id, homejson[id])
                    e.reply([
                        global.segment.at(id), "\n",
                        `🚔 被报警了！需要赔偿${fine}金币作为罚款！`
                    ])
                } else {
                    // 金币不足，关监狱
                    let placejson = await this.dataManager.getUserPlace(id)
                    if (!placejson[id]) {
                        placejson[id] = { place: "home" };
                    }
                    placejson[id].place = 'prison'
                    homejson[id].money = 0
                    await this.dataManager.saveUserPlace(id, placejson[id])
                    await this.dataManager.saveUserHome(id, homejson[id])
                    const redisClient9 = getRedis();
                    await redisClient9.setex(`akasha:wife-prison:${e.group_id}:${id}`, 3600, "1") // 1小时监禁
                    e.reply([
                        global.segment.at(id), "\n",
                        `🚔 被报警了！金币不足支付罚款！\n`,
                        `💰 金币被没收\n`,
                        `⛓️ 被关进监狱1小时！\n`,
                        `📍 位置已变更为: 监狱`
                    ])
                }
            }, 4000)
        }
    }
    //抢老婆失败时调用
    async ntrF(e, jia, yi, key = 'ntr') {
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        if (key == 'ntr') {
            var pcj = Math.round((homejson[yi].love / 10) + (homejson[jia].money / 3) + 100)//赔偿金
            setTimeout(() => {
                e.reply([
                    global.segment.at(jia), "\n",
                    `对方报警,你需要赔偿${pcj}金币,;金币不足将会被关禁闭`, "\n",
                ])
            }, 4000);
        }
        if (key == 'Robbery') {
            var pcj = Math.round(100 + Math.random() * 100)
            setTimeout(() => {
                e.reply([
                    global.segment.at(jia), "\n",
                    `你抢劫被抓到,你需要赔偿${pcj}金币,;金币不足将会被关禁闭`, "\n",
                ])
            }, 4000);
        }
        var jbtime = (pcj - homejson[jia].money) * 10//禁闭时间

        if (homejson[jia].money < pcj) {
            homejson[yi].money += homejson[jia].money
            homejson[jia].money = 0
            
            // 更新获胜者的金币任务进度
            const { QuestSystem } = await import('../../components/quest_system.js')
             const questSystem = new QuestSystem()
             await questSystem.updateQuestProgress(yi, e.group_id, 'max_money', homejson[yi].money)
            
            const redisClient10 = getRedis();
            await redisClient10.set(`akasha:wife-jinbi-cd:${e.group_id}:${jia}`, currentTime, {
                EX: jbtime
            });
            setTimeout(() => {
                e.reply(`恭喜你,你的金币不足,因此赔光了还被关禁闭${jbtime / 60}分`)
            }, 5000);
        }
        if (homejson[jia].money >= pcj) {
            homejson[yi].money += pcj
            homejson[jia].money -= pcj
            
            // 更新双方的金币任务进度
            const { QuestSystem } = await import('../../components/quest_system.js')
             const questSystem = new QuestSystem()
             await questSystem.updateQuestProgress(yi, e.group_id, 'max_money', homejson[yi].money)
            if (homejson[jia].money > 0) {
                await questSystem.updateQuestProgress(jia, e.group_id, 'max_money', homejson[jia].money)
            }
            
            setTimeout(() => {
                e.reply(`你成功清赔款${pcj}金币!`)
            }, 6000);
        }
        await dataManager.saveUserHome(id, homejson[id])
    }
    //抢老婆成功时调用
    async ntrT(e, jia, yi, key = 'ntr') {
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        if (key == 'ntr') {
            if ((homejson[jia].money > (homejson[yi].love * 1.5)) && (homejson[jia].money > homejson[yi].money))
                e.reply([
                    global.segment.at(yi), "\n",
                    `很遗憾!由于你老婆对你的好感并不是很高,对方又太有钱了!你的老婆被人抢走了!!!`
                ])
            else {
                e.reply([
                    global.segment.at(yi), "\n",
                    `很遗憾!由于你的疏忽,你的老婆被人抢走了!!!`
                ])
            }
            homejson[jia].s = homejson[yi].s
            homejson[jia].love = 6
            homejson[yi].s = 0
            homejson[yi].love = 0
        }
        if (key == 'Robbery') {
            e.reply([
                global.segment.at(yi), "\n",
                `很遗憾!由于你的疏忽,你的钱抢走了!!!`
            ])
            money = 100 + 100 * Math.random()
            homejson[yi].money -= money
            homejson[jia].money += money

        }
        await dataManager.saveUserHome(id, homejson[id])
    }
    //愿意 - 表白同意功能
    async yy(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var homejson = await this.dataManager.getUserHome(id)
        var placejson = await this.dataManager.getUserPlace(id)
        var battlejson = await this.dataManager.getUserBattle(id)
        var housejson = await this.dataManager.getUserHouse(id)
        
        // 检查是否有待处理的表白
        let confessionKey = `akasha:confession-wait:${e.group_id}:${id}`
        if (!isRedisAvailable()) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查表白状态"])
            return
        }
        const redisClient11 = getRedis();
        let confessionData = await redisClient11.get(confessionKey)
        
        if (!confessionData) {
            e.reply([
                global.segment.at(id), "\n",
                `目前没有人向你表白哦~\n`,
                `💡 有人表白时使用[愿意]接受，[拒绝]拒绝`
            ])
            return
        }
        
        let confession = JSON.parse(confessionData)
        let proposerId = confession.proposer_id
        let proposerName = confession.proposer_name
        
        // 检查表白者是否还在群中
        const memberMap = await e.group.getMemberMap()
        if (!memberMap.get(proposerId)) {
            if (isRedisAvailable()) {
                const redisClient12 = getRedis();
        await redisClient12.del(confessionKey)
            }
            e.reply("表白者已不在群中，表白自动取消")
            return
        }
        
        // 检查双方是否已有伴侣
        if (homejson[id] && homejson[id].s !== '' && homejson[id].s !== 0) {
            await redisClient11.del(confessionKey)
            e.reply([
                global.segment.at(id), "\n",
                `你已经有伴侣了，无法接受表白`
            ])
            return
        }
        
        let proposerHome = homejson[proposerId]
        if (proposerHome && proposerHome.s !== '' && proposerHome.s !== 0) {
            await redisClient11.del(confessionKey)
            e.reply([
                global.segment.at(id), "\n",
                `${proposerName}已经有伴侣了，表白自动取消`
            ])
            return
        }
        
        // 位置加成计算
        let currentPlace = placejson[id] || { place: 'home' }
        let locationBonus = 0
        let locationDesc = ''
        
        switch (currentPlace.place) {
            case 'city':
                locationBonus = 20
                locationDesc = '城市的浪漫氛围'
                break
            case 'business':
                locationBonus = 15
                locationDesc = '商业区的繁华'
                break
            case 'bank':
                locationBonus = 10
                locationDesc = '银行的安全感'
                break
            default:
                locationBonus = 5
                locationDesc = '家的温馨'
                break
        }
        
        // 房屋等级加成
        let houseBonus = (housejson[id]?.loveup || 1) * 10
        
        // 计算初始好感度
        let baseLove = 50 + locationBonus + houseBonus
        let finalLove = Math.min(baseLove + Math.floor(Math.random() * 30), 100)
        
        // 建立关系
        if (!homejson[id]) {
            await this.creat_(e, id)
            homejson = await this.dataManager.getUserHome(id)
        }
        if (!homejson[proposerId]) {
            await this.creat_(e, proposerId)
            homejson = await this.dataManager.getUserHome(id)
        }
        
        homejson[id].s = proposerId
        homejson[id].love = finalLove
        homejson[proposerId].s = id
        homejson[proposerId].love = finalLove
        
        // 奖励金币
        let rewardMoney = 200 + Math.floor(Math.random() * 100)
        homejson[id].money += rewardMoney
        homejson[proposerId].money += rewardMoney
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserHome(proposerId, homejson[proposerId])
        await redisClient11.del(confessionKey)
        
        // 更新任务进度
        try {
            const { QuestSystem } = await import('../../components/quest_system.js')
            const questSystem = new QuestSystem()
            await questSystem.updateQuestProgress(id, e.group_id, 'wife_count', 1)
            await questSystem.updateQuestProgress(proposerId, e.group_id, 'wife_count', 1)
            await questSystem.updateQuestProgress(id, e.group_id, 'max_love', finalLove)
            await questSystem.updateQuestProgress(proposerId, e.group_id, 'max_love', finalLove)
            await questSystem.updateQuestProgress(id, e.group_id, 'interaction_count', 1)
            await questSystem.updateQuestProgress(proposerId, e.group_id, 'interaction_count', 1)
        } catch (err) {
            // 忽略任务系统错误
        }
        
        e.reply([
            global.segment.at(proposerId), " ", global.segment.at(id), "\n",
            `🎉 表白成功！恭喜你们成为情侣！\n`,
            `💕 初始好感度：${finalLove}\n`,
            `🏠 房屋加成：+${houseBonus}\n`,
            `📍 位置加成：+${locationBonus} (${locationDesc})\n`,
            `💰 奖励金币：${rewardMoney}\n`,
            `💡 可以通过[抱抱]、[逛街]、[打工]等方式增加好感度`
        ])
    }
    
    // 位置移动系统
    async goToCity(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var placejson = await this.dataManager.getUserPlace(id)
        var homejson = await this.dataManager.getUserHome(id)
        
        // 检查是否在监狱
        let currentPlace = placejson[id] || { place: 'home' }
        if (currentPlace.place === 'prison') {
            e.reply([global.segment.at(id), "\n你在监狱里，无法移动！"])
            return
        }
        
        // 移动费用
        let moveCost = 50
        if (homejson[id].money < moveCost) {
            e.reply([global.segment.at(id), "\n移动到城市需要50金币，你的金币不足！"])
            return
        }
        
        homejson[id].money -= moveCost
        placejson[id] = { place: 'city', lastMove: Date.now() }
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserPlace(id, placejson[id])
        
        e.reply([
            global.segment.at(id), "\n",
            `🏙️ 你来到了城市\n`,
            `💰 花费: 50金币\n`,
            `💡 在城市中，抢劫和牛头人成功率更高！`
        ])
    }
    
    async goToBusiness(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var placejson = await this.dataManager.getUserPlace(id)
        var homejson = await this.dataManager.getUserHome(id)
        
        // 检查是否在监狱
        let currentPlace = placejson[id] || { place: 'home' }
        if (currentPlace.place === 'prison') {
            e.reply([global.segment.at(id), "\n你在监狱里，无法移动！"])
            return
        }
        
        // 移动费用
        let moveCost = 80
        if (homejson[id].money < moveCost) {
            e.reply([global.segment.at(id), "\n移动到商业区需要80金币，你的金币不足！"])
            return
        }
        
        homejson[id].money -= moveCost
        placejson[id] = { place: 'business', lastMove: Date.now() }
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserPlace(id, placejson[id])
        
        e.reply([
            global.segment.at(id), "\n",
            `🏢 你来到了商业区\n`,
            `💰 花费: 80金币\n`,
            `💡 在商业区中，可以进行更多商业活动！`
        ])
    }
    
    async goToBank(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var placejson = await this.dataManager.getUserPlace(id)
        var homejson = await this.dataManager.getUserHome(id)
        
        // 检查是否在监狱
        let currentPlace = placejson[id] || { place: 'home' }
        if (currentPlace.place === 'prison') {
            e.reply([global.segment.at(id), "\n你在监狱里，无法移动！"])
            return
        }
        
        // 移动费用
        let moveCost = 100
        if (homejson[id].money < moveCost) {
            e.reply([global.segment.at(id), "\n移动到银行需要100金币，你的金币不足！"])
            return
        }
        
        homejson[id].money -= moveCost
        placejson[id] = { place: 'bank', lastMove: Date.now() }
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserPlace(id, placejson[id])
        
        e.reply([
            global.segment.at(id), "\n",
            `🏦 你来到了银行\n`,
            `💰 花费: 100金币\n`,
            `💡 在银行中抢劫有额外奖励，但风险也更高！`
        ])
    }
    
    async checkLocation(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var placejson = await this.dataManager.getUserPlace(id)
        
        let currentPlace = placejson[id] || { place: 'home' }
        let locationName = ''
        let locationDesc = ''
        
        switch (currentPlace.place) {
            case 'home':
                locationName = '🏠 家'
                locationDesc = '安全的地方，但机会有限'
                break
            case 'city':
                locationName = '🏙️ 城市'
                locationDesc = '繁华的地方，抢劫和牛头人成功率+10%'
                break
            case 'business':
                locationName = '🏢 商业区'
                locationDesc = '商业中心，各种活动成功率略有提升'
                break
            case 'bank':
                locationName = '🏦 银行'
                locationDesc = '抢银行有额外奖励，但被抓风险更高'
                break
            case 'prison':
                locationName = '⛓️ 监狱'
                locationDesc = '被关押中，无法进行大部分活动'
                if (isRedisAvailable()) {
                    const redisClient13 = getRedis();
                    let prisonTime = await redisClient13.ttl(`akasha:wife-prison:${e.group_id}:${id}`)
                    if (prisonTime > 0) {
                        locationDesc += `，剩余${Math.ceil(prisonTime/60)}分钟`
                    }
                } else {
                    locationDesc += '，Redis不可用，无法获取剩余时间'
                }
                break
            default:
                locationName = '❓ 未知位置'
                locationDesc = '你在一个神秘的地方'
                break
        }
        
        e.reply([
            global.segment.at(id), "\n",
            `📍 当前位置: ${locationName}\n`,
            `📝 位置描述: ${locationDesc}\n`,
            `💡 使用[去城市][去商业区][去银行][回家]移动位置`
        ])
    }
    //测试数据保存
   
    //拒绝 - 表白拒绝功能
    async jj(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var homejson = await this.dataManager.getUserHome(id)
        var placejson = await this.dataManager.getUserPlace(id)
        var battlejson = await this.dataManager.getUserBattle(id)
        
        // 检查是否有待处理的表白
        let confessionKey = `akasha:confession-wait:${e.group_id}:${id}`
        if (!isRedisAvailable()) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查表白状态"])
            return
        }
        const redisClient14 = getRedis();
        let confessionData = await redisClient14.get(confessionKey)
        
        if (!confessionData) {
            e.reply([
                global.segment.at(id), "\n",
                `目前没有人向你表白哦~\n`,
                `💡 有人表白时使用[愿意]接受，[拒绝]拒绝`
            ])
            return
        }
        
        let confession = JSON.parse(confessionData)
        let proposerId = confession.proposer_id
        let proposerName = confession.proposer_name
        
        // 检查表白者是否还在群中
        const memberMap = await e.group.getMemberMap()
        if (!memberMap.get(proposerId)) {
            await redisClient14.del(confessionKey)
            e.reply("表白者已不在群中，表白自动取消")
            return
        }
        
        // 拒绝的后果
        let proposerHome = homejson[proposerId]
        if (proposerHome) {
            // 表白者失去金币和心情
            let lostMoney = 100 + Math.floor(Math.random() * 100)
            proposerHome.money = Math.max(0, proposerHome.money - lostMoney)
            
            // 设置表白冷却时间（被拒绝后更长的冷却）
            if (isRedisAvailable()) {
                await redisClient14.set(`akasha:confession-rejected-cd:${e.group_id}:${proposerId}`, Date.now(), {
                    EX: 7200 // 2小时冷却
                })
            }
            
            await this.dataManager.saveUserHome(proposerId, proposerHome)
        }
        
        // 位置影响拒绝的严重程度
        let currentPlace = placejson[id] || { place: 'home' }
        let rejectSeverity = ''
        let extraPenalty = 0
        
        switch (currentPlace.place) {
            case 'city':
                rejectSeverity = '在众目睽睽下'
                extraPenalty = 50
                break
            case 'business':
                rejectSeverity = '在商业区'
                extraPenalty = 30
                break
            case 'bank':
                rejectSeverity = '在银行里'
                extraPenalty = 20
                break
            default:
                rejectSeverity = ''
                extraPenalty = 0
                break
        }
        
        if (extraPenalty > 0 && proposerHome) {
            proposerHome.money = Math.max(0, proposerHome.money - extraPenalty)
            await this.dataManager.saveUserHome(proposerId, proposerHome)
        }
        
        await redisClient14.del(confessionKey)
        
        // 随机拒绝理由
        const rejectReasons = [
            "我们还是做朋友比较好",
            "我觉得我们不太合适",
            "我现在不想谈恋爱",
            "你是个好人，但是...",
            "我们认识的时间还不够长",
            "我心里已经有人了",
            "我觉得我们性格不合",
            "现在不是时候"
        ]
        
        const randomReason = rejectReasons[Math.floor(Math.random() * rejectReasons.length)]
        
        // 更新任务进度（拒绝也是一种社交互动）
        try {
            const { QuestSystem } = await import('../../components/quest_system.js')
            const questSystem = new QuestSystem()
            await questSystem.updateQuestProgress(id, e.group_id, 'interaction_count', 1)
        } catch (err) {
            // 忽略任务系统错误
        }
        
        e.reply([
            global.segment.at(proposerId), " ", global.segment.at(id), "\n",
            `💔 表白被拒绝了...\n`,
            `💬 拒绝理由："${randomReason}"\n`,
            rejectSeverity ? `📍 ${rejectSeverity}被拒绝，额外损失${extraPenalty}金币\n` : '',
            `⏰ 表白冷却时间：2小时\n`,
            `💡 ${proposerName}，不要灰心，或许可以先通过其他方式增进感情`
        ])
    }
    
    // 处理表白回应
    async handleConfessionResponse(e, proposer_id, responder_id, accepted) {
        const groupId = e.group_id
        const filename = `${groupId}.json`
        
        // 清除表白等待状态
        if (isRedisAvailable()) {
            const redisClient15 = getRedis();
            await redisClient15.del(`akasha:confession-wait:${groupId}:${responder_id}`)
        }
        
        if (accepted) {
            // 表白被接受
            const proposerHomejson = await dataManager.getUserHome(proposer_id)
            const responderHomejson = await dataManager.getUserHome(responder_id)
            
            // 检查双方是否都没有对象
            if (proposerHomejson[proposer_id] && proposerHomejson[proposer_id].s !== 0 && proposerHomejson[proposer_id].s !== undefined && proposerHomejson[proposer_id].s !== null && proposerHomejson[proposer_id].s !== '') {
                await e.reply('表白者已经有对象了，表白失效！')
                return
            }
            if (responderHomejson[responder_id] && responderHomejson[responder_id].s !== 0 && responderHomejson[responder_id].s !== undefined && responderHomejson[responder_id].s !== null && responderHomejson[responder_id].s !== '') {
                await e.reply('你已经有对象了，不能接受表白！')
                return
            }
            
            // 建立关系
            proposerHomejson[proposer_id].s = responder_id
            proposerHomejson[proposer_id].love = Math.round(Math.random() * (80 - 60) + 60)
            proposerHomejson[proposer_id].money += 50
            
            responderHomejson[responder_id].s = proposer_id
            responderHomejson[responder_id].love = Math.round(Math.random() * (80 - 60) + 60)
            responderHomejson[responder_id].money += 50
            
            // 更新首次结婚任务进度
            const { QuestSystem } = await import('../../components/quest_system.js')
            const questSystem = new QuestSystem()
            await questSystem.updateQuestProgress(proposer_id, groupId, 'first_marriage', 1, true)
            await questSystem.updateQuestProgress(responder_id, groupId, 'first_marriage', 1, true)
            
            await dataManager.saveUserHome(proposer_id, proposerHomejson[proposer_id])
            await dataManager.saveUserHome(responder_id, responderHomejson[responder_id])
            
            await e.reply([
                global.segment.at(proposer_id), ' 和 ', global.segment.at(responder_id), '\n',
                '💕 表白成功！恭喜你们在一起了！\n',
                '🎁 每人获得50金币奖励！\n',
                '❤️ 愿你们的爱情长长久久！'
            ])
        } else {
            // 表白被拒绝
            await e.reply([
                global.segment.at(proposer_id), '\n',
                '💔 很遗憾，表白被拒绝了...\n',
                '😊 不要灰心，缘分会在合适的时候到来的！'
            ])
        }
    }
    
    //随机娶
    async wife(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var homejson = await this.dataManager.getUserHome(id)
        var placejson = await this.dataManager.getUserPlace(id)
        var housejson = await this.dataManager.getUserHouse(id)
        var battlejson = await this.dataManager.getUserBattle(id)
        
        // 检查是否被禁闭或死亡
        if (await this.is_killed(e, 'wife', false) == true) return
        
        // 检查位置限制
        let userPlace = placejson[id] || { place: 'home' }
        if (userPlace.place !== "home") {
            e.reply([
                global.segment.at(id), "\n",
                `你不在家,不能娶群友,当前位置为：${userPlace.place}\n请先[回家]`
            ])
            return
        }
        
        // 检查并修正老婆数据：如果老婆数据为0，则修改为空字符串
        if (homejson[id] && homejson[id].s === 0) {
            homejson[id].s = ''
            await this.dataManager.saveUser(id, homejson)
        }
        
        // 检查是否已有老婆
        if (homejson[id] && homejson[id].s !== 0 && homejson[id].s !== '') {
            let wifeName = await this.people(e, 'nickname', homejson[id].s)
            let she_he = await this.people(e, 'sex', homejson[id].s)
            e.reply([
                global.segment.at(id), "\n",
                `你已经有老婆了！${she_he}是${wifeName}\n`,
                `好感度：${homejson[id].love}\n`,
                `如需更换请先[闹离婚]`
            ])
            return
        }
        
        // 获取群成员信息（统一获取，避免重复调用）
        const memberMap = await e.group.getMemberMap()
        
        // 解析是否指定了目标用户（强娶功能）
        let targetId = null
        let isForceMarry = false
        
        // 检查消息中是否有@用户（参考cpwsc.js的方法）
        if (e.at) {
            const atUserId = parseInt(e.at)
            const targetMember = memberMap.get(atUserId)
            if (targetMember && atUserId !== e.user_id && atUserId.toString().length >= 5) {
                targetId = atUserId
                isForceMarry = true
            }
        }
        
        // 检查冷却时间（强娶冷却时间更长）
        let UserPAF = battlejson[id].Privilege
        let isDev = this.checkDevPermission(e)
        let cdKey = isForceMarry ? `akasha:wife-force-cd:${e.group_id}:${id}` : `akasha:wife-random-cd:${e.group_id}:${id}`
        if (!isRedisAvailable()) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查冷却时间"])
            return
        }
        const redisClient16 = getRedis();
        let lastTime = await redisClient16.ttl(cdKey);
        if (lastTime !== -2 && !UserPAF && !isDev) {
            e.reply([
                global.segment.at(id), "\n",
                `${isForceMarry ? '强娶' : '娶群友'}功能冷却中！(*/ω＼*)`, "\n",
                `还需等待${Math.ceil(lastTime / 60)}分钟`
            ]);
            return
        }
        
        // 检查金币要求（强娶需要更多金币）
        let minMoney = isForceMarry ? 200 : 100
        if (homejson[id].money < minMoney) {
            e.reply([
                global.segment.at(id), "\n",
                `金币不足！${isForceMarry ? '强娶' : '娶群友'}需要至少${minMoney}金币作为彩礼\n`,
                `当前金币：${homejson[id].money}\n`,
                `可以通过[打工赚钱]或[领取低保]获得金币`
            ])
            return
        }
        
        let target, targetName, target_she_he
        
        if (isForceMarry && targetId) {
            // 强娶指定用户
            if (targetId == id) {
                e.reply("你不能娶自己！")
                return
            }
            
            if (targetId == e.bot.uin) {
                e.reply("你不能娶机器人！")
                return
            }
            
            // 获取目标用户信息（使用已获取的memberMap）
             target = memberMap.get(targetId)
             if (!target) {
                 e.reply("目标用户不在群中！")
                 return
             }
            
            targetName = await this.people(e, 'nickname', targetId)
            target_she_he = await this.people(e, 'sex', targetId)
            
            // 检查目标是否已有老婆
            let targetHome = homejson[targetId]
            // 检查并修正目标用户的老婆数据：如果老婆数据为0，则修改为空字符串
            if (targetHome && targetHome.s === 0) {
                targetHome.s = ''
                await this.dataManager.saveUser(targetId, {[targetId]: targetHome})
            }
            
            if (targetHome && targetHome.s !== '' && targetHome.s !== 0) {
                let targetWifeName = await this.people(e, 'nickname', targetHome.s)
                e.reply([
                    global.segment.at(id), "\n",
                    `${targetName} 已经有老婆了！\n`,
                    `${target_she_he}的老婆是：${targetWifeName}\n`,
                    `无法强娶已有伴侣的人`
                ])
                return
            }
        } else {
            // 随机娶群友（使用已获取的memberMap）
            let arrMember = Array.from(memberMap.values());
            
            // 过滤可娶对象（排除自己、机器人、已有老婆的人）
            let availableMembers = []
            for (let member of arrMember) {
                if (member.user_id == id || member.user_id == e.bot.uin) continue
                
                // 检查对方是否已有老婆
                let targetHome = homejson[member.user_id]
                // 检查并修正目标用户的老婆数据：如果老婆数据为0，则修改为空字符串
                if (targetHome && targetHome.s === 0) {
                    targetHome.s = ''
                    await this.dataManager.saveUser(member.user_id, {[member.user_id]: targetHome})
                }
                if (targetHome && targetHome.s !== '' && targetHome.s !== 0) continue
                
                availableMembers.push(member)
            }
            
            if (availableMembers.length === 0) {
                e.reply([
                    global.segment.at(id), "\n",
                    `群里没有可娶的对象了！\n`,
                    `所有人都已经有老婆了或者只有你一个人在群里\n`,
                    `💡 可以尝试[强娶@群友]功能`
                ])
                return
            }
            
            // 随机选择目标
            target = availableMembers[Math.floor(Math.random() * availableMembers.length)]
            targetId = target.user_id
            targetName = await this.people(e, 'nickname', targetId)
            target_she_he = await this.people(e, 'sex', targetId)
        }
        
        // 计算成功率（基于金币、房屋等级、工作历史等）
        let baseSuccessRate = isForceMarry ? (sjwife + 20) : sjwife // 强娶基础成功率更高
        let moneyBonus = Math.min(homejson[id].money / 1000 * 10, 30) // 金币加成，最多30%
        let houseBonus = (housejson[id].loveup - 1) * 15 // 房屋加成
        
        // 工作历史加成
        let workHistory = await this.dataManager.getUserWorkHistory(id)
        let workBonus = 0
        if (workHistory && workHistory.length > 0) {
            let totalWork = workHistory.length
            workBonus = Math.min(totalWork / 10 * 5, 15) // 每10次工作增加5%成功率，最多15%
        }
        
        // 保底机制：检查失败次数
        let failCountKey = isForceMarry ? `akasha:wife-force-fail-count:${e.group_id}:${id}` : `akasha:wife-random-fail-count:${e.group_id}:${id}`
        let failCount = await redisClient16.get(failCountKey) || 0
        failCount = parseInt(failCount)
        
        // 保底逻辑：连续失败10次后必定成功
        let isGuaranteed = failCount >= 10
        let totalSuccessRate = isGuaranteed ? 100 : Math.min(baseSuccessRate + moneyBonus + houseBonus + workBonus, isForceMarry ? 98 : 95)
        
        // 设置冷却时间（强娶60分钟，普通30分钟）
        let cdTime = isForceMarry ? 3600 : 1800
        await redisClient16.set(cdKey, Date.now(), {
            EX: cdTime
        });
        
        // 消耗金币
        let costMoney = Math.floor(minMoney + Math.random() * (isForceMarry ? 200 : 100))
        homejson[id].money -= costMoney
        
        // 判断是否成功
        let success = Math.random() * 100 < totalSuccessRate
        
        if (success) {
            // 成功娶到
            homejson[id].s = targetId
            homejson[id].love = Math.floor(Math.random() * (isForceMarry ? 30 : 50) + (isForceMarry ? 20 : 50)) // 强娶好感度更低
            
            // 给对方也设置关系（如果对方没有数据则创建）
            if (!homejson[targetId]) {
                await this.creat_(e, targetId)
                // 重新获取目标用户的数据
                const targetUserHome = await this.dataManager.getUserHome(targetId)
                // 将新创建的目标用户数据合并到现有的homejson中
                homejson = { ...homejson, ...targetUserHome }
            }
            
            // 确保目标用户数据存在（先设置基础数据，好感度稍后设置）
            if (!homejson[targetId]) {
                homejson[targetId] = {
                    s: '',
                    love: 1, // 设置为1避免触发自动分手
                    money: 500,
                    wait: 0
                }
            }
            
            // 设置对方的关系状态
            homejson[targetId].s = id
            homejson[targetId].love = Math.floor(Math.random() * (isForceMarry ? 20 : 30) + (isForceMarry ? 10 : 30)) // 对方的好感度
            
            // 成功时重置失败计数器
            await redisClient16.del(failCountKey)
            
            let guaranteedText = isGuaranteed ? '\n🎯 保底机制触发！必定成功！' : ''
            
            e.reply([
                global.segment.at(targetId), "\n",
                `🎉 ${isForceMarry ? '强娶成功！' : '恭喜！娶群友成功！'}\n`,
                `💕 你成功${isForceMarry ? '强娶了' : '娶到了'}${targetName}(${target_she_he})\n`,
                `💰 花费彩礼：${costMoney}金币\n`,
                `💖 初始好感度：${homejson[id].love}\n`,
                `🏠 房屋加成：+${Math.floor(houseBonus)}%\n`,
                `💼 工作加成：+${Math.floor(workBonus)}%\n`,
                `📊 总成功率：${Math.floor(totalSuccessRate)}%\n`,
                `💳 剩余金币：${homejson[id].money}${guaranteedText}\n\n`,
                `💡 ${isForceMarry ? '强娶的好感度较低，需要更多努力维护关系' : '可以通过[抱抱]、[逛街]、[打工]等方式增加好感度'}`
            ])
            
            // 更新任务进度
            try {
                const { QuestSystem } = await import('../../components/quest_system.js')
                const questSystem = new QuestSystem()
                await questSystem.updateQuestProgress(id, e.group_id, 'wife_count', 1)
                await questSystem.updateQuestProgress(id, e.group_id, 'max_love', homejson[id].love)
            } catch (err) {
              
            }
            
        } else {
            // 失败
            let failReasons = isForceMarry ? [
                `${targetName}强烈反抗，强娶失败`,
                `${targetName}逃跑了，没抓到`,
                `群友们阻止了你的强娶行为`,
                `${targetName}说宁死不从`,
                `强娶被群管发现，被阻止了`
            ] : [
                `${targetName}对你没有感觉`,
                `${targetName}觉得你不够有钱`,
                `${targetName}说你们不合适`,
                `${targetName}已经心有所属`,
                `${targetName}觉得你的房子太小了`,
                `${targetName}说要再考虑考虑`
            ]
            let failReason = failReasons[Math.floor(Math.random() * failReasons.length)]
            
            // 失败时增加失败计数器
            failCount++
            await redisClient16.set(failCountKey, failCount, { EX: 86400 * 7 }) // 7天过期
            
            let failCountText = `\n📊 连续失败次数：${failCount}/10`
            let guaranteeText = failCount >= 10 ? '\n🎯 下次娶群友将触发保底机制！' : failCount >= 8 ? `\n⚡ 还有${10 - failCount}次失败就会触发保底！` : ''
            
            e.reply([
                global.segment.at(id), "\n",
                `💔 很遗憾，${isForceMarry ? '强娶' : '娶群友'}失败了...\n`,
                `🎯 目标：${targetName}(${target_she_he})\n`,
                `😢 失败原因：${failReason}\n`,
                `💰 损失彩礼：${costMoney}金币\n`,
                `📊 成功率：${Math.floor(totalSuccessRate)}%\n`,
                `💳 剩余金币：${homejson[id].money}${failCountText}${guaranteeText}\n\n`,
                `💡 提升金币、房屋等级和工作经验可以增加成功率`
            ])
        }
        
        // 保存数据
        await this.dataManager.saveUserHome(id, homejson[id])
        
        // 如果成功娶到，还需要保存对方的数据
        if (success && targetId) {
            await this.dataManager.saveUserHome(targetId, homejson[targetId])
        }
        
        // 检查是否触发其他事件（只在成功娶到时检查）
        if (success && await this.is_fw(e, homejson) == true) return
        
        return true
    }
    //主动分手/甩掉对方
    async breakup(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        
        // 检查是否被禁闭或死亡
        if (await this.is_killed(e, 'breakup', false) == true) return
        
        // 获取各种数据
        var homejson = await this.dataManager.getUserHome(id)
        var battlejson = await this.dataManager.getUserBattle(id)
        var placejson = await this.dataManager.getUserPlace(id)
        var housejson = await this.dataManager.getUserHouse(id)
        
        // 检查是否有老婆
        if (!homejson[id] || homejson[id].s === '') {
            e.reply([global.segment.at(id), "\n你还没有老婆，无法分手！"])
            return
        }
        
        let wifeId = homejson[id].s
        let wifeName = await this.people(e, 'nickname', wifeId)
        
        // 检查冷却时间
        if (!isRedisAvailable()) {
            e.reply([global.segment.at(id), "\n", "Redis不可用，无法检查冷却时间"])
            return
        }
        const redisClient17 = getRedis();
        let lastTime = await redisClient17.ttl(`akasha:wife-breakup-cd:${e.group_id}:${id}`);
        if (lastTime !== -2 && !this.checkDevPermission(e)) {
            e.reply([global.segment.at(id), "\n", `分手冷却时间还有${lastTime}秒哦~`])
            return true
        }
        
        // 获取老婆数据
        var wifeHomejson = await this.dataManager.getUserHome(wifeId)
        
        // 计算分手成本和后果
        let currentLove = homejson[id].love || 0
        let breakupCost = Math.round(currentLove * 10) // 好感度越高，分手成本越高
        let emotionalDamage = Math.round(currentLove * 0.1) // 情感创伤影响经验
        
        // 位置影响分手方式
        let userPlace = placejson[id] || { place: 'home' }
        let breakupMethod = ''
        let costMultiplier = 1
        
        switch (userPlace.place) {
            case 'home':
                breakupMethod = '在家中'
                costMultiplier = 1.2 // 在家分手更痛苦
                break
            case 'city':
                breakupMethod = '在城市中'
                costMultiplier = 0.8 // 在城市分手较轻松
                break
            case 'business':
                breakupMethod = '在商业区'
                costMultiplier = 0.9
                break
            case 'prison':
                e.reply([global.segment.at(id), "\n你在监狱里，无法进行分手！"])
                return
            default:
                breakupMethod = '在某个地方'
                break
        }
        
        breakupCost = Math.round(breakupCost * costMultiplier)
        
        // 检查是否有足够金币支付分手费用
        if (homejson[id].money < breakupCost) {
            e.reply([
                global.segment.at(id), "\n",
                `💔 分手需要${breakupCost}金币的分手费，你的金币不足！\n`,
                `💡 当前金币: ${homejson[id].money}\n`,
                `📍 位置影响: ${breakupMethod}（费用×${costMultiplier}）`
            ])
            return
        }
        
        // 房屋影响分手后的状态
        let houseComfort = housejson[id] ? housejson[id].loveup : 1
        let recoveryBonus = Math.round(houseComfort * 20) // 房屋等级影响恢复
        
        // 执行分手
        homejson[id].money -= breakupCost
        homejson[id].s = ''
        homejson[id].love = 0
        
        // 更新老婆数据
        if (wifeHomejson[wifeId]) {
            wifeHomejson[wifeId].s = 0
            wifeHomejson[wifeId].love = 0
            // 老婆获得一半分手费作为补偿
            wifeHomejson[wifeId].money += Math.round(breakupCost * 0.5)
            await this.dataManager.saveUserHome(wifeId, wifeHomejson[wifeId])
        }
        
        // 经验损失（情感创伤）
        battlejson[id].experience = Math.max(0, battlejson[id].experience - emotionalDamage)
        
        // 分手后的心情影响（临时debuff）
        await redis.setex(`akasha:wife-heartbreak:${e.group_id}:${id}`, 3600, currentLove.toString()) // 1小时心碎状态
        
        await this.dataManager.saveUserHome(id, homejson[id])
        await this.dataManager.saveUserBattle(id, battlejson[id])
        
        // 分手类型和消息
        let breakupType = ''
        let breakupMessage = ''
        
        if (currentLove < 100) {
            breakupType = '和平分手'
            breakupMessage = '你们和平地结束了这段关系'
        } else if (currentLove < 500) {
            breakupType = '痛苦分手'
            breakupMessage = '这是一次痛苦的分手，双方都受到了伤害'
        } else {
            breakupType = '撕心裂肺的分手'
            breakupMessage = '这次分手让你们都心碎不已'
        }
        
        e.reply([
            global.segment.at(id), "\n",
            `💔 ${breakupType}\n`,
            `👫 你与 ${wifeName} 分手了\n`,
            `📍 分手地点: ${breakupMethod}\n`,
            `💰 分手费用: ${breakupCost}金币\n`,
            `💝 对方补偿: ${Math.round(breakupCost * 0.5)}金币\n`,
            `📉 经验损失: ${emotionalDamage}点\n`,
            `🏠 房屋安慰: +${recoveryBonus}点恢复\n`,
            `💭 ${breakupMessage}\n`,
            `⏰ 心碎状态: 1小时（影响部分功能）`
        ])
        
        // 设置分手冷却
        await redis.setex(`akasha:wife-breakup-cd:${e.group_id}:${id}`, 1800, "1") // 30分钟冷却
        
        // 触发分手后事件
        await this.triggerPostBreakupEvents(e, id, currentLove, userPlace.place)
        
        return true
    }
    
    async triggerPostBreakupEvents(e, id, loveLevel, location) {
        // 根据好感度和位置触发不同的后续事件
        setTimeout(async () => {
            let eventChance = Math.random()
            
            if (loveLevel > 500 && eventChance < 0.3) {
                // 高好感度分手可能触发挽回事件
                e.reply([
                    global.segment.at(id), "\n",
                    `💌 你收到了前任的挽回信息...\n`,
                    `💡 也许还有机会重新开始？`
                ])
            } else if (location === 'city' && eventChance < 0.2) {
                // 在城市分手可能遇到新的机会
                e.reply([
                    global.segment.at(id), "\n",
                    `🌟 在城市中走走，你遇到了新的机会...\n`,
                    `💡 使用[娶群友]寻找新的伴侣吧！`
                ])
            } else if (loveLevel < 100 && eventChance < 0.4) {
                // 低好感度分手比较轻松
                let homejson = await this.dataManager.getUserHome(id)
                let bonus = Math.round(Math.random() * 200 + 100)
                homejson[id].money += bonus
                await this.dataManager.saveUserHome(id, homejson[id])
                
                e.reply([
                    global.segment.at(id), "\n",
                    `😌 轻松的分手让你心情不错\n`,
                    `💰 意外获得${bonus}金币！`
                ])
            }
        }, 5000)
    }
    //移除自己的银啪成员
    async nofuck(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        if (!e.at) {
            e.reply(`请at你不想邀请银啪的人`)
            return
        }
        var id = e.user_id
        var filename = e.group_id + `.json`
        var inpajson = await dataManager.getUserxiaoqie(id)
        // 安全检查：确保inpajson和用户数据存在
        if (inpajson && inpajson[id] && inpajson[id].fuck) {
            inpajson[id].fuck = inpajson[id].fuck.filter(item => item != e.at)//去掉老婆
            await dataManager.saveUserXiaoqie(id, inpajson[id])
        } else {
            e.reply(`数据异常，请稍后再试`)
            return
        }
        e.reply(`${e.at}已被你踢出了银啪!`)
    }
    //退出他人的银啪行列
    async fuckno(e){
        if (!e.at) {
            e.reply(`请at你不想加入银啪的人`)
            return
        }
        var id = e.at
        var filename = e.group_id + `.json`
        var inpajson = await dataManager.getUserxiaoqie(id)
        // 安全检查：确保inpajson和用户数据存在
        if (inpajson && inpajson[id] && inpajson[id].fuck) {
            inpajson[id].fuck = inpajson[id].fuck.filter(item => item != e.user_id)//去掉老婆
            await dataManager.saveUserXiaoqie(id, inpajson[id])
        } else {
            e.reply(`数据异常，请稍后再试`)
            return
        }
        e.reply(`你成功退出了${e.at}的银啪!`)
    }
    //家庭信息，可以@别人
    async read(e) {
        if (e.atme || e.atall) {
            e.reply(`不可以这样！`)
            return
        }//@了所有人和机器人
        var id = e.user_id
        var filename = e.group_id + `.json`
        
        //读取家庭和房子信息
        var homejson = await dataManager.getUserHome(id)
        var housejson = await dataManager.getUserHouse(id)
        var inpajson = await dataManager.getUserxiaoqie(id)
        var battlejson = await dataManager.getUserBattle(id)
        var placejson = await dataManager.getUserPlace(id)
        var workHistory = await dataManager.getUserWorkHistory(id) || []
        
        //如果有人被@
        if (e.at) id = e.at
        
        // 检查用户数据是否存在，如果不存在则创建基础数据
        if (!homejson[id]) {
            await this.creat_(e, id)
            homejson = await dataManager.getUserHome(id)
        }
       
        
        
        //获取你是哪些人的老婆
        let iswife_list = []
        //遍历这个群里面所有人
        for (let j of Object.keys(homejson)) {
            //如果这个人的老婆 == id
            if (homejson[j].s == id)
                iswife_list.push(Number(j))
        }
        
        // 增强的房屋信息，集成位置和战斗系统
        let locationName = this.getLocationName(placejson[id]?.place || 'home')
        let battleInfo = battlejson[id] ? `\n⚔️ 战斗等级: Lv.${battlejson[id].level || 0} (${battlejson[id].levelname || '无等级'})\n✨ 经验值: ${battlejson[id].experience || 0}` : ''
        let privilegeInfo = battlejson[id]?.Privilege ? `\n👑 特权等级: ${battlejson[id].Privilege}` : ''
        
        var msg_house = `💰 你现在还剩下${homejson[id].money}金币\n🏠 你的住所信息为\n🏡 名字：${housejson[id].name}\n📦 容量：${housejson[id].space}\n💎 价值：${housejson[id].price}金币\n💕 好感倍率：${housejson[id].loveup}\n📍 当前位置：${locationName}${battleInfo}${privilegeInfo}`
        
        // 工作记录信息（仅自己可见）
        let workInfo = ''
        if (workHistory.length > 0 && !e.at) {
            let recentWork = workHistory.slice(-3).reverse()
            workInfo = '\n\n💼 最近工作记录：\n'
            for (let work of recentWork) {
                workInfo += `📅 ${work.time}: ${work.job_name} (+${work.total_money}金币)\n`
            }
        }
        
        // 冷却时间信息（仅自己可见）
        let cooldownInfo = ''
        if (!e.at) {
            let cooldowns = await this.getCooldownStatus(e, id)
            if (cooldowns.length > 0) {
                cooldownInfo = '\n\n⏰ 冷却状态：\n'
                for (let cd of cooldowns) {
                    cooldownInfo += `${cd.name}: ${cd.status}\n`
                }
            }
        }
        
        //你对老婆的好感
        var msg_love3 = ""
        //开头语
        var msgstart = ""
        
        //有老婆的
        if (homejson[id].s !== 0 && homejson[id].s !== undefined && homejson[id].s !== null && homejson[id].s !== '') {
            //用people函数判断下这个人是男是女
            var she_he = await this.people(e, 'sex', homejson[id].s)
            //用people函数获取昵称
            var name = await this.people(e, 'nickname', homejson[id].s)
            //你的老婆和好感度
            var msg_love2 = `${she_he}对你的好感度为：${homejson[id].love}\n`
            
            //两情相悦的
            if (iswife_list.includes(Number(homejson[id].s))) {
                let mywife = homejson[id].s
                msgstart = `💕 两心靠近是情缘,更是吸引;\n💖 两情相悦是喜欢,更是眷恋。\n🌹 和你两情相悦的人是${name},\n`
                msg_love3 = `💝 你对${she_he}的好感为${homejson[mywife].love}\n`
                //把喜欢你的人从这个数组去除
                iswife_list.splice(iswife_list.indexOf(homejson[id].s), 1)
            }
            //不是两情相悦的
            else {
                msgstart = `💑 你的群友老婆是${name}\n`
            }
        }
        //单身的
        else {
            msgstart = `💔 现在的你还是一位单身贵族，没有老婆哦\n`
            var msg_love2 = '' // 单身的没有msg_love2
        }
        
        //对msg_love处理
        //喜欢你的人
        let msg_love = '💘 喜欢你但是你不喜欢的人有：\n'
        if (iswife_list.length > 0) {
            var notlqxyk = iswife_list.filter(item => item != Number(homejson[id].s))//去掉老婆
            for (let i of notlqxyk) {
                let admirerName = await this.people(e, 'nickname', i)
                msg_love = msg_love + `👤 ${admirerName}(${i})\n💖 好感度为：${homejson[i].love}\n`
            }
            msg_love = msg_love + `💡 快去处理一下吧\n`
        }
        else msg_love = '💘 喜欢你但是你不喜欢的人有：\n😔 一个也没有\n'
        
        //查询银啪人员（仅自己可见）
        let inpamsg = []
        if (!e.at && inpajson[id] && inpajson[id].fuck) {
            inpamsg.push(`🔥 可以与你银啪的有\n`)
            for(let inpa of inpajson[id].fuck){
                let inpaName = await this.people(e, 'nickname', inpa)
                inpamsg.push(`👥 ${inpaName}\n`)
            }
            if (inpajson[id].kun) {
                inpamsg.push(`🍆 牛牛长度: ${inpajson[id].kun}cm\n`)
            }
            inpamsg.push(`🎯 你已经发起了${inpajson[id].fucktime || 0}次银啪`)
        }
        
        // 互动建议（基于当前状态，仅自己可见）
        let suggestions = []
        if (!e.at) {
            suggestions.push('\n💡 建议操作：\n')
            
            if (!homejson[id].s || homejson[id].s === '') {
                suggestions.push('💘 使用 #娶群友 寻找伴侣\n')
            } else {
                if (homejson[id].love < 500) {
                    suggestions.push('💕 使用 #抱抱 增加好感度\n')
                }
                suggestions.push('💰 使用 #打工 赚取金币\n')
                if (inpajson[id] && inpajson[id].fuck && inpajson[id].fuck.length > 0) {
                    suggestions.push('🔥 使用 #开始银啪 进行互动\n')
                }
            }
            
            if (homejson[id].money < 500) {
                suggestions.push('🆘 使用 #领取低保 获得基础金币\n')
            }
            
            if (!housejson[id] || housejson[id].loveup <= 1) {
                suggestions.push('🏠 使用 #看房 #买房 改善居住条件\n')
            }
            
            if ((placejson[id]?.place || 'home') === 'home') {
                suggestions.push('🌍 使用 #去城市 #去商业区 探索更多功能\n')
            }
            
            // 根据位置提供特定建议
            let currentPlace = placejson[id]?.place || 'home'
            if (currentPlace === 'city') {
                suggestions.push('🏦 使用 #去银行 进行金融操作\n')
                suggestions.push('💰 使用 #抢银行 获取大量金币（有风险）\n')
            } else if (currentPlace === 'business') {
                suggestions.push('🛍️ 使用 #逛街 寻找礼物\n')
            }
        }
        
        var msg = []
        //最后回复信息
        if (homejson[id].s !== 0 && homejson[id].s !== undefined && homejson[id].s !== null && homejson[id].s !== '') {
            msg.push([
                global.segment.at(e.user_id), "\n",
                global.segment.image(`https://q1.qlogo.cn/g?b=qq&s=0&nk=${id}`), "\n",
                msgstart,
                global.segment.image(`https://q1.qlogo.cn/g?b=qq&s=0&nk=${homejson[id].s}`), "\n",
                msg_love2 || '',
                msg_love3,
            ])
            msg.push(msg_love)
            msg.push(msg_house + workInfo + cooldownInfo)
            if (inpamsg.length > 0) {
                msg.push(inpamsg.join(''))
            }
            if (suggestions.length > 0) {
                msg.push(suggestions.join(''))
            }
            Config.getforwardMsg(msg, e)
        }
        else {
            msg.push([
                global.segment.at(e.user_id), "\n",
                global.segment.image(`https://q1.qlogo.cn/g?b=qq&s=0&nk=${id}`), "\n",
                msgstart,
            ])
            msg.push(msg_love)
            msg.push(msg_house + workInfo + cooldownInfo)
            if (suggestions.length > 0) {
                msg.push(suggestions.join(''))
            }
            Config.getforwardMsg(msg, e)
        }
        
        return true;
    }
    //打工
    async getmoney(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        if (await this.is_jinbi(e) == true) return
        
        var id = e.user_id
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        var housejson = await dataManager.getUserHouse(id)
        var battlejson = await dataManager.getUserBattle(id)
        var workjson = await dataManager.loadJsonData(workpath)
        
        // 检查是否有老婆
        if (!homejson[id] || homejson[id].s === '') {
            e.reply(`醒醒,你还在这里没有老婆!!没有老婆谁给你工作动力?`)
            return
        }
        
        // 检查位置数据是否存在，如果不存在则创建默认数据
        if (!placejson[id]) {
            placejson[id] = { place: "home" }
            await dataManager.saveUserPlace(id, placejson[id])
        }
        
        // 检查冷却时间
        let UserPAF = battlejson[id].Privilege
        let lastTime = await redis.ttl(`akasha:wife-work-cd:${e.group_id}:${id}`);
        if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
            e.reply([
                global.segment.at(id), "\n",
                `等会儿哦！(*/ω＼*)`, "\n",
                `该命令还有${Math.ceil(lastTime / 60)}分钟cd`
            ]);
            return
        }
        
        // 检查位置数据是否存在，如果不存在则创建默认数据
        if (!placejson[id]) {
            placejson[id] = { place: "home" }
            await dataManager.saveUserPlace(id, placejson[id])
        }
        
        // 检查位置
        if (placejson[id].place !== "home") {
            e.reply([
                global.segment.at(id), "\n",
                `你不在家,不能出去工作,当前位置为：${placejson[id].place}\n请先[回家]`
            ])
            return
        }
        
        if (await this.is_killed(e, 'getmoney', true) == true) { return }
        
        var msg = e.msg.replace(/(打工赚钱|打工|#)/g, "").replace(/[\n|\r]/g, "，").trim()
        
        // 如果没有指定工作类型，显示工作列表
        if (!msg || !workjson.jobs[msg]) {
            let jobList = []
            jobList.push('📋 可选择的工作类型:')
            for (let jobId of Object.keys(workjson.jobs)) {
                let job = workjson.jobs[jobId]
                let loveReq = workjson.work_requirements.min_love[jobId] || 0
                let moneyReq = workjson.work_requirements.min_money[jobId] || 0
                let canWork = homejson[id].love >= loveReq && homejson[id].money >= moneyReq
                let status = canWork ? '✅' : '❌'
                jobList.push(`${status} ID:${jobId} - ${job.name}\n${job.description}\n💰收入:${job.base_money[0]}-${job.base_money[1]} 💖要求好感:${loveReq} 💰要求金币:${moneyReq}\n`)
            }
            jobList.push('\n使用方法: #打工 [工作ID]\n例如: #打工 1')
            Config.getforwardMsg(jobList, e)
            return true
        }
        
        let job = workjson.jobs[msg]
        let loveReq = workjson.work_requirements.min_love[msg] || 0
        let moneyReq = workjson.work_requirements.min_money[msg] || 0
        
        // 检查工作要求
        if (homejson[id].love < loveReq) {
            e.reply(`好感度不足！${job.name}需要至少${loveReq}好感度，当前好感度：${homejson[id].love}`)
            return
        }
        
        if (homejson[id].money < moneyReq) {
            e.reply(`金币不足！${job.name}需要至少${moneyReq}金币作为启动资金，当前金币：${homejson[id].money}`)
            return
        }
        
        // 开始工作
        let startMsg = workjson.work_messages.start[Math.floor(Math.random() * workjson.work_messages.start.length)]
        e.reply([
            global.segment.at(id), "\n",
            `${startMsg}\n`,
            `你选择了工作：${job.name}\n`,
            `${job.description}\n`,
            `正在努力工作中...`
        ])
        
        // 设置冷却时间
        await redis.set(`akasha:wife-work-cd:${e.group_id}:${id}`, currentTime, {
            EX: cdTime3
        });
        
        // 更新位置
        placejson[id].place = "working"
        await dataManager.saveUserPlace(id, placejson[id])
        
        // 计算收入
        let baseMoney = Math.floor(Math.random() * (job.base_money[1] - job.base_money[0] + 1)) + job.base_money[0]
        
        // 好感度加成
        let loveBonus = Math.floor(baseMoney * job.love_bonus * (homejson[id].love / 1000))
        
        // 房屋加成
        let houseBonus = Math.floor(baseMoney * job.house_bonus * (housejson[id].loveup - 1))
        
        let totalMoney = baseMoney + loveBonus + houseBonus
        let loveGain = Math.floor(Math.random() * 10 + 5) // 基础好感度增加5-14
        
        // 检查特殊事件
        let eventMsg = ""
        let eventMoneyBonus = 0
        let eventLoveBonus = 0
        
        for (let eventId of Object.keys(job.special_events)) {
            let event = job.special_events[eventId]
            if (Math.random() < event.probability) {
                eventMsg = event.msg
                eventMoneyBonus = event.money_bonus || 0
                eventLoveBonus = event.love_bonus || 0
                break
            }
        }
        
        totalMoney += eventMoneyBonus
        loveGain += eventLoveBonus
        
        // 应用房屋好感度加成
        loveGain = Math.floor(loveGain * housejson[id].loveup)
        
        setTimeout(async () => {
            // 更新数据
            homejson[id].money += totalMoney
            homejson[id].love += loveGain
            placejson[id].place = "home" // 工作完成后回家
            
            let resultMsg = [
                global.segment.at(id), "\n",
                `🎉 工作完成！\n`,
                `💼 工作：${job.name}\n`,
                `💰 基础收入：${baseMoney}\n`
            ]
            
            if (loveBonus > 0) {
                resultMsg.push(`💖 好感加成：+${loveBonus}\n`)
            }
            if (houseBonus > 0) {
                resultMsg.push(`🏠 房屋加成：+${houseBonus}\n`)
            }
            if (eventMsg) {
                resultMsg.push(`🎲 特殊事件：${eventMsg}\n`)
                if (eventMoneyBonus > 0) {
                    resultMsg.push(`🎁 事件奖励：+${eventMoneyBonus}金币\n`)
                }
                if (eventLoveBonus > 0) {
                    resultMsg.push(`💕 额外好感：+${eventLoveBonus}\n`)
                }
            }
            
            resultMsg.push(`\n💰 总收入：${totalMoney}金币\n`)
            resultMsg.push(`💖 好感度：+${loveGain} (当前：${homejson[id].love})\n`)
            resultMsg.push(`💳 当前金币：${homejson[id].money}`)
            
            e.reply(resultMsg)
            
            // 更新任务进度
             const { QuestSystem } = await import('../../components/quest_system.js')
             const questSystem = new QuestSystem()
             await questSystem.updateQuestProgress(id, e.group_id, 'max_money', homejson[id].money)
             await questSystem.updateQuestProgress(id, e.group_id, 'max_love', homejson[id].love)
             await questSystem.updateQuestProgress(id, e.group_id, 'work_count', 1)
             
             // 保存工作记录
             let workRecord = {
                 time: currentTime,
                 job_name: job.name,
                 job_id: msg,
                 base_money: baseMoney,
                 love_bonus: loveBonus,
                 house_bonus: houseBonus,
                 event_bonus: eventMoneyBonus,
                 total_money: totalMoney,
                 love_gain: loveGain,
                 event_msg: eventMsg
             }
             
             // 获取或创建工作历史
             let workHistory = await dataManager.getUserWorkHistory(id) || []
             workHistory.push(workRecord)
             
             // 只保留最近50条记录
             if (workHistory.length > 50) {
                 workHistory = workHistory.slice(-50)
             }
             
             await dataManager.saveUserWorkHistory(id, workHistory)
             
             // 保存数据
             await dataManager.saveUserHome(id, homejson[id])
             await dataManager.saveUserPlace(id, placejson[id])
            
            // 检查是否触发其他事件
            if (await this.is_fw(e, homejson) == true) return
            
        }, 3000) // 3秒后显示结果，模拟工作时间
        
        return true
    }
    
    //工作状态查询
    async workstatus(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        var housejson = await dataManager.getUserHouse(id)
        var battlejson = await dataManager.getUserBattle(id)
        var workjson = await dataManager.loadJsonData(workpath)
        
        if (!homejson[id] || homejson[id].s === '') {
            e.reply(`醒醒,你还在这里没有老婆!!没有老婆谁给你工作动力?`)
            return
        }
        
        // 检查冷却时间
        let lastTime = await redis.ttl(`akasha:wife-work-cd:${e.group_id}:${id}`);
        let cdStatus = lastTime === -2 ? '✅ 可以工作' : `⏰ 冷却中 (${Math.ceil(lastTime / 60)}分钟)`
        
        // 计算可用工作
        let availableJobs = []
        let unavailableJobs = []
        
        for (let jobId of Object.keys(workjson.jobs)) {
            let job = workjson.jobs[jobId]
            let loveReq = workjson.work_requirements.min_love[jobId] || 0
            let moneyReq = workjson.work_requirements.min_money[jobId] || 0
            let canWork = homejson[id].love >= loveReq && homejson[id].money >= moneyReq
            
            if (canWork) {
                availableJobs.push(`✅ ${job.name} (收入:${job.base_money[0]}-${job.base_money[1]})`)
            } else {
                let reason = []
                if (homejson[id].love < loveReq) reason.push(`需要好感${loveReq}`)
                if (homejson[id].money < moneyReq) reason.push(`需要金币${moneyReq}`)
                unavailableJobs.push(`❌ ${job.name} (${reason.join(', ')})`)
            }
        }
        
        // 计算工作效率加成
        let loveBonus = Math.floor((homejson[id].love / 1000) * 100)
        let houseBonus = Math.floor((housejson[id].loveup - 1) * 100)
        
        let statusMsg = [
            `👤 ${await this.people(e, 'nickname', id)} 的工作状态\n`,
            `💼 当前状态: ${cdStatus}\n`,
            `📍 当前位置: ${placejson[id].place === 'home' ? '🏠 在家' : placejson[id].place === 'working' ? '💼 工作中' : placejson[id].place}\n`,
            `💰 当前金币: ${homejson[id].money}\n`,
            `💖 当前好感: ${homejson[id].love}\n`,
            `🏠 房屋加成: ${houseBonus}%\n`,
            `💕 好感加成: ${loveBonus}%\n\n`,
            `📋 可用工作 (${availableJobs.length}个):\n`,
            availableJobs.join('\n'),
            availableJobs.length > 0 ? '\n' : '',
            unavailableJobs.length > 0 ? `\n🚫 暂不可用 (${unavailableJobs.length}个):\n${unavailableJobs.join('\n')}\n` : '',
            `\n💡 使用 #打工 [工作ID] 开始工作\n`,
            `💡 使用 #打工 查看详细工作列表`
        ]
        
        e.reply([
            global.segment.at(id), "\n",
            statusMsg.join('')
        ])
        
        return true
     }
     
     //工作记录查询
     async workhistory(e) {
         if (!e.group_id) {
             e.reply('该功能仅支持群聊使用')
             return
         }
         
         var id = e.user_id
         var homejson = await dataManager.getUserHome(id)
         
         if (!homejson[id] || homejson[id].s === '') {
             e.reply(`醒醒,你还在这里没有老婆!!没有老婆谁给你工作动力?`)
             return
         }
         
         let workHistory = await dataManager.getUserWorkHistory(id) || []
         
         if (workHistory.length === 0) {
             e.reply([
                 global.segment.at(id), "\n",
                 `📋 你还没有任何工作记录\n`,
                 `💡 使用 #打工 开始你的第一份工作吧！`
             ])
             return
         }
         
         // 计算统计数据
         let totalEarnings = workHistory.reduce((sum, record) => sum + record.total_money, 0)
         let totalLoveGain = workHistory.reduce((sum, record) => sum + record.love_gain, 0)
         let workCount = workHistory.length
         let avgEarnings = Math.floor(totalEarnings / workCount)
         
         // 统计工作类型
         let jobStats = {}
         workHistory.forEach(record => {
             if (!jobStats[record.job_name]) {
                 jobStats[record.job_name] = { count: 0, earnings: 0 }
             }
             jobStats[record.job_name].count++
             jobStats[record.job_name].earnings += record.total_money
         })
         
         // 获取最近5条记录
         let recentRecords = workHistory.slice(-5).reverse()
         
         let historyMsg = [
             `📊 ${await this.people(e, 'nickname', id)} 的工作记录\n\n`,
             `📈 总体统计:\n`,
             `💼 总工作次数: ${workCount}次\n`,
             `💰 总收入: ${totalEarnings}金币\n`,
             `💖 总好感获得: ${totalLoveGain}\n`,
             `📊 平均收入: ${avgEarnings}金币/次\n\n`,
             `🏆 工作类型统计:\n`
         ]
         
         // 添加工作类型统计
         for (let jobName of Object.keys(jobStats)) {
             let stat = jobStats[jobName]
             let avgJobEarnings = Math.floor(stat.earnings / stat.count)
             historyMsg.push(`• ${jobName}: ${stat.count}次 (平均${avgJobEarnings}金币)\n`)
         }
         
         historyMsg.push(`\n📝 最近5次工作记录:\n`)
         
         // 添加最近记录
         recentRecords.forEach((record, index) => {
             let timeStr = record.time.split(' ')[1].substring(0, 5) // 只显示时分
             let eventStr = record.event_msg ? ` 🎲${record.event_msg.substring(0, 10)}...` : ''
             historyMsg.push(`${index + 1}. ${record.job_name} (${timeStr}) +${record.total_money}💰${eventStr}\n`)
         })
         
         historyMsg.push(`\n💡 使用 #打工状态 查看当前状态`)
         
         e.reply([
             global.segment.at(id), "\n",
             historyMsg.join('')
         ])
         
         return true
     }
     
     //看房
    async gethouse(e) {
        var housething = await dataManager.loadJsonData(housepath);//读取文件
        var msg = []
        msg.push('欢迎光临,请过目:')
        var house = []
        for (let i of Object.keys(housething)) {
            msg.push(`id: ${i}\n${housething[i].name}\n容量: ${housething[i].space}\n价格: ${housething[i].price}\n好感增幅: ${housething[i].loveup}\n`)
        }
        Config.getforwardMsg(msg,e)
        return true
    }
    //买房,可以给别人买
    async buyhouse(e) {
        var housething = await dataManager.loadJsonData(housepath);//读取文件
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var housejson = await dataManager.getUserHouse(id)
        var msg = e.msg.replace(/(买房|#)/g, "").replace(/[\n|\r]/g, "，").trim()
        if (homejson[id].money < housething[msg].price) {
            e.reply(`金币不足`)
            return
        }
        if (await this.is_killed(e, 'buyhouse', true) == true) return
        let buyerId = e.user_id  // 购买者ID
        if (e.at) id = e.at      // 受益者ID
        homejson[buyerId].money -= housething[msg].price
        housejson[id].space += housething[msg].space
        housejson[id].loveup += housething[msg].loveup
        housejson[id].price += housething[msg].price
        await dataManager.saveUserHome(buyerId, homejson[buyerId])  // 保存购买者数据
        await dataManager.saveUserHouse(id, housejson[id])         // 保存受益者房屋数据
        e.reply(`购买成功,你本次为${id}消费${housething[msg].price}金币`)
        return true;
    }
    //住所改名
    async namedhouse(e) {
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var housejson = await dataManager.getUserHouse(id)
        var msg = e.msg.replace(/(住所改名|#)/g, "").replace(/[\n|\r]/g, "，").trim()
        var shifu = housejson[id].space * 10
        if (homejson[id].money < shifu) {
            e.reply(`金币不足,需要${shifu}金币`)
            return
        }
        homejson[id].money -= shifu
        housejson[id].name = msg
        await dataManager.saveUserHome(id, homejson[id])
        await dataManager.saveUserHouse(id, housejson[id])
        e.reply(`改名"${msg}"成功`)
        return true;
    }
    //逛街
    async gift(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        if (await this.is_jinbi(e) == true) return
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        var giftthing = await dataManager.loadJsonData(giftpath);//读取文件
        if (!homejson[id] || homejson[id].s == 0) {//如果json中不存在该用户或者老婆s为0
            e.reply(`醒醒,你还在这里没有老婆!!`)
            return
        }
        var battlejson = await dataManager.getUserBattle(id)
        let UserPAF = battlejson[id].Privilege
        let lastTime = await redis.ttl(`akasha:wife-gift-cd:${e.group_id}:${e.user_id}`);
        if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
            e.reply([
                global.segment.at(e.user_id), "\n",
                `等会儿哦！(*/ω＼*)`, "\n",
                `该命令还有${lastTime / 60}分cd`
            ]);
            return
        }
        if (!placejson[id]) {
            placejson[id] = { place: "home" };
            await dataManager.saveUserPlace(id, placejson[id]);
        }
        if (placejson[id].place !== "home") {
            e.reply([
                global.segment.at(id), "\n",
                `你不在家,不能进行逛街,当前位置为：${placejson[id].place}`
            ])
            return
        }
        if (await this.is_killed(e, 'gift', true) == true) { return }
        var placeid = Math.round(Math.random() * (Object.keys(giftthing.placename).length - 1))//随机获取一个位置id
        var placemsg = giftthing.start[placeid + 1]//获取消息
        e.reply([
            global.segment.at(id), "\n",
            `${placemsg}\n`,
            `你选择[进去看看]还是[去下一个地方]?`
        ])
        placejson[id].place = giftthing.placename[placeid]
        await dataManager.saveUserPlace(id, placejson[id])//保存位置
        await redis.set(`akasha:wife-gift-cd:${e.group_id}:${e.user_id}`, currentTime, {
            EX: cdTime5
        });
        return true;
    }
    //逛街事件结束
    async gift_continue(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        if (await this.is_jinbi(e) == true) return
        if (await this.is_MAXEX(e, 'gift') == true) return
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        var housejson = await dataManager.getUserHouse(id)
        if (!homejson[e.user_id] || homejson[e.user_id].money <= 0) {
            e.reply(`金币都没了,还是别进去了吧`)
            return
        }
        var giftthing = await dataManager.loadJsonData(giftpath);//读取位置资源文件
        if (!placejson[id]) {
            placejson[id] = { place: "home" };
            await dataManager.saveUserPlace(id, placejson[id]);
        }
        if (placejson[id].place == "home") {
            e.reply([
                global.segment.at(id), "\n",
                `你在家,先逛街出去吧`
            ])
            return
        }
        if (!homejson[id] || homejson[id].s == 0) {//如果json中不存在该用户或者老婆s为0
            e.reply(`醒醒,你还在这里没有老婆!!`)
            return
        }
        if (placejson[id].place == "any")
            return
        if (await this.is_killed(e, 'gift', true) == true) { return }
        var userplacename = placejson[id].place//获取玩家位置名A
        var placemodle = giftthing[userplacename]//获取位置资源中的位置A的数据B
        var placeid = Math.round(Math.random() * (Object.keys(placemodle).length - 1) + 1)//随机从B中选择一个位置id
        var placemsg = placemodle[placeid].msg//获取消息
        e.reply(`${placemsg}`)
        placejson[id].place = "any"
        placejson[id].placetime++
        homejson[id].money += placemodle[placeid].money
        homejson[id].love += Math.round(placemodle[placeid].love * housejson[id].loveup)
        
        // 更新特殊任务进度
          const { QuestSystem } = await import('../../components/quest_system.js')
          const questSystem = new QuestSystem()
        await questSystem.updateQuestProgress(id, e.group_id, 'max_money', homejson[id].money)
          await questSystem.updateQuestProgress(id, e.group_id, 'max_love', homejson[id].love)
        setTimeout(() => {
            e.reply([
                global.segment.at(id), "\n",
                `恭喜你,你本次的行动结果为,金币至${homejson[id].money},好感度至${homejson[id].love}\n你可以选择[去下一个地方]或者[回家]\n当前剩余行动点${gifttime - placejson[id].placetime}`
            ])
        }, 2000)
        await dataManager.saveUserHome(id, homejson[id])
        await dataManager.saveUserPlace(id, placejson[id])//保存位置
        if (await this.is_fw(e, homejson) == true) return
        return true;
    }
    //逛街事件继续
    async gift_over(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        if (await this.is_jinbi(e) == true) return
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        var giftthing = await dataManager.loadJsonData(giftpath);//读取位置资源文件
        if (!placejson[id]) {
            placejson[id] = { place: "home" };
            await dataManager.saveUserPlace(id, placejson[id]);
        }
        if (placejson[id].place == "home") {
            e.reply([
                global.segment.at(id), "\n",
                `你在家,先逛街出去吧`
            ])
            return
        }
        if (await this.is_killed(e, 'gift', true) == true) { return }
        var placeid = Math.round(Math.random() * (Object.keys(giftthing.placename).length - 1))//随机获取一个位置id
        var placemsg = giftthing.start[placeid + 1]//获取消息
        e.reply([
            global.segment.at(id), "\n",
            `${placemsg}\n`,
            `你选择[进去看看]还是[去下一个地方]?`
        ])
        placejson[id].place = giftthing.placename[placeid]
        await dataManager.saveUserPlace(id, placejson[id])//保存位置
        return true;
    }
    //回家
    async gohome(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        if (await this.is_jinbi(e) == true) return
        var id = e.user_id
        var filename = e.group_id + `.json`
        var placejson = await dataManager.getUserPlace(id)
        if (!placejson[id]) {
            placejson[id] = { place: "home" };
            await dataManager.saveUserPlace(id, placejson[id]);
        }
        if (placejson[id].place == "home") {
            e.reply([
                global.segment.at(id), "\n",
                `你已经在家了`
            ])
            return
        }
        if (await this.is_killed(e, 'gohome', true) == true) { return }
        e.reply([
            global.segment.at(id), "\n",
            `你回到了家`
        ])
        placejson[id].place = "home"
        placejson[id].placetime = 0
        await dataManager.saveUserPlace(id, placejson[id])//保存位置
        return true;
    }
    //买虚空彩球
    async lottery1(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        var id = e.user_id
        let myRBB = await redis.keys(`akasha:wife-lottery1:${e.group_id}:${id}:*`, (err, data) => { });
        myRBB = myRBB.toString().split(":")
        if (myRBB.length == 7) {
            e.reply([
                global.segment.at(id), "\n",
                `你买过了`
            ])
            return
        }
        var battlejson = await dataManager.getUserBattle(id)
        let UserPAF = battlejson[id].Privilege
        let lastTime = await redis.ttl(`akasha:wife-lottery1-cd:${e.group_id}:${id}`);
        if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
            e.reply([
                global.segment.at(e.user_id), "\n",
                `等会儿哦！(*/ω＼*)`, "\n",
                `该命令还有${lastTime / 60}分cd`
            ]);
            return
        }
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        if (!placejson[id]) {
            placejson[id] = { place: "home" };
            await dataManager.saveUserPlace(id, placejson[id]);
        }
        if (placejson[id].place !== "SportsLottery") {
            e.reply([
                global.segment.at(id), "\n",
                `你不在游乐场店周围,当前位置为：${placejson[id].place}`
            ])
            return
        }
        var msg = e.msg.replace(/(获取虚空彩球|#)/g, "").replace(/[\n|\r]/g, "")
        var haoma = msg.split(" ")
        var redball = haoma.slice(0, -1)
        var blueball = haoma[6]
        console.log(haoma)
        console.log(redball)
        console.log(blueball)
        if (blueball > 16 || redball.length !== new Set(redball).size) {
            e.reply(`输入有误,篮球不能超过16,红球不能含有重复号码`)
            return
        }
        for (var b = 0; b < haoma.length; b++) {
            if (haoma[b] > 33 || haoma[b] == '00') {
                e.reply(`输入有误,红球号码不能超过33,号码不能为00`)
                return
            }
        }
        if (homejson[id].money < 300)
            return e.reply(`金币不足,需要300金币`)
        let buytime = `${new Date().getFullYear()}-${new Date().getMonth() + 1}-${new Date().getDate()}`
        let ssqdata = `红${redball.toString()}蓝${blueball}时间${buytime}`
        console.log(`${id}获取虚空彩球${ssqdata}`)
        await redis.set(`akasha:wife-lottery1:${e.group_id}:${id}:${redball.toString()}:${blueball}:${buytime}`, currentTime, {
            EX: 86400
        });
        homejson[id].money -= 300
        await dataManager.saveUserHome(id, homejson[id])
        await redis.set(`akasha:wife-lottery1-cd:${e.group_id}:${id}`, currentTime, {
            EX: cdTime8
        });
        e.reply(`你选择了${ssqdata}`)
        return true;
    }
    //看看自己的虚空彩球
    async readRBB(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        let myRBB = await redis.keys(`akasha:wife-lottery1:${e.group_id}:${e.user_id}:*`, (err, data) => { });
        myRBB = myRBB.toString().split(":")
        console.log(myRBB)
        switch (myRBB.length) {
            case 1:
                e.reply(`你还没买或已过期`)
                break
            case 7:
                e.reply(`你的虚空彩球为红球${myRBB[4]},蓝球${myRBB[5]},购买时间${myRBB[6]},有效期24小时`)
                break
            default:
                e.reply(`存在错误数据,请联系管理者[清除老婆数据]`)
        }
        return true;
    }
    //兑换虚空彩球
    async useRBB(e) {
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var AmyRBB = await redis.keys(`akasha:wife-lottery1:${e.group_id}:${e.user_id}:*`, (err, data) => { });
        var myRBB = AmyRBB.toString().split(":")
        if (myRBB.length == 1) {
            e.reply(`你还没买或已过期`)
            return
        }
        if (myRBB.length == 7) {
            var trueRBBjson = await dataManager.loadJsonData(lotterypath);//读取文件
            let title = "RBB"
            var trueR = (trueRBBjson[title].redball).toString().split(",")
            var trueB = trueRBBjson[title].blueball
            var trueTime = trueRBBjson[title].time
            console.log(trueR)
            console.log(trueB)
            var lastR = []
            var myR = myRBB[4].split(",")
            console.log(myR)
            var myB = myRBB[5].toString()
            console.log(myB)
            var mytime = myRBB[6]
            console.log(`购买时间${mytime}当前开奖时间${trueTime}`)
            if (mytime !== trueTime)
                return e.reply(`未开奖或已过期`)
            trueR.some(function (i) {
                if (myR.includes(i))
                    lastR.push(i)
            })
            console.log(lastR)
            switch (lastR.length) {
                case 6:
                    if (myB == trueB) {
                        e.reply(`恭喜你!!!获得一等奖50万金币!!!`)
                        homejson[id].money += 5000000
                    }
                    else {
                        homejson[id].money += 200000
                        e.reply(`恭喜你!!!获得二等奖20万金币!!!`)
                    }
                    break
                case 5:
                    if (myB == trueB) {
                        e.reply(`恭喜你!!!获得三等奖5万金币!!!`)
                        homejson[id].money += 50000
                    }
                    else {
                        homejson[id].money += 20000
                        e.reply(`恭喜你!!!获得四等奖2万金币!!!`)
                    }
                    break
                case 4:
                    if (myB == trueB) {
                        e.reply(`恭喜你!!!获得四等奖2万金币!!!`)
                        homejson[id].money += 20000
                    }
                    else {
                        homejson[id].money += 1000
                        e.reply(`恭喜你!!!获得五等奖1千金币!!!`)
                    }
                    break
                case 3:
                    if (myB == trueB) {
                        e.reply(`恭喜你!!!获得五等奖1千金币!!!`)
                        homejson[id].money += 1000
                    }
                    else {
                        homejson[id].money += 6
                        e.reply(`安慰奖6个金币!`)
                    }
                    break
                case 2:
                    if (myB == trueB) {
                        e.reply(`恭喜你!!!获得六等奖5百金币!!!`)
                        homejson[id].money += 500
                    }
                    else {
                        homejson[id].money += 6
                        e.reply(`安慰奖6个金币!`)
                    }
                    break
                case 1:
                    if (myB == trueB) {
                        e.reply(`恭喜你!!!获得六等奖5百金币!!!`)
                        homejson[id].money += 500
                    }
                    else {
                        homejson[id].money += 6
                        e.reply(`安慰奖6个金币!`)
                    }
                    break
                default:
                    e.reply(`一个也没中`)
            }
            await dataManager.saveUserHome(id, homejson[id])
        }
        else {
            e.reply(`存在错误数据,请联系管理者[清除老婆数据]`)
        }
        await redis.del(AmyRBB);
        e.reply(`成功兑换,请查看你的信息`)
        return true;
    }
    //抱抱,有千分之一的概率被干掉
    async touch(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        
        var id = e.user_id
        var homejson = await this.dataManager.getUserHome(id)
        var placejson = await this.dataManager.getUserPlace(id)
        var battlejson = await this.dataManager.getUserBattle(id)
        var housejson = await this.dataManager.getUserHouse(id)
        
        // 检查是否有老婆
        if (!homejson[id] || homejson[id].s === '' || homejson[id].s === 0) {
            e.reply([
                global.segment.at(id), "\n",
                `你还没有老婆，无法抱抱！\n`,
                `💡 可以通过[娶群友]或[表白]功能寻找伴侣`
            ])
            return
        }
        
        // 检查是否在监狱
        let currentPlace = placejson[id] || { place: 'home' }
        if (currentPlace.place === 'prison') {
            e.reply([
                global.segment.at(id), "\n",
                `你在监狱里，无法抱抱老婆！\n`,
                `⛓️ 等出狱后再说吧...`
            ])
            return
        }
        
        // 检查冷却时间
        let UserPAF = battlejson[id]?.Privilege
        let isDev = this.checkDevPermission(e)
        let lastTime = await redis.ttl(`akasha:wife-touch-cd:${e.group_id}:${id}`)
        
        if (lastTime !== -2 && !UserPAF && !isDev) {
            e.reply([
                global.segment.at(id), "\n",
                `抱抱功能冷却中！(*/ω＼*)\n`,
                `还需等待${Math.ceil(lastTime / 60)}分钟`
            ])
            return
        }
        
        // 位置加成计算
        let locationBonus = 1.0
        let locationDesc = ''
        
        switch (currentPlace.place) {
            case 'home':
                locationBonus = 1.5
                locationDesc = '在家的温馨环境'
                break
            case 'city':
                locationBonus = 1.2
                locationDesc = '城市的浪漫氛围'
                break
            case 'business':
                locationBonus = 1.1
                locationDesc = '商业区的繁华'
                break
            case 'bank':
                locationBonus = 0.9
                locationDesc = '银行的严肃环境'
                break
            default:
                locationBonus = 1.0
                locationDesc = '普通环境'
                break
        }
        
        // 房屋等级加成
        let houseBonus = (housejson[id]?.loveup || 1)
        
        // 时间加成（晚上抱抱效果更好）
        let hour = new Date().getHours()
        let timeBonus = 1.0
        let timeDesc = ''
        
        if (hour >= 20 || hour <= 6) {
            timeBonus = 1.3
            timeDesc = '夜晚的浪漫时光'
        } else if (hour >= 7 && hour <= 11) {
            timeBonus = 1.2
            timeDesc = '清晨的温柔时光'
        } else {
            timeBonus = 1.0
            timeDesc = '日常时光'
        }
        
        // 计算好感度增加
        let baseLoveGain = 15 + Math.floor(Math.random() * 10)
        let finalLoveGain = Math.floor(baseLoveGain * locationBonus * houseBonus * timeBonus)
        
        // 检查当前好感度，高好感度时抱抱效果递减
        let currentLove = homejson[id].love || 0
        if (currentLove > 200) {
            finalLoveGain = Math.floor(finalLoveGain * 0.7)
        } else if (currentLove > 100) {
            finalLoveGain = Math.floor(finalLoveGain * 0.85)
        }
        
        // 随机事件
        let specialEvent = ''
        let bonusReward = 0
        let randomEvent = Math.random()
        
        if (randomEvent < 0.1) {
            // 10% 概率特殊事件
            specialEvent = '💝 老婆给了你一个惊喜礼物！'
            bonusReward = 50 + Math.floor(Math.random() * 100)
            homejson[id].money += bonusReward
        } else if (randomEvent < 0.2) {
            // 10% 概率额外好感
            specialEvent = '✨ 这次抱抱特别温馨！'
            finalLoveGain = Math.floor(finalLoveGain * 1.5)
        } else if (randomEvent < 0.25) {
            // 5% 概率被打
            specialEvent = '😅 老婆害羞地推开了你...'
            finalLoveGain = Math.floor(finalLoveGain * 0.5)
        }
        
        // 应用好感度变化
        homejson[id].love += finalLoveGain
        
        // 设置冷却时间
        await redis.set(`akasha:wife-touch-cd:${e.group_id}:${id}`, Date.now(), {
            EX: cdTime4
        })
        
        await this.dataManager.saveUserHome(id, homejson[id])
        
        // 更新任务进度
        try {
            const { QuestSystem } = await import('../../components/quest_system.js')
            const questSystem = new QuestSystem()
            await questSystem.updateQuestProgress(id, e.group_id, 'touch_count', 1)
            await questSystem.updateQuestProgress(id, e.group_id, 'max_love', homejson[id].love)
            await questSystem.updateQuestProgress(id, e.group_id, 'interaction_count', 1)
        } catch (err) {
            // 忽略任务系统错误
        }
        
        // 获取老婆名字
        let wifeName = await this.people(e, 'nickname', homejson[id].s)
        
        e.reply([
            global.segment.at(id), "\n",
            `💕 你抱了抱${wifeName}\n`,
            `💖 好感度 +${finalLoveGain}\n`,
            `📍 位置加成：${Math.floor((locationBonus - 1) * 100)}% (${locationDesc})\n`,
            `🏠 房屋加成：${Math.floor((houseBonus - 1) * 100)}%\n`,
            `⏰ 时间加成：${Math.floor((timeBonus - 1) * 100)}% (${timeDesc})\n`,
            specialEvent ? `${specialEvent}\n` : '',
            bonusReward > 0 ? `💰 获得奖励：${bonusReward}金币\n` : '',
            `💕 当前好感度：${homejson[id].love}\n`,
            `⏰ 下次抱抱冷却：${Math.ceil(cdTime4/60)}分钟`
        ])
    }
    //查看本群所有cp
   
    //500以内可以领取低保
    async poor(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        var id = e.user_id
        var battlejson = await dataManager.getUserBattle(id)
        let UserPAF = battlejson[id].Privilege
        let lastTime = await redis.ttl(`akasha:wife-poor-cd:${e.group_id}:${id}`);
        if (lastTime !== -2 && !UserPAF && !this.checkDevPermission(e)) {
            e.reply([
                global.segment.at(id), "\n",
                `等会儿哦！(*/ω＼*)`, "\n",
                `该命令还有${lastTime / 60}分cd`
            ]);
            return
        }
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        if (homejson[id].money < 500) {
            homejson[id].money += 500
            e.reply(`成功领取500金币`)
            await dataManager.saveUserHome(id, homejson[id])
            await redis.set(`akasha:wife-poor-cd:${e.group_id}:${id}`, currentTime, {
                EX: cdTime7
            });
            return
        }
        if (homejson[id].money >= 500) {
            e.reply(`这就是有钱人的嘴脸吗`)
        }
        return true
    }
    //转账功能
    async Transfer_money(e) {
        if (!e.group_id) {
            e.reply('该功能仅支持群聊使用')
            return
        }
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var housejson = await dataManager.getUserHouse(id)
        if (!homejson[id] || homejson[id].s == 0) {
            e.reply([
                global.segment.at(id), "\n",
                `你暂时在这里没有老婆哦,不用上交了`
            ])
            return
        }
        if (homejson[id].money <= 0) {
            e.reply([
                global.segment.at(id), "\n",
                `你自己已经很穷了,上交个啥?`
            ])
            return
        }
        var msg = e.msg.replace(/(上交存款|#)/g, "").replace(/[\n|\r]/g, "，").trim()
        var id2 = homejson[id].s
        var homejson2 = await dataManager.getUserHome(id2)  //给老婆创建存档
        var yingfu = Math.round(msg)
        var shifu = Math.round(yingfu * 1.1)
        e.reply([
            global.segment.at(id), "\n",
            `您本次应付需要${yingfu}金币,实付需要${shifu}`
        ])
        setTimeout(async () => {
            if (!homejson[id] || homejson[id].money < shifu) {
                e.reply([
                    global.segment.at(id), "\n",
                    `你的金币不足,上交失败`
                ])
                return
            }
            else if (homejson[id].money >= shifu) {
                e.reply([
                    global.segment.at(id), "\n",
                    `上交成功\n`,
                    `老婆对你的好感上升了${Math.round(yingfu / 10)}`,
                ])
                homejson[id].money -= shifu
                if (!homejson2[id2]) {
                    homejson2[id2] = { money: 0 }
                }
                homejson2[id2].money += yingfu
                homejson[id].love += Math.round((yingfu / 10) * housejson[id].loveup)
                
                // 更新特殊任务进度
                const { QuestSystem } = await import('../../components/quest_system.js')
          const questSystem = new QuestSystem()
                if (homejson[id].money > 0) {
                     await questSystem.updateQuestProgress(id, e.group_id, 'max_money', homejson[id].money)
                 }
                 await questSystem.updateQuestProgress(id, e.group_id, 'max_love', homejson[id].love)
                 await questSystem.updateQuestProgress(id2, e.group_id, 'max_money', homejson2[id2].money)
                
                await dataManager.saveUserHome(id, homejson[id])
                await dataManager.saveUserHome(id2, homejson2[id2])
            }
        }, 1500)
        return true;
    }
    //清除所有人的本插件redis数据或者指定某个人的
    async delREDIS(e) {
        if (!e.group_id) {
            e.reply("该功能仅支持群聊使用")
            return
        }
        if (e.isMaster) {
            let cddata = await redis.keys(`akasha:*:${e.group_id}:*`, (err, data) => { });
            if (e.at) {
                cddata = await redis.keys(`akasha:*:${e.group_id}:${e.at}`, (err, data) => { });
                e.reply(`成功重置${e.at}的时间`)
            }
            else {
                e.reply(`成功清除本群所有人的的时间`)
            }
            await redis.del(cddata);
            return true;
        }
    }
    //下面的都是函数,调用时需使用awiat等待以免异步执行---------------------------------------------------------//
    //创建存档
    async creat_(e, id) {
        // 不要覆盖传入的id参数
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var placejson = await dataManager.getUserPlace(id)
        var housejson = await dataManager.getUserHouse(id)
        var inpajson = await dataManager.getUserxiaoqie(id)
        
        // 确保用户数据存在，如果不存在则创建默认数据
        if (!homejson[id]) {
            homejson[id] = {
                s: '',
                love: 0,
                money: 500,
                wait: 0
            }
            await dataManager.saveUserHome(id, homejson[id])
        }
        
        if (!placejson[id]) {
            placejson[id] = {
                place: 'home'
            }
            await dataManager.saveUserPlace(id, placejson[id])
        }
        
        if (!housejson[id]) {
            housejson[id] = {
                price: 0,
                space: 0,
                loveup: 1
            }
            await dataManager.saveUserHouse(id, housejson[id])
        }
        
        return { homejson, placejson, housejson, inpajson }
    }
    //看看你是哪些人的老婆函数
    async is_wife(e, id) {
        if (!e.group_id) {
            return []
        }
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        let wifelist = []//看看这个Id是哪些人的老婆
        for (let i of Object.keys(homejson)) {//读取json里面的对象名
            if (homejson[i].s == id)//如果有人的老婆是是这个id
                wifelist.push(i)
        }
        return wifelist
    }
    // 获取位置名称
    getLocationName(place) {
        const locationNames = {
            'home': '🏠 家',
            'city': '🏙️ 城市',
            'business': '🏢 商业区',
            'bank': '🏦 银行',
            'working': '💼 工作中',
            'prison': '⛓️ 监狱',
            'shopping': '🛍️ 逛街中'
        }
        return locationNames[place] || `📍 ${place}`
    }
    
    // 获取冷却状态
    async getCooldownStatus(e, id) {
        let cooldowns = []
        
        const cdChecks = [
            { key: `akasha:wife-touch-cd:${e.group_id}:${id}`, name: '💕 抱抱' },
            { key: `akasha:wife-work-cd:${e.group_id}:${id}`, name: '💼 打工' },
            { key: `akasha:wife-gift-cd:${e.group_id}:${id}`, name: '🛍️ 逛街' },
            { key: `akasha:wife-ntr-cd:${e.group_id}:${id}`, name: '😈 抢老婆' },
            { key: `akasha:wife-Robbery-cd:${e.group_id}:${id}`, name: '💰 抢劫' },
            { key: `akasha:wife-poor-cd:${e.group_id}:${id}`, name: '🆘 低保' },
            { key: `akasha:wife-prison:${e.group_id}:${id}`, name: '⛓️ 监禁' }
        ]
        
        for (let check of cdChecks) {
            try {
                let ttl = await redis.ttl(check.key)
                if (ttl > 0) {
                    let minutes = Math.ceil(ttl / 60)
                    let status = minutes > 60 ? `${Math.ceil(minutes/60)}小时` : `${minutes}分钟`
                    cooldowns.push({ name: check.name, status: status })
                }
            } catch (error) {
                // 忽略Redis错误
            }
        }
        
        return cooldowns
    }
    
    //群成员资料函数
    async people(e, keys, id) {
        let memberMap = await e.group.getMemberMap();
        let arrMember = Array.from(memberMap.values());
        var this_one = arrMember.filter(item => {
            return item.user_id == id
            //用过滤器返回了user_id==id的人
        })
        var lp = this_one[0]
        
        // 安全检查：如果用户不在群中，返回默认值
        if (!lp) {
            if (keys == 'sex') {
                return '他/她'  // 返回中性称呼
            }
            if (keys == 'nickname') {
                return `用户${id}`  // 返回用户ID作为昵称
            }
            return '未知'
        }
        
        if (keys == 'sex') {
            var she_he = '她'
            if (lp.sex == 'male')
                she_he = '他'
            return she_he
        }
        if (keys == 'nickname') {
            var name = lp.nickname
            if (lp.card !== '')
                name = lp.card
            return name
        }

    }
    //看看你是不是在关禁闭
    async is_jinbi(e) {
        if (!e.group_id) {
            return false
        }
        let jinbi = await redis.ttl(`akasha:wife-jinbi-cd:${e.group_id}:${e.user_id}`);
        if (jinbi !== -2) {
            e.reply([
                global.segment.at(e.user_id), "\n",
                `你已经被关进禁闭室了!!!时间到了自然放你出来\n你还需要被关${jinbi / 60}分钟`
            ])
            return true
        }
        return false
    }
    //看看你会不会被干掉,key是事件名称,globaldeath是全局千分之一死亡
    async is_killed(e, keys, globaldeath) {
        if (!e.group_id) {
            return false
        }
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        var housejson = await dataManager.getUserHouse(id)
        if (!homejson[id] || !housejson[id]) {
            return false
        }
        let kill = Math.round(Math.random() * 999)
        if (kill == 6 && globaldeath) {
            e.reply([`触发千分之一的概率事件!!!,\n`,
                `很遗憾的告诉你,发生了意外,你失去了你所有的金币你的住所...失去了你的老婆...真是离谱(划掉)遗憾啊,\n`, "\n",
                `你,是否愿意重来呢?`, "\n",
                `即使,金钱,好感...一切都要重新开始吗?`, "\n",
                `做出你的选择吧!`
            ])
            homejson[id].money = 0
            homejson[id].love = 0
            homejson[id].s = ''
            housejson[id].price = 0
            housejson[id].space = 0
            housejson[id].loveup = 1
            await dataManager.saveUserHome(id, homejson[id])
            await dataManager.saveUserHouse(id, housejson[id])
            return true
        }
        if (keys == "buyhouse" && kill < 10) {
            homejson[id].money = 0
            await dataManager.saveUserHome(id, homejson[id])
            e.reply([
                `很遗憾的告诉你,\n`,
                `你被骗的苦茶子都没了`
            ])
            return true
        }
        if (keys == "getmoney") {
            if (kill < 300) {
                homejson[id].money += 100
                e.reply(`老板看你挺卖力,发了100奖金给你`)
            }
            if (kill >= 600) {
                homejson[id].money -= 50
                e.reply(`摸鱼被发现了,罚款50`)
            }
            await dataManager.saveUserHome(id, homejson[id])
        }
        return false
    }
    //判断好感度是否双方都小于等于0,是则拆散,单向老婆则只失去老婆
    async is_fw(e, homejson) {
        if (!e.group_id) {
            return false
        }
        var id = e.user_id
        
        // 使用传入的homejson参数，而不是重新获取数据
        if (!homejson || !homejson[id]) {
            return false
        }
       
        if (homejson[id].love <= 0) {
            e.reply(`很遗憾,由于你老婆对你的好感太低,你老婆甩了你`)
            homejson[id].love = 0
            homejson[id].s = ''
            await this.dataManager.saveUserHome(id, homejson[id])
            return true;
        }
        return false;
    }
    //判断行为次数是否上限
    async is_MAXEX(e, keys) {
        if (!e.group_id) {
            return false
        }
        var id = e.user_id
        var filename = e.group_id + `.json`
        var placejson = await dataManager.getUserPlace(id)
        if (!placejson[e.user_id]) {
            return false
        }
        if (placejson[e.user_id].placetime >= gifttime && keys == 'gift') {
            e.reply(`单次逛街行动上限,你回了家`)
            if (!placejson[id]) {
                placejson[id] = { place: "home", placetime: 0 };
            }
            placejson[id].place = "home"
            placejson[id].placetime = 0
            await dataManager.saveUserPlace(id, placejson[id])
            return true
        }
        else return false;
    }
    //抢老婆决斗
    async duel(e) {
        console.log("用户命令：", e.msg);
        let user_id = e.user_id;
        let user_id2 = e.at; //获取当前at的那个人
        var battlejson = await dataManager.getUserBattle(user_id)
        var battlejson = await dataManager.getUserBattle(user_id2)
        let level = battlejson[user_id].level
        let level2 = battlejson[user_id2].level
        let user_id2_nickname = null
        for (let msg of e.message) { //赋值给user_id2_nickname
            if (msg.type === 'at') {
                user_id2_nickname = msg.text//获取at的那个人的昵称
                break;
            }
        }
        if (!level)
            level = 0
        if (!level2)
            level2 = 0
        let filename1 = `${user_id}.json`;
        let filename2 = `${user_id2}.json`;
        let num13 = 0
        let num14 = 0
        let num15 = 0
        let num23 = 0
        let num24 = 0
        let num25 = 0
        if (fs.existsSync(dirpath2 + "/" + filename1)) {
            var json1 = await dataManager.loadJsonData(dirpath2 + "/" + filename1);
            if (json1.hasOwnProperty(3))
                num13 = Object.keys(json1[3]).length
            if (json1.hasOwnProperty(4))
                num14 = Object.keys(json1[4]).length
            if (json1.hasOwnProperty(5))
                num15 = Object.keys(json1[5]).length
        }
        if (fs.existsSync(dirpath2 + "/" + filename2)) {
            var json2 = await dataManager.loadJsonData(dirpath2 + "/" + filename2);
            if (json2.hasOwnProperty(3))
                num23 = Object.keys(json2[3]).length
            if (json2.hasOwnProperty(4))
                num24 = Object.keys(json2[4]).length
            if (json2.hasOwnProperty(5))
                num25 = Object.keys(json2[5]).length
        }
        //读取文件
        var win_level = level - level2
        let win = 50 + Magnification * win_level + num13 + num14 * 2 + num15 * 3 - num23 - num24 * 2 - num25 * 3
        let random = Math.random() * 100//禁言随机数
        //提示
        e.reply([global.segment.at(e.user_id),
        `你的境界为${battlejson[user_id].levelname}\n${user_id2_nickname}的境界为${battlejson[user_id2].levelname}\n决斗开始!战斗力意义系数${Magnification},境界差${win_level},你的获胜概率是${win}`]);//发送消息
        //判断
        let is_win = false
        if (win > random) {//判断是否成功
            is_win = true
        }
        return is_win;
    }
    


    async delerrdata(e) {
        if (!e.group_id) {
            e.reply("该功能仅支持群聊使用")
            return
        }
        var id = e.user_id
        var filename = e.group_id + `.json`
        var homejson = await dataManager.getUserHome(id)
        let wifearr = []//所有人的的老婆
        //找出所有人的老婆,转为String型
        for (let data of Object.keys(homejson)) {
            if (await homejson[data].s !== 0 && homejson[data].s !== undefined && homejson[data].s !== null && homejson[data].s !== '')
                wifearr.push(String(homejson[data].s))
        }
        console.log(`所有人的老婆`, wifearr)
        let memberMap = await e.group.getMemberMap();
        let arrMember = []
        for (let aaa of memberMap) {
            arrMember.push(String(aaa[1].user_id))
        }
        console.log(`群成员`, arrMember)
        //找出不在群的老婆
        let deadwife = wifearr.filter(item => !arrMember.includes(item))
        console.log(`不在的老婆`, deadwife)
        //找出这些已退群的老婆的拥有者
        let widedeadid = Object.keys(homejson).filter(item => deadwife.includes(String(homejson[item].s)))
        console.log(`这些老婆的拥有者`, widedeadid)
        //找出不在群的用户
        let deadid = Object.keys(homejson).filter(item => !arrMember.includes(item))
        console.log(`不在群的用户`, deadid)
        let chick = 0
        //把老婆跑了的用户老婆删除
        for (let shit of widedeadid) {
            homejson[shit].s = 0
            chick++
        }
        //删掉不在群的用户
        let ikun = 0
        for (let errid of deadid) {
            delete (homejson[errid])
            ikun++
        }
        await dataManager.saveUserHome(id, homejson[id])
        e.reply(`清除本群无效/错误存档成功,\n本次共错误退群存档${ikun}个,\n删除错误的老婆${chick}位`)
        return true
    }

}

// 动态添加位置移动规则
if (typeof qqy !== 'undefined') {
    qqy.prototype.constructor.prototype.rule = qqy.prototype.constructor.prototype.rule || []
    qqy.prototype.constructor.prototype.rule.push(
        
    )
}

    

export default qqy
//# sourceMappingURL=getwife.map