#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import time
import requests
import string
import subprocess
from datetime import datetime
from urllib.parse import quote
from itertools import accumulate
from collections import defaultdict
from appium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from xxunit import Timer, logger, caps, rules, cfg
#from model import BankQuery
from secureRandom import SecureRandom as random
from xxQuestionBank import localmodel,LocalBank,LocalModel

class Automation():
    # 初始化 Appium 基本参数
    def __init__(self):
        self.connect()
        self.desired_caps = {
            "platformName": caps["platformname"],
            "platformVersion": caps["platformversion"],
            "automationName": caps["automationname"],
            "unicodeKeyboard": caps["unicodekeyboard"],
            "resetKeyboard": caps["resetkeyboard"],
            "noReset": caps["noreset"],
            'newCommandTimeout': 800,
            "deviceName": caps["devicename"],
            "uuid": caps["uuid"],
            "appPackage": caps["apppackage"],
            "appActivity": caps["appactivity"]
        }
        logger.info('打开 appium 服务,正在配置...')
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.desired_caps)
        self.wait = WebDriverWait(self.driver, 25)
        self.size = self.driver.get_window_size()

    def connect(self):
        logger.info(f'正在连接模拟器 {caps["uuid"]}，请稍候...')
        if 0 == subprocess.check_call(f'adb connect {caps["uuid"]}', shell=True, stdout=subprocess.PIPE):
            logger.info(f'模拟器 {caps["uuid"]} 连接成功')
        else:
            logger.info(f'模拟器 {caps["uuid"]} 连接失败')

    def disconnect(self):
        logger.info(f'正在断开模拟器 {caps["uuid"]}，请稍候...')
        if 0 == subprocess.check_call(f'adb disconnect {caps["uuid"]}', shell=True, stdout=subprocess.PIPE):
            logger.info(f'模拟器 {caps["uuid"]} 断开成功')
        else:
            logger.info(f'模拟器 {caps["uuid"]} 断开失败')

    # 屏幕方法
    def swipe_up(self):
        # 向上滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.65, 0.75),
                          self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.25, 0.35), random.uniform(800, 1200))
        logger.debug('向上滑动屏幕')

    def swipe_down(self):
        # 向下滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.25, 0.35),
                          self.size['width'] * random.uniform(0.55, 0.65),
                          self.size['height'] * random.uniform(0.65, 0.75), random.uniform(800, 1200))
        logger.debug('向下滑动屏幕')

    def swipe_right(self):
        # 向右滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.01, 0.11),
                          self.size['height'] * random.uniform(0.75, 0.89),
                          self.size['width'] * random.uniform(0.89, 0.98),
                          self.size['height'] * random.uniform(0.75, 0.89), random.uniform(800, 1200))
        logger.debug('向右滑动屏幕')
    def swipe_left(self):
        # 向右滑动屏幕
        self.driver.swipe(self.size['width'] * random.uniform(0.89, 0.98),
                          self.size['height'] * random.uniform(0.75, 0.89),
                          self.size['width'] * random.uniform(0.01, 0.11),
                          self.size['height'] * random.uniform(0.75, 0.89), random.uniform(800, 1200))
        logger.debug('向左滑动屏幕')

    def find_element(self, ele:str):
        logger.debug(f'find elements by xpath: {ele}')
        try:
            element = self.driver.find_element_by_xpath(ele)
        except NoSuchElementException as e:
            logger.error(f'找不到元素: {ele}')
            raise e
        return element

    def find_elements(self, ele:str):
        logger.debug(f'find elements by xpath: {ele}')
        try:
            elements = self.driver.find_elements_by_xpath(ele)
        except NoSuchElementException as e:
            logger.error(f'找不到元素: {ele}')
            raise e
        return elements

    # 返回事件
    def safe_back(self, msg='default msg'):
        logger.debug(msg)
        self.driver.keyevent(4)
        time.sleep(1) # 返回后延时1秒，如果模拟器渲染较慢，可以适当增大这个延时

    def safe_click(self, ele:str):
        logger.debug(f'safe click {ele}')
        button = self.wait.until(EC.presence_of_element_located((By.XPATH, ele)))
        # button = self.find_element(ele)
        button.click()
        time.sleep(1) # 点击后延时1秒，如果模拟器渲染较慢，可以适当增大这个延时

    def __del__(self):
        self.driver.close_app()
        self.driver.quit()


