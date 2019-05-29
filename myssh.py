import paramiko
from day06 import getip
import threading  # 多线程，多任务用以提高效率
import time
import os


class ssh_link(object):

    # windows向linux推送公钥
    def sendkeys(self, ip, port, user, passwd, publicfile):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        try:
            ssh.connect(hostname=ip, port=port, username=user, password=passwd)
        except Exception:
            print("连接失败!")
        stdin, stdout, stderr = ssh.exec_command("cd .ssh")
        if stderr.read() != "":
            ssh.exec_command("mkdir .ssh;chmod 700 .ssh")

            trans = paramiko.Transport((ip, int(port)))
            trans.connect(username=user, password=passwd)
            sftp = paramiko.SFTPClient.from_transport(trans)
            if user == "root":
                sftp.put("{}".format(publicfile), "/root/.ssh/authorized_keys")
                print("推送公钥成功!")
            else:
                sftp.put("{}".format(publicfile), "/home/{}/.ssh/authorized_keys".format(user))
                stdin, stdout, stderr = ssh.exec_command("chmod 644 /home/{}/.ssh/authorized_keys".format(user))
                if stderr.read() != "":
                    print("推送公钥失败!")
                else:
                    print("公钥推送成功!")
            trans.close()
        else:
            stdin, stdout, stderr = ssh.exec_command("cat .ssh/authorized_keys")
            if stderr.read() != "":
                trans = paramiko.Transport((ip, port))
                trans.connect(username=user, password=passwd)
                sftp = paramiko.SFTPClient.from_transport(trans)
                if user == "root":
                    sftp.put("{}".format(publicfile), "/root/.ssh/authorized_keys")
                    print("推送公钥成功!")
                else:
                    sftp.put("{}".format(publicfile), "/home/{}/.ssh/authorized_keys".format(user))
                    stdin, stdout, stderr = ssh.exec_command("chmod 644 /home/{}/.ssh/authorized_keys".format(user))
                    if stderr.read() != "":
                        print("推送公钥失败!")
                    else:
                        print("公钥推送成功!")
                trans.close()
            else:
                f = open("{}".format(publicfile))
                lines = ""
                for i in f:
                    lines += i
                f.close()
                if user == "root":
                    stdin, stdout, stderr = ssh.exec_command("{} >> /root/.ssh/authorized_keys".format(lines))
                    if stderr.read() != "":
                        print("推送公钥失败!")
                    else:
                        print("公钥推送成功!")
                else:
                    stdin, stdout, stderr = ssh.exec_command("{} >> /home/{}/.ssh/authorized_keys".format(lines, user))
                    if stderr.read() != "":
                        print("推送公钥失败!")
                    else:
                        print("公钥推送成功!")

        ssh.close()

    # linux执行命令
    def exec_cmd(self, ip, port, command, privatefile):
        ssh = paramiko.SSHClient()
        private_key = paramiko.RSAKey.from_private_key_file(privatefile)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        try:
            ssh.connect(hostname=ip, port=port, username="root", pkey=private_key, timeout=2)
            stdin, stdout, stderr = ssh.exec_command(command)
            console_out = stdout.read()
            console_error = stderr.read()
            print("主机IP:{}".format(ip))
            print(console_out.decode())
            print(console_error.decode())
            ssh.close()
        except TimeoutError:
            print("主机IP:{}".format(ip))
            print("连接失败,可能由于对方主机不存在，或者网络不通")
            ssh.close()
        except Exception:
            print("主机IP:{}".format(ip))
            print("连接失败")
            ssh.close()

    # 读取文件,建立连接，执行命令
    def auto_ssh(self):
        while True:
            print("""***********请选择操作:***********
1.从文件读取ip端口
2.从数据库中读取ip端口
3.把文件ip端口存到数据库
4.推送公钥
5.退出
*********************************************************""")
            option = input("请输入操作(1/2/3/4):")
            if option == "1":
                filepath = input("请输入文件的路径:")
                absname = filepath.replace("\\", "/")
                while not os.path.isfile(absname):
                    filepath = input("请输入文件的路径:")
                    absname = filepath.replace("\\", "/")
                privatefile = input("请输入私钥路径:")
                absname2 = privatefile.replace("\\", "/")
                while not os.path.isfile(absname2):
                    privatefile = input("请输入私钥路径:")
                    absname2 = privatefile.replace("\\", "/")
                type = input("请输入你要操作的主机类型(webservers):")
                ip_ports = getip.getipsandports(filepath, type)
                while len(ip_ports) == 0:
                    print("主机类型名称错误!")
                    type = input("请输入你要操作的主机类型(webservers):")
                ip_ports = getip.getipsandports(filepath, type)
                cmd = input("请输入你要执行的命令:")

                for i in ip_ports:
                    a = threading.Thread(target=self.exec_cmd, args=(i.get("ip"), i.get("port"), cmd, absname2))
                    a.start()
                    time.sleep(1)
                time.sleep(5)
            elif option == "2":
                ip = input("请输入mysql数据库的主机IP:")
                port = input("请输入mysql数据库的端口:")
                user = input("请输入mysql数据库的用户名:")
                passwd = input("请输入mysql数据库的密码:")
                dbname = input("请输入数据库名:")
                keyword = input("请输入你要操作的主机类型(webservers):")
                ip_ports = getip.gethosts(keyword, user, passwd, ip, port, dbname)
                while ip_ports is None:
                    ip = input("请输入mysql数据库的主机IP:")
                    port = input("请输入mysql数据库的端口:")
                    user = input("请输入mysql数据库的用户名:")
                    passwd = input("请输入mysql数据库的密码:")
                    dbname = input("请输入数据库名:")
                    keyword = input("请输入你要操作的主机类型(webservers):")
                    ip_ports = getip.gethosts(keyword, user, passwd, ip, port, dbname)
                while len(ip_ports) == 0:
                    print("主机类型名称错误!")
                    keyword = input("请输入你要操作的主机类型(webservers):")
                    ip_ports = getip.gethosts(keyword, user, passwd, ip, port, dbname)
                privatefile = input("请输入私钥路径:")
                absname2 = privatefile.replace("\\", "/")
                while not os.path.isfile(absname2):
                    privatefile = input("请输入私钥路径:")
                    absname2 = privatefile.replace("\\", "/")
                cmd = input("请输入你要执行的命令:")

                for i in ip_ports:
                    a = threading.Thread(target=self.exec_cmd, args=(i.get("ip"), i.get("port"), cmd, absname2))
                    a.start()
                    time.sleep(1)
                time.sleep(5)
            elif option == "3":
                filepath = input("请输入文件的路径:")
                absname = filepath.replace("\\", "/")
                while not os.path.isfile(absname):
                    filepath = input("请输入文件的路径:")
                    absname = filepath.replace("\\", "/")
                ip = input("请输入mysql数据库的主机IP:")
                port = input("请输入mysql数据库的端口:")
                user = input("请输入mysql数据库的用户名:")
                passwd = input("请输入mysql数据库的密码:")
                dbname = input("请输入数据库名:")
                result = getip.putintodb(absname, user, passwd, ip, port, dbname)
                while result is None:
                    ip = input("请输入mysql数据库的主机IP:")
                    port = input("请输入mysql数据库的端口:")
                    user = input("请输入mysql数据库的用户名:")
                    passwd = input("请输入mysql数据库的密码:")
                    dbname = input("请输入数据库名:")
                    result = getip.putintodb(absname, user, passwd, ip, port, dbname)
                print(result)
                time.sleep(5)
            elif option == "4":
                ip = input("请输入你要推送公钥的ip:")
                port = input("请输入端口port:")
                passwd = input("请输入root密码:")
                publicfile = input("请输入你的公钥路径,以便推送公钥到{}:".format(ip))
                self.sendkeys(ip, port, "root", passwd, publicfile)
            elif option == "5":
                break
            else:
                print("请输入正确的操作项（eg:1,2,3,4,5）")


openssh = ssh_link()
openssh.auto_ssh()
