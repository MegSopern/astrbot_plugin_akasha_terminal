import json
import os
import random

class lottery():
    def __init__(self):
        pass

    def lottery(timies:int):

        try:
            with open("./core/weapon.json","r") as file:    
                print("文件打开成功")
        except:
            print("文件打开失败!")
        
        i = int(1)      #默认抽奖次数

        prize = []      #存储区间

        while i <= timies:
            a = random.randint(1,312)
            prize.append(a)
            i += 1

        a = int(0)
        #通过权重进行抽奖,判断数字落到哪个区间
        for a in (1,len(prize)):
            #五星
            if prize[a] >= 1 and prize[a] <= 31:
                q = random.randint(500,531)
                print(f"你获得了{file['q']['name']}")
                a+=1
            #四星
            elif prize[a] > 31 and prize <=91:
                q = random.randint(400,430)
                print(f"你获得了{file['q']['name']}")
                a+=1
            #三星
            elif prize[a] >91 and prize[a] <=312:
                q = random.randint(300,313)               
                print(f"你获得了{file['q']['name']}")

            else: print("抽nm'的奖")