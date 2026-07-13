# 贸易项目每日推送——每天18:00自动发送飞书卡片
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

from 飞书关键词助手 import 查投标, 查中标, 查全部, 查贷款到期

查投标()
查中标()
查全部()
查贷款到期()

print("Daily push done")