class App(Automation):
    def __init__(self, username="", password=""):
        self.username = username
        self.password = password
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
        }
        #self.query = BankQuery()
        self.bank = None
        self.score = defaultdict(tuple)

        super().__init__()

        self.login_or_not()
        self.driver.wait_activity('com.alibaba.android.rimet.biz.home.activity.HomeActivity', 20, 3)
        self.view_score()


    def login_or_not(self):
        # com.alibaba.android.user.login.SignUpWithPwdActivity
        time.sleep(10) # 首屏等待时间
        try:
            home = self.driver.find_element_by_xpath(rules["home_entry"])
            logger.debug(f'不需要登录')
            return 
        except NoSuchElementException as e:
            logger.debug(self.driver.current_activity)
            logger.debug(f"非首页，先进行登录")
        
        if not self.username or not self.password:
            logger.error(f'未提供有效的username和password')
            logger.info(f'也许你可以通过下面的命令重新启动:')
            logger.info(f'\tpython -m xuexi -u "your_username" -p "your_password"')
            raise ValueError('需要提供登录的用户名和密钥，或者提前在App登录账号后运行本程序')
        
        username = self.wait.until(EC.presence_of_element_located((
            By.XPATH, rules["login_username"]
        )))
        password = self.wait.until(EC.presence_of_element_located((
            By.XPATH, rules["login_password"]
        )))
        username.send_keys(self.username)
        password.send_keys(self.password)
        self.safe_click(rules["login_submit"])
        time.sleep(8)
        try:
            home = self.driver.find_element_by_xpath(rules["home_entry"])
            logger.debug(f'无需点击同意条款按钮')
            return 
        except NoSuchElementException as e:
            logger.debug(self.driver.current_activity)
            logger.debug(f"需要点击同意条款按钮")
            self.safe_click(rules["login_confirm"])
        time.sleep(3)
        
    def logout_or_not(self):
        if cfg.getboolean("prefers", "keep_alive"):
            logger.debug("无需自动注销账号")
            return 
        self.safe_click(rules["mine_entry"])
        self.safe_click(rules["setting_submit"])
        self.safe_click(rules["logout_submit"])
        self.safe_click(rules["logout_confirm"])
        logger.info("已注销")


    def view_score(self):
        self.safe_click(rules['score_entry'])
        titles = ["登录", "我要选读文章", "视听学习", "视听学习时长", "每日答题", "每周答题", "专项答题", 
                "挑战答题", "订阅", "分享", "发表观点", "本地频道"]
        try:
            score_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules['score_list'])))
            # score_list = self.find_elements(rules["score_list"])
        except:
            #ttt = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, 'android:id/button2')))
            self.driver.keyevent(4)
            score_list = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules['score_list'])))
          

        for t, score in zip(titles, score_list):
            s = score.get_attribute("name")
            self.score[t] = tuple([int(x) for x in re.findall(r'\d+', s)])

        print(self.score)
        for i in self.score:
            logger.debug(f'{i}, {self.score[i]}')
        self.safe_back('score -> home')

    def back_or_not(self, title):
        # return False
        g, t = self.score[title]
        if g == t:
            logger.debug(f'{title} 积分已达成，无需重复获取积分')
            return True
        return False

    def _search(self, content, options, exclude=''):
        # 职责 网上搜索
        logger.debug(f'搜索 {content} <exclude = {exclude}>')
        logger.info(f"选项 {options}")
        content = re.sub(r'[\(（]出题单位.*', "", content)
        if options[-1].startswith("以上") and chr(len(options)+64) not in exclude:
            logger.info(f'根据经验: {chr(len(options)+64)} 很可能是正确答案')
            return chr(len(options)+64)
        # url = quote('https://www.baidu.com/s?wd=' + content, safe=string.printable)
        url = quote("https://www.sogou.com/web?query=" + content, safe=string.printable)
        response = requests.get(url, headers=self.headers).text
        counts = []
        for i, option in zip(['A', 'B', 'C', 'D', 'E', 'F'], options):
            count = response.count(option)
            counts.append((count, i))
            logger.info(f'{i}. {option}: {count} 次')
        counts = sorted(counts, key=lambda x:x[0], reverse=True)
        counts = [x for x in counts if x[1] not in exclude]
        c, i = counts[0]
        if 0 == c:     
            # 替换了百度引擎为搜狗引擎，结果全为零的机会应该会大幅降低       
            _, i = random.choice(counts)
            logger.info(f'搜索结果全0，随机一个 {i}')
        logger.info(f'根据网络搜索结果: {i} 很可能是正确答案')
        return i






