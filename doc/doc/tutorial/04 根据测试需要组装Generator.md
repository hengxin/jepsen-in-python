# 04 根据测试需要配置组装Generator

### 写在前面

------

Generator模块是Jepsen五大模块之一，主要职责为生成对数据库的操作operations（读、写、比较并交换等，以下简称**op**）交予：

1. Client模块对应的DB节点执行
2. Nemesis模块执行（即向分布式系统注入破坏性操作，例如杀死数据节点，制造网络分区）

两种情况下，Generator模块都会记录对应模块返回的执行结果，生成历史日志供Checker模块进行检验。

它可以说算是Jepsen框架的一大特色，通过其内置的几十种Generator的组合包装，测试者可以达成较高水平的对op生成规则的控制，如并发数限制、时间限制、生成间隔、同步等等，以覆盖丰富的测试场景。

接下来，教程将对常用的一些Generator作一个简单介绍（详细信息可以查看generator.py源码注释），并在最后将给出一个组装使用Generator的参考例子。

### 什么是一个generator

------

一个generator具备两个基本的方法，它们都是函数式的：

```python
    def update(gen, test: dict, context: dict, event):
        """
        :param gen: 一个generator对象
        :param test: 传入的本次测试配置（来自config.yaml）
        :param context: 测试运行时的上下文，包括当前空闲线程、时间等信息
        :param event: 事件，通常是一个op
        :return: gen2: 通过该次调用传入的generator的状态得到了更新，返回更新后的generator
        """

    def op(gen, test: dict, context: dict):
        """
        :param gen: 一个generator对象
        :param test: 传入的本次测试配置（来自config.yaml）
        :param context: 测试运行时的上下文，包括当前空闲线程、时间等信息
        :return: None: 该generator的生命已经结束，无法再扔出op
                 或者
                [op, gen2]: 所生成的op以及新状态的generator
        """
```

除了在generator.py源码中显式继承自Generator抽象类的子类外，部分python基本数据类型也算作一个generator：

- **字面量 None：**op方法、update方法均返回None。
- **字典 dict：**调用op方法返回自身*（注：会补充一些运行时字段）*；忽略update方法。（在这种情况下，generator就是一个op）
- **函数 function：**该函数（记为**f**）需要接收0或2个参数，若**f()**或**f(test, context)**的调用结果（记为res）不为None，则再次调用并返回op([res, gen], test, context)，否则返回None；忽略update方法。
- **列表 list：**该列表调用op方法，列表中第一个generator调用op方法，若结果不为None，返回生成的op、新状态的generator、列表中剩下的generator所组成的列表，否则摒弃掉该元素则再次调用并返回op(gen[1:], test, context)；update方法仅更新list中第一个元素，返回该列表。



### 常用的generator简介

#### Mix

```python
gen.mix(gens: list)
```

接收一个generator列表，将其包装为一个更大的generator，op将随机从这些generator中扔出。



#### Any

```
gen.any(*args)
```

接收若干个generator，将其包装为一个更大的generator，op可从里面任意一个抛出（更准确地说，每次抛出时间 'soonest' 的那个）。



#### Nemesis

```python
gen.nemesis(nemesis_gen, client_gen=None)
```

若nemesis_gen参数为None，则视为不开启nemesis；client_gen为None时op将全扔给nemesis；否则将返回它们两通过gen.any组合的结果。



#### Limit

```python
gen.limit(times: int, gen)
```

通过times参数限制所传入generator允许生成op的次数上限（超过则op调用返回None），若传入的整数为负数，上限为|MIN_INT - times|次。(MIN_INT = -sys.maxint - 1)



#### Sleep

```
gen.sleep(dt)
```

顾名思义，这是一个特殊的op，使接收到它的线程睡眠dt**秒**。



#### Log

```python
gen.log(msg)
```

日志类型的op，用于打印自定义的信息（如阶段开始结束时的信息）。



#### Cycle

```python
gen.cycle(gen, times=-1)
```

通过times参数设定generator可供循环使用的次数（从能正常扔出op到返回None为止视为一次循环），若传入的整数为负数，次数为|MIN_INT - times|。(MIN_INT = -sys.maxint - 1)



#### TimeLimit

```
gen.time_limit(dt, gen)
```

通过dt参数设定generator在多少**秒**内可以生成op（从generator启动开始，超时则op调用返回None）。



#### Stagger

```
gen.stagger(dt, gen)
```

通过dt参数设定generator以大致（不精确的，每次从 0 ~ 2*dt 间隔浮动）dt**秒**为周期生成op（亦即op间的延迟大致为dt秒）。



#### Delay

```
gen.delay(dt, gen)
```

通过dt参数设定generator以较为精确的dt秒为周期生成op。



#### Synchronize

```
gen.synchronize(gen)
```

包装一个generator，等待直到所有worker都空闲时才能抛出op（取消并行，每次有且仅有一个worker从该generator中接收op）。



#### Phases

```
gen.phases(*gens)
```

接收若干个generator，返回一个均synchronize化的generator列表直到前一个generator无法抛出op或pending后才接着处理下一个generator。



#### FlipFlop

```
gen.flip_flop(a, b)
```

接收两个generator：a和b， 二者交替抛出op（a->b->a->b...），直到其中一个generator生命结束（即返回None）。



### 如何组装

在Pyjepsen.py中，通过以下方式来组装你的generator

```python
Pipeline([
	gen.gen1_,
	partial(gen.gen2_(args2)),
	partial(gen.gen3_(args3)),
])(args1)
```

*（使用第三方库fastcore.transfrom.Pipeline来实现类似于clojure **->>** 关键字的函数管道式调用效果，否则组装将 ”嵌套地狱 ”）*

以下是一个实际例子：

```python
generator = Pipeline([
    gen.mix,
    partial(gen.stagger, 1),
    partial(gen.nemesis, gen.cycle([
        gen.sleep(5),
        {"type": "info", "f": "start"},
        gen.sleep(5),
        {"type": "info", "f": "stop"}
    ])),
    partial(gen.time_limit, 30)
])([read, write, cas])

# 其中read, write, cas为用户定义的针对数据库的读写CAS操作函数
```

它的效果同：

```python
generator = \
	gen.time_limit(30,
               gen.nemesis(gen.cycle([
                   gen.sleep(5),
                   {"type": "info", "f": "start"},
                   gen.sleep(5),
                   {"type": "info", "f": "stop"}
               ]),
                           gen.stagger(1,
                                       gen.mix([read, write, cas]))))
```

前者代码更加清晰美观，便于维护。

