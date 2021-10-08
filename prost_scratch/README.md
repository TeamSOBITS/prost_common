# TurtleBot一斉git pullの手順

## cluster sshのインストール

```bash
sudo apt install clusterssh
```

## bashrcを開く

```bash
sudo gedit ~/.bashrc
```

## bashrcに以下を記述

```bash
alias ps-ssh='cssh pi-ps@192.168.1.10 pi-ps@192.168.1.20 pi-ps@192.168.1.30 pi-ps@192.168.1.40 pi-ps@192.168.1.50 pi-ps@192.168.1.60'
```

### WifiとすべてのTurtleBotの電源を入れる（OSが立ち上がるまで30秒ほど待つ。）

## clustersshを起動（最初はturtlebotに接続するかどうか(yes or no)、パスワードの入力を要求される。）

```bash
sudo gedit ~/.bashrc
```

## 以下、macrosモードで同じコマンドを6台に一斉送信(個別で制御するときはmacrosモードを切ること)

```bash
python git_pull_all_prost.py 
```

# scratchのlaunch群の基本制御コマンド

## launchの開始(電源起動時に勝手に実行される)

```bash
sudo systemctl start scratch.service
```

## launchの終了

```bash
sudo systemctl stop scratch.service
```

## launchの状態表示

```bash
sudo systemctl status scratch.service
```
