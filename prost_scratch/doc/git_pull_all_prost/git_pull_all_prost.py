#! /usr/bin/env python
# coding:utf-8
import subprocess
from subprocess import check_output,Popen
import os
import time

#"git pull"を実行させたくないpackageはここに名前を入れてください。
ignore_packages = ["aaa", "bbb", "ccc"]


if __name__ == "__main__":
    #ネットに接続出来たか確認
    IP = "192.168.1."#接続を確認したいIP設定
    while True:
		wifi_ip = check_output(['hostname', '-I'])
		if IP in wifi_ip:
			print "###  start ###"
			#user_nameを取得 /home/xxx/catkin_wsのxxxの部分
			user_name = str(os.environ.get("USER"))

			#catkin_ws/src/にあるファイル名をすべて取得する
			packages = subprocess.Popen(("ls", "/home/"+user_name+"/catkin_ws/src"), stdout=subprocess.PIPE).stdout.readlines()

			#CMakeListsはパッケージではないので除去
			packages.remove('CMakeLists.txt\n')

			#各packageに対して"git pull"を実行
			for package in packages:
				#改行コードを除去
				package_name = str(package.strip("\n"))

				#packageの中身のファイル名を取得
				elements = subprocess.Popen(("ls", "-a","/home/"+user_name+"/catkin_ws/src/"+package_name), stdout=subprocess.PIPE).stdout.readlines()

				# GitLab(GitHub)からcloneしたファイルを検索
				if ".git\n" in elements:
				    print "----------------"
				    print "[%s]"%package_name

				    try:
				        #packageがある場所まで絶対パスで移動
				        os.chdir( "/home/"+user_name+"/catkin_ws/src/"+package_name)

				        if package_name in ignore_packages:
				            print "pass\n"
				        else:
				            #"git pull"実行
				            res = subprocess.Popen(("git", "pull"), stdout=subprocess.PIPE).stdout.readlines()
				            print str(res[0])
				    except:
				        print "Some error has occuered."
	   
		    
			#prostのnodeを立てる
			#node_run = Popen(["roslaunch","prost_scratch","scratch_connector.launch"])
			#time.sleep(3)
			break
    print("--git pull finish--")
