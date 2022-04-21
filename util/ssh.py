# -*- coding: utf-8 -*-
# @Time    : 2022/3/6 23:26
# @Author  : jiangnanweishao999
# @Email   : 2764065464@qq.com
# @File    : ssh.py.py
import logging
import paramiko


def join_parameter(opts: dict):
    s = ""
    for k in opts.keys():
        s += "{} {} ".format(k, opts[k])
    return s


class ssh_client:
    def __init__(self, hostname, port, username, password):
        self.ssh_connection = paramiko.SSHClient()
        self.ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_connection.connect(hostname=hostname,
                                    port=port,
                                    username=username,
                                    password=password)
        self.root_path = self.pwd()
        self.mkdir()

    def shutdown(self):
        self.ssh_connection.close()

    def exec_command(self, command, print=False, opts=None, return_result=False):
        if opts is None:
            opts = {}
        full_command = "{} {}".format(command, join_parameter(opts))
        stdin, stdout, stderr = self.ssh_connection.exec_command(full_command)
        results = []
        i = stdout.readline()
        while i != '':
            results.append(i)
            i = stdout.readline()
            if print:
                logging.warning(i)
        logging.debug("{} completed!".format(full_command))
        if return_result:
            return results

    def exec_sudo_command(self, command, print=False, opts=None, return_result=False):
        if opts is None:
            opts = {}
        full_command = "{} {}".format(command, join_parameter(opts))
        sudo_command = 'sudo sh -c "{}"'.format(full_command)
        stdin, stdout, stderr = self.ssh_connection.exec_command(sudo_command)
        i = stdout.readline()
        results = []
        while i != '':
            results.append(i)
            i = stdout.readline()
            if print:
                logging.warning(i)
        logging.debug("{} completed!".format(full_command))
        if return_result:
            return results

    def pwd(self):
        stdin, stdout, stderr = self.ssh_connection.exec_command("pwd")
        return stdout.readline().rstrip("\n")

    def mkdir(self, root="", filename="tmp"):
        if not root:
            root = self.root_path
        self.exec_sudo_command("mkdir {}/{}".format(root,filename))

    def touch(self, root="", filename="tmp"):
        if not root:
            root = self.root_path
        self.exec_sudo_command("touch {}/{}".format(root,filename))

    def wget(self, url, save_path="", file_name="", opts=None):
        if opts is None:
            opts = {
                "--no-check-certificate": ""
            }
        if file_name:
            opts["-O"] = file_name
        if save_path:
            opts["-P"] = save_path
        else:
            opts["-P"] = self.root_path+"/tmp"
        command = "wget {}".format(url)
        self.exec_sudo_command(command, opts=opts)

    def tar(self, file_name, file_path="", mode="", opts=None):
        if opts is None:
            opts = {}
        if mode == "unzip":
            command = "tar -zxvf {}".format(file_name)
            self.exec_sudo_command(command, False, opts)
        elif mode == "zip":
            command = "tar -czvf {} {}".format(file_name, file_path)
            self.exec_sudo_command(command, False, opts)
        else:
            command = "tar --help"
            self.exec_sudo_command(command, True, opts)

    def unzip(self, file_name, opts=None):
        self.tar(file_name=file_name, mode="unzip", opts=opts)

    def zip(self, file_name, file_path, opts=None):
        self.tar(file_name=file_name, file_path=file_path, mode="zip", opts=opts)

    def mv(self, origin_file, new_file):
        command = "mv {} {}".format(origin_file, new_file)
        self.exec_sudo_command(command)

    def kill_by_process(self, process_name):
        command = "ps -ef|grep "+process_name+"|grep -v grep|awk '{print $2}'|xargs sudo kill -9"
        self.exec_command(command)

    def kill(self, pid):
        command = "kill -9 {}".format(pid)
        self.exec_command(command)

    def drop_net(self, ip_address):
        opts = {
            "-A": "INPUT",
            "-s": ip_address,
            "-j": "DROP",
            "-w": ""
        }
        self.iptables(opts)

    def drop_all_net(self, ip_address_list):
        opts = {
            "-A": "INPUT",
            "-s": ",".join(ip_address_list),
            "-j": "DROP",
            "-w": ""
        }
        self.iptables(opts)

    def heal_net(self):
        opts = {
            "-F": "",
            "-w": ""
        }
        self.iptables(opts)
        opts = {
            "-X": "",
            "-w": ""
        }
        self.iptables(opts)

    def iptables(self, opts):
        command = "iptables"
        self.exec_sudo_command(command, opts=opts, print=False)

    def get_time(self):
        command = "date '+%a %b %d %H:%M:%S %Y'"
        return self.exec_command(command, return_result=True)[0].strip('\n')

    def set_time(self, new_time):
        command = "date -s '{}'".format(new_time)
        self.exec_sudo_command(command)


if __name__ == "__main__":
    s = ssh_client(hostname="public-cd-a5.disalg.cn", port=22, username="leoyhwei", password="Asdf159753")
    print(s.set_time("2013-09-27 02:55:57"))
