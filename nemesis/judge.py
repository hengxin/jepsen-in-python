# -*- coding: utf-8 -*-
# @Time    : 2022/3/10 15:27
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : judge.py.py


# 返回一个闭包
import math
import random


def other_nodes(lists, nth):
    result = []
    for i in range(0, len(lists)):
        if i != nth:
            for j in lists[i]:
                result.append(j)
    return result


def complete_grudge(lists: list):
    result = {}
    for i in range(0, len(lists)):
        for j in lists[i]:
            result[j] = other_nodes(lists, i)
    return result



def shuffle(list_a: list):
    result = []
    while len(list_a) > 0:
        i = random.randint(0, len(list_a)-1)
        result.append(list_a[i])
        list_a.remove(list_a[i])
    return result


# one: 随机选到1 返回{1:{2,3,4,5},
#                        2:{1},
#                        3:{1},
#                        4:{1},
#                        5:{1}}
def one(clients: list):
    i = random.randint(0, len(clients)-1)
    list_a = [clients[i]]
    list_b = clients
    list_b.remove(clients[i])
    return complete_grudge([list_a, list_b])


# majority: 先进行随机打乱,假设结果为[2 5 3 4 1],则返回
#                    {2:{3,4,1},
#                     5:{3,4,1},
#                     3:{2,5},
#                     4:{2,5},
#                     1:{2,5}}
def majority(clients: list):
    half = math.floor(len(clients)/2)
    shuffled_clients = shuffle(clients)
    return complete_grudge([shuffled_clients[0:half], shuffled_clients[half:]])



# majorities-ring:固定算法，互为首领 以[1 2 3 4 5]为例子则有结果(5个节点结果是确定的)
#                     {2:{4,5},
#                      1:{4,3},
#                      5:{3,2},
#                      4:{1,2},
#                      3:{1,5}}
# 以[1 2 3 4 5 6 7]为例子则有结果(多于5个则不确定)，暂不举例
def majorities_ring(clients):
    pass


# minority-third:与majority类似，但是取1/3 向下取整
def minority_third(clients):
    third = math.floor(len(clients) / 3)
    shuffled_clients = shuffle(clients)
    return complete_grudge([shuffled_clients[0:third], shuffled_clients[third:]])
    pass


# primaries:所有节点与其他分别分割 结果为{1:{2,3,4,5},
#                                     2:{1,3,4,5},
#                                     3:{1,2,4,5},
#                                     4:{1,2,3,5},
#                                     5:{1,2,3,4}
def primaries(clients):
    client_list = []
    for i in clients:
        client_list.append([i])
    return complete_grudge(client_list)
    pass


if __name__ =="__main__":
    print(majority([1,2,3,4,5]))
    print(one([1,2,3,4,5]))
    print(minority_third([1, 2, 3, 4, 5]))
    print(primaries([1,2,3,4,5]))