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


def invert_grudge(client: list, result: dict):
    invert_result = {}
    for key in result.keys():
        j = []
        for i in client:
            if i not in result[key]:
                j.append(i)
        invert_result[key] = j
    return invert_result


def shuffle(a_list: list):
    result = []
    list_a = a_list.copy()
    while len(list_a) > 0:
        i = random.randint(0, len(list_a) - 1)
        result.append(list_a[i])
        list_a.remove(list_a[i])
    return result


def get_dns(degree: dict):
    degree_list = []
    for key in degree.keys():
        for i in shuffle(degree[key]):
            degree_list.append([key, i])
    return degree_list


# one: 随机选到1 返回{1:{2,3,4,5},
#                        2:{1},
#                        3:{1},
#                        4:{1},
#                        5:{1}}
def one(clients: list):
    i = random.randint(0, len(clients) - 1)
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
    half = math.floor(len(clients) / 2)
    shuffled_clients = shuffle(clients)
    return complete_grudge([shuffled_clients[0:half], shuffled_clients[half:]])


# majorities-ring:固定算法，互为首领 以[1 2 3 4 5]为例子则可能有结果
#                     {2:{4,5},
#                      1:{4,3},
#                      5:{3,2},
#                      4:{1,2},
#                      3:{1,5}}

def majorities_ring_perfect(clients):
    length = len(clients)
    step = math.floor(length / 2)
    shuffled_clients = shuffle(clients)
    result = {}
    for i in range(0, length):
        result[shuffled_clients[i]] = [shuffled_clients[(i + step - length if (i + step >= length) else i + step)]]
    for i in result.keys():
        result[result[i][0]].append(i)
    return result


# 以[1 2 3 4 5 6]为例
# 将每个节点分为一个组
# {1},{2},{3},{4},{5},{6}
# 将每个组的（度，首领）对进行随机排序
# [1,6] [1,2] [1,3] [1,4] [1,5], [1 1]
# 挑选第一个组作为a 再在之后中挑选顺序最靠前的可以连接的组b进行连接
# 可以连接的组b指b的组中不包含a
# 知道a的度>=n/2+1 此例中为4
# 以[1 2 3 4 5 6 7]为例子则可能有结果:
#                      {1:{6,3,2}, 1{2,7}
#                       2:{7,5,1}, 2{1,3}
#                       3:{1,4,5}, 3{4,2}
#                       4:{6,3},   4{3,5}
#                       5:{7,3,2}, 5{6,3}
#                       6:{7,1,4}, 6{5,7}
#                       7:{6,2,5}} 7{1,6}
# 以[1 2 3 4 5 6 7 8]:
#                      {1:{2,5,8}, 1{2, 8, 3}
#                       2:{7,1,3}, 2{1, 3, 4}
#                       3:{7,6,2}, 3{2, 4, 1}
#                       4:{6,5,8}, 4{3, 5, 2}
#                       5:{7,1,4}, 5{4, 6, 7}
#                       6:{4,3,8}, 6{5, 7, 8}
#                       7:{3,2,5}, 7{6, 8, 5}
#                       8:{4,1,6}} 8{7, 1, 6}
def majorities_ring_stochastic(clients):
    result = {}
    for i in range(1, len(clients) + 1):
        result[i] = [clients[i - 1]]
    degree = {1: clients.copy()}
    for i in range(2, len(clients)):
        degree[i] = []
    while True:
        dns = get_dns(degree)
        a = dns[0]
        if a[0] >= math.floor(len(clients) / 2) + 1:
            break
        b = None
        for i in range(1, len(dns)):
            if result[dns[i][1]].count(a[1]) == 0:
                b = dns[i]
                break
        if not b:
            break
        result[a[1]].append(b[1])
        result[b[1]].append(a[1])
        degree[a[0]].remove(a[1])
        degree[a[0] + 1].append(a[1])
        degree[b[0]].remove(b[1])
        degree[b[0] + 1].append(b[1])
    return invert_grudge(clients, result)


def majorities_ring(clients):
    if len(clients) <= 5:
        return majorities_ring_perfect(clients)
    else:
        return majorities_ring_stochastic(clients)


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


if __name__ == "__main__":
    # print(majority([1, 2, 3, 4, 5]))
    # print(one([1, 2, 3, 4, 5]))
    # print(minority_third([1, 2, 3, 4, 5]))
    # print(primaries([1, 2, 3, 4, 5]))
    print(majorities_ring([1, 2, 3, 4, 5]))
