# nemesis设计
## nemesis持有的对象
* 各个节点的ssh链接
* nemesis的mode
* nemesis的相关配置
## nemesis持有的方法
  Mandatory options:

    :db         The database you'd like to act on

  Optional options:

    :interval   The interval between operations, in seconds.
    :faults     A collection of enabled faults, e.g. [:partition, :kill, ...]
    :partition  Controls network partitions
    :kill       Controls process kills
    :pause      Controls process pauses and restarts

  Possible faults:

    :partition
    :kill
    :pause
    :clock

  Partition options:

    :targets    A collection of partition specs, e.g. [:majorities-ring, ...]

  Kill and Pause options:

    :targets    A collection of node specs, e.g. [:one, :all]"
## 网络分割算法  Partition
 此算法得出的结果对网络进行分区以引入错误
 算法类型:

    :one 随机选一个            
    :majority 选一半，优先选取少的那一半，即一个队列的前一半
    :majorities-ring 
    :minority-third   
    :primaries

    举例:
    节点为: [1 2 3 4 5]
    one: 随机选到1 返回{1:{2,3,4,5},
                       2:{1},
                       3:{1},
                       4:{1},
                       5:{1}}
    majority: 先进行随机打乱,假设结果为[2 5 3 4 1],则返回
                       {2:{3,4,1},
                        5:{3,4,1},
                        3:{2,5},
                        4:{2,5},
                        1:{2,5}}
    majorities-ring:固定算法，互为首领 以[1 2 3 4 5]为例子则有结果(5个节点结果是确定的)
                        {2:{4,5},
                        1:{4,3},
                        5:{3,2},
                        4:{1,2},
                        3:{1,5}}
                        以[1 2 3 4 5 6 7]为例子则有结果(多于5个则不确定)，暂不举例
    minority-third:与majority类似，但是取1/3 向下取整
    primaries:所有节点与其他分别分割 结果为{1:{2,3,4,5},
                                        2:{1,3,4,5},
                                        3:{1,2,4,5},
                                        4:{1,2,3,5},
                                        5:{1,2,3,4}
                        
## 杀死/暂停进程 kill/pause
 直接对db进行操作 给点节点(一个列表对象，单个或多个节点)

## 调整时钟 clock
 调整所有节点的时钟，退出后恢复
 
## 分割模块
* 网络关闭方法
* 选举算法
* 数据库管理方法
* 时间调整方法