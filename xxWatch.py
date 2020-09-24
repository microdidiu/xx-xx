# 视听学习模块  
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from xxunit import logger,cfg,rules
from secureRandom import SecureRandom as random
from xxQuestionBank import localmodel,LocalBank,LocalModel

class xxWatch(): 
    def __init__(self,app):
        self.app=app
        self.has_bgm = cfg.get("prefers", "radio_switch")
        if "disable" == self.has_bgm:
            self.view_time = 1080
        else:
            self.view_time = 360
        self.radio_chanel = cfg.get("prefers", "radio_chanel")
        try:
            self.video_count = cfg.getint("prefers", "video_count")
            self.view_delay = 15
        except:
            g, t = self.app.score["视听学习"]
            if t == g:
                self.video_count = 0
                self.view_delay = random.randint(15, 30)
            else:
                self.video_count = random.randint(
                        cfg.getint('prefers', 'video_count_min'), 
                        cfg.getint('prefers', 'video_count_max'))
                self.view_delay = self.view_time // self.video_count + 1
        logger.debug(f'视听学习: {self.video_count}')

    def music(self):
        if "disable" == self.has_bgm:
            logger.debug(f'广播开关 关闭')
        elif "enable" == self.has_bgm:
            logger.info(f'广播开关 开启')
            self._music()
        else:
            logger.debug(f'广播开关 默认')
            g, t = self.score["视听学习时长"]
            if g ==  t:
                logger.debug(f'视听学习时长积分已达成，无需重复收听')
                return
            else:
                self._music()
    
    def _music(self):
        logger.debug(f'正在打开《{self.radio_chanel}》...')
        self.app.safe_click('//*[@resource-id="cn.xuexi.android:id/home_bottom_tab_button_mine"]')
        self.app.safe_click('//*[@text="听新闻广播"]')
        self.app.safe_click(f'//*[@text="{self.radio_chanel}"]')
        self.app.safe_click(rules['home_entry'])

    def _watch(self, video_count=None):
        g1, t1 = self.app.score["视听学习"]
        g2, t2 = self.app.score["视听学习时长"]
        
        if (g1 ==  t1)  and (g2==t2):
            logger.debug(f'视听学习时长积分已达成，无需重复收听')
            return

        logger.info("开始浏览百灵视频...")
        self.app.safe_click(rules['bailing_enter'])
        self.app.safe_click(rules['bailing_enter']) # 再点一次刷新短视频列表
        self.app.safe_click(rules['video_first'])
        logger.info(f'预计观看视频 {video_count} 则')
        while video_count:
            video_count -= 1
            video_delay = random.randint(self.view_delay, self.view_delay + min(10, self.video_count))
            logger.info(f'正在观看视频 <{video_count}#> {video_delay} 秒进入下一则...')
            time.sleep(video_delay)
            self.app.swipe_up()
        else:
            logger.info(f'视听学习完毕，正在返回...')
            self.app.safe_back('video -> bailing')
            logger.debug(f'正在返回首页...')
            self.app.safe_click(rules['home_entry'])

    def watch(self):
        self._watch(self.video_count)
