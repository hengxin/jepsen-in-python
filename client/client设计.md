# client
## client作用
* 持有ssh连接
* 持有数据库连接
* 进行数据库相关操作
## client持有属性
* hostname(服务器ip)
* port(ssh端口号)  
* username(登录服务器username)
* passwd(登录服务器passwd)
* ssh_connection(对服务器的连接)
* db_connection(对数据库的连接)
## client持有函数
* 用于初始化数据库的函数
* 用于获取数据库连接的函数  
* 用户销毁、清理数据库的函数  
* 用户读、写、修改数据库数据的函数
## client职责
* 初始化ssh连接
* 初始化数据库
* 初始化数据库连接
* 执行对数据库的相关操作(读、写、修改)
## client产生
* 主程序读取配置文件
  
  形如:
  
  n1:
  
    ip: xx.xx.xx.xx
  
    username:root
  
    passwd:passwd
  
  n2:
    
    ...
* 根据节点数量初始化不同数量的client对象,每个client对象分别持有各个节点的ip等信息
* client构造函数中调用init_ssh来获得ssh连接
* client构造函数中调用初始化数据库的函数init_db,通过ssh连接来进行数据库的初始化
* client构造函数中调用连接数据库函数connect_db获得数据库连接db_connection
* client构造完成
* 后续client对象由generator持有并调用client的读、写、修改方法等函数对数据库进行操作并返回结果进行记录