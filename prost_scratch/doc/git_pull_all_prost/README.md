# Git_Pull_All

## 説明
`~/catkin_ws/src`の中にあるパッケージの**全て**に対して`git pull`を実行します。  

## 使い方
```
cd ~/git_pull_all_prost

python git_pull_all_prost.py

```

~/.bashrcに、
`alias gpa='cd && python git_pull_all/git_pull_all_prost.py'`と記入しておけば、便利だと思います。

## 注意
- `git pull`を実行させたくないpackageは、git_pull_all_prost.pyの７行目にある`ignore_packages`の中に記入しておいてください。
- 最初の１回はパスワードの入力を求められるかもしれません。
