import re
from sqlalchemy import create_engine, MetaData, Column, String, INTEGER
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base

# 创建对象的基类:
Base = automap_base()


# 用于建表以及生成模型对象，保存到数据表中
class Servers(Base):
    # 表的名字:
    __tablename__ = 'servers_ip_port'
    # 表的结构:
    id = Column(INTEGER, primary_key=True)
    ip = Column(String(15))
    port = Column(INTEGER)
    gname = Column(String(20))


# 创建连接
def create_link(user, passwd, ip, port, dbname):
    engine = create_engine("mysql+pymysql://{}:{}@{}:{}/{}".format(user, passwd, ip, port, dbname))
    return engine


# 获取session
def getDBSession(engine):
    DBSession = sessionmaker(bind=engine)
    return DBSession()


# 从文件读取ip和端口
def getipsandports(path, keyword):
    f = open(path, mode="r")
    # 用来保存类似[webservers]的行在文件中的下标
    arr = []
    # 用来保存类似'[webservers]'的key
    keys = []
    # 用来保存所有的ip地址
    values = []
    # 用来保存类似{'[webservers]':[10.1.1.1,10.1.1.2,...],'[....]':[.....]}
    nameandip = {}

    for index, item in enumerate(f):
        if re.findall("^\[", item):
            keys.append(item.strip())
            nameandip[item.strip()] = []
            arr.append(index)
    f.seek(0)
    for index, item in enumerate(f):
        for i, o in enumerate(arr):
            """
                用来判断前[]到下一个[]之间的ip地址存到nameandip，作为前[]的值
                用以构建{'[webservers]':[{"ip:"10.1.1.1",port:"22"},
                {"ip:"10.1.1.2",port:"33"},...],'[....]':[.....]}
           """
            if i < len(arr) - 1:
                index1 = i + 1
                if index > o and index < arr[index1] and item.strip() != "":
                    nameandip[keys[i]].append({"ip": item.strip().split(":")[0],
                                               "port": item.strip().split(":")[1]})
                    values.append({"ip": item.strip().split(":")[0],
                                   "port": item.strip().split(":")[1]})
            else:
                if index > o and item.strip() != "":
                    nameandip[keys[i]].append({"ip": item.strip().split(":")[0],
                                               "port": item.strip().split(":")[1]})
                    values.append({"ip": item.strip().split(":")[0],
                                   "port": item.strip().split(":")[1]})
    f.close()
    """
        如果没有输入关键字，默认返回所有的ip值，
        否则判断是否输对关键字，输对返回对应组的值，否则返回空列表
    """
    if keyword != "":
        if "[{}]".format(keyword) in nameandip.keys():
            return nameandip["[{}]".format(keyword)]
        else:
            return []
    else:
        return values


# 读取文件内容并加入数据库中
def putintodb(path, user, passwd, ip, port, dbname):
    hostip = ip
    engine = create_link(user, passwd, ip, port, dbname)
    # 判断库中是否存在servers_ip_port表，存在，直接往表里插数据,不存在根据 类Servers 去生成表
    try:
        metadata = MetaData(engine)
        Base.prepare(engine, reflect=True)
        if 'servers_ip_port' not in Base.classes.keys():
            Base.metadata.create_all(engine)
        session = getDBSession(engine)
    except Exception:
        print("数据库连接失败")
        return None
    f = open(path, mode="r")
    arr = []
    keys = []
    serverlist = []
    # 查询表内所有的ip端口信息,用以剔除文件中和表内相同的ip端口信息
    serverObj = session.query(Servers).all()

    if len(serverObj) > 0:
        for server in serverObj:
            s = Servers(ip=server.ip, port=server.port, gname=server.gname)
            serverlist.append(s)
    for index, item in enumerate(f):
        if re.findall("^\[", item):
            keys.append(item.strip()[1:len(item.strip()) - 1])
            arr.append(index)
    f.seek(0)
    for index, item in enumerate(f):
        for i, o in enumerate(arr):
            """
                用来判断前[]到下一个[]之间的ip地址存到nameandip，作为前[]的值
                用以构建{'[webservers]':[{"ip:"10.1.1.1",port:"22"},
                {"ip:"10.1.1.2",port:"33"},...],'[....]':[.....]}
           """
            if i < len(arr) - 1:
                index1 = i + 1
                if index > o and index < arr[index1] and item.strip() != "":
                    ip = item.strip().split(":")[0];
                    port = int(item.strip().split(":")[1]);
                    isExist = False
                    for k in serverlist:
                        if k.ip == ip and k.port == port and k.gname == keys[i]:
                            isExist = True
                    if isExist == False:
                        server = Servers(ip=ip, port=port, gname=keys[i])
                        # 添加到session:
                        session.add(server)
                        # 提交即保存到数据库:
                        session.commit()
            else:
                if index > o and item.strip() != "":
                    ip = item.strip().split(":")[0];
                    port = int(item.strip().split(":")[1]);
                    isExist = False
                    for k in serverlist:
                        if k.ip == ip and k.port == port and k.gname == keys[i]:
                            isExist = True
                    if isExist == False:
                        server = Servers(ip=ip, port=port, gname=keys[i])
                        # 添加到session:
                        session.add(server)
                        # 提交即保存到数据库:
                        session.commit()

    f.close()
    session.close()
    return '已保存至{}的{}库servers_ip_port表中'.format(hostip, dbname)


# 获取主机ip和端口
def gethosts(keyword, user, passwd, ip, port, dbname):
    engine = create_link(user, passwd, ip, port, dbname)
    Base.prepare(engine, reflect=True)
    session = getDBSession(engine)
    try:
        if keyword == '':
            serverObj = session.query(Servers).all()
        else:
            serverObj = session.query(Servers).filter(Servers.gname == '{}'.format(keyword)).all()
        serverlist = []
        for server in serverObj:
            serverlist.append({"ip": server.ip, "port": server.port})
        session.close()
        return serverlist
    except Exception:
        print("数据库连接失败")
        return None
    session.close()
