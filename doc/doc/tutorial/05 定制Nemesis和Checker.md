# 定制Nemesis和Checker
在运行过程中，可以为你的分布式系统注入各种错误以及定义如何检查结果
本项目通过配置文件的方式来控制Nemesis和Checker的特征
```yaml
nemesis:
  # mode -- partition, clock, pause, kill, None
  mode: "None" # Nemesis的类型
  # when mode is partition, partition_method must be set
  # partition_method:
  #   one: randomly select one of the nodes
  #   majority: select the first floor half of the nodes
  #   majorities_ring: select some groups by a great algorithm
  #   minority-third: select the first one-third floor of the nodes
  #   primaries: separate all nodes with each other
  # partition_method: "majorities_ring" # 为partition模式的Nemesis指定一个用于分区的算法
  # when mode is clock. step nust be set
  # It`s the time of the step the clock will be changed and the unit is seconds
  #step: 60 # 为clock模式函数指定修改服务器的时间

checker:
  # models -- cas-register, mutex, register
  models: "cas-register" # 指定检查操作历史的checker类型
  # algos -- competition, wgl, linear
  algos: "competition" # 指定检查操作历史的checker算法
```