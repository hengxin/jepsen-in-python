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



    def shutdown(self):
        self.ssh_connection.close()

    def exec_command(self, command, print=False, opts=None):
        if opts is None:
            opts = {}
        full_command = "{} {}".format(command, join_parameter(opts))
        stdin, stdout, stderr = self.ssh_connection.exec_command(full_command)
        i = stdout.readline()
        while i != '':
            i = stdout.readline()
            if print:
                logging.warning(i)
        logging.info("{} completed!".format(full_command))
        return

    def wget(self, url, save_path="", file_name="", opts=None):
        if opts is None:
            opts = {}
        if file_name:
            opts["-O"] = file_name
        if save_path:
            opts["-P"] = save_path
        command = "wget {}".format(url)
        self.exec_command(command, opts)

    def tar(self, file_name, file_path="", mode="", opts=None):
        if opts is None:
            opts = {}
        if mode == "unzip":
            command = "tar -zxvf {}".format(file_name)
            self.exec_command(command, False, opts)
        elif mode == "zip":
            command = "tar -czvf {} {}".format(file_name, file_path)
            self.exec_command(command, False, opts)
        else:
            command = "tar --help"
            self.exec_command(command, True, opts)

    def unzip(self, file_name, opts=None):
        self.tar(file_name=file_name, mode="unzip", opts=opts)

    def zip(self, file_name, file_path, opts=None):
        self.tar(file_name=file_name, file_path=file_path, mode="zip", opts=opts)

    def mv(self, origin_file, new_file):
        command = "mv {} {}".format(origin_file, new_file)
        self.exec_command(command)

    def kill_by_process(self, process_name):
        command = "ps -ef|grep "+process_name+"|grep -v grep|awk '{print $2}'|xargs kill -9"
        self.exec_command(command)

    def kill(self, pid):
        command = "kill -9 {}".format(pid)
        self.exec_command(command)