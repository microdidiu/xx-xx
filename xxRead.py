# 新闻阅读模块
#from unit import Timer,  caps, rules, cfg
from xxunit import logger,cfg,rules
from secureRandom import SecureRandom as random
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
class xxRead():
    def __init__(self,app):
        self.app=app
        self.read_time = 361
        self.volumn_title = cfg.get("prefers", "article_volumn_title")
        self.star_share_comments_count = cfg.getint("prefers", "star_share_comments_count")
        self.titles = list()
        try:
            self.read_count = cfg.getint("prefers", "article_count")
            self.read_delay = 30
        except:
            self.read_count = random.randint(
                        cfg.getint('prefers', 'article_count_min'), 
                        cfg.getint('prefers', 'article_count_max'))
            self.read_delay = self.read_time // self.read_count + 1
        logger.debug(f'阅读文章: {self.read_count}')

    def _star_once(self):
        return
        if self.back_or_not("收藏"):
            return
        logger.debug(f'这篇文章真是妙笔生花呀！收藏啦！')
        self.safe_click(rules['article_stars'])
        # self.safe_click(rules['article_stars']) # 取消收藏

    def _comments_once(self, title="好好学习，天天强国"):
        # return # 拒绝留言
        if self.app.back_or_not("发表观点"):
            return
        logger.debug(f'哇塞，这么精彩的文章必须留个言再走！')
        self.app.safe_click(rules['article_comments'])
        edit_area = self.app.wait.until(EC.presence_of_element_located((By.XPATH, rules['article_comments_edit'])))
        # edit_area = self.find_element(rules['article_comments_edit'])
        edit_area.send_keys(title)
        self.app.safe_click(rules['article_comments_publish'])
        time.sleep(2)
        self.app.safe_click(rules['article_comments_list'])
        self.app.safe_click(rules['article_comments_delete'])
        self.app.safe_click(rules['article_comments_delete_confirm'])

    def _share_once(self):
        if self.app.back_or_not("分享"):
            return
        logger.debug(f'好东西必须和好基友分享，走起，转起！')
        self.app.safe_click(rules['article_share'])
        self.app.safe_click(rules['article_share_xuexi'])
        time.sleep(3)
        self.app.safe_back('share -> article')

    def _star_share_comments(self, title):
        logger.debug(f'哟哟，切克闹，收藏转发来一套')
        if random.random() < 0.33:
            self._comments_once(title)
            if random.random() < 0.5:
                self._star_once()
                self._share_once()
            else:
                self._share_once()
                self._star_once()
        else:
            if random.random() < 0.5:
                self._star_once()
                self._share_once()
            else:
                self._share_once()
                self._star_once()
            self._comments_once(title)

    def _read(self, num, ssc_count):
        logger.info(f'预计阅读新闻 {num} 则')
        while num > 0: # or ssc_count:
            try:
                articles = self.app.driver.find_elements_by_xpath(rules['article_list'])
            except:
                logger.debug(f'真是遗憾，一屏都没有可点击的新闻')
                articles = []
            for article in articles:
                title = article.get_attribute("name")
                if title in self.titles:
                    continue
                try:
                    pic_num = article.parent.find_element_by_id("cn.xuexi.android:id/st_feeds_card_mask_pic_num")
                    logger.debug(f'这绝对是摄影集，直接下一篇')
                    continue
                except:
                    logger.debug(f'这篇文章应该不是摄影集了吧')
                article.click()
                num -= 1
                logger.info(f'<{num}> 当前篇目 {title}')
                article_delay = random.randint(self.read_delay, self.read_delay+min(10, self.read_count))
                logger.info(f'阅读时间估计 {article_delay} 秒...')
                while article_delay > 0:
                    if article_delay < 20:
                        delay = article_delay
                    else:
                        delay = random.randint(min(10, article_delay), min(20, article_delay))
                    logger.debug(f'延时 {delay} 秒...')
                    time.sleep(delay)
                    article_delay -= delay
                    self.app.swipe_up()
                else:
                    logger.debug(f'完成阅读 {title}')

                if ssc_count > 0:
                    try:
                        comment_area = self.app.driver.find_element_by_xpath(rules['article_comments'])
                        self._star_share_comments(title)
                        ssc_count -= 1
                    except:
                        logger.debug('这是一篇关闭评论的文章，收藏分享留言过程出现错误')

                self.titles.append(title)
                self.app.safe_back('article -> list')
                if 0 >= num:
                    break
            else:
                self.app.swipe_up()
    
    def _kaleidoscope(self):
        ''' 本地频道积分 +1 '''
        if self.app.back_or_not("本地频道"):
            return 
        volumns = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules['article_volumn'])))
        volumns[3].click()
        time.sleep(10)
        # self.safe_click(rules['article_kaleidoscope'])
        target = None
        try:
            target = self.app.driver.find_element_by_xpath(rules['article_kaleidoscope'])
        except NoSuchElementException as e:
            logger.error(f'没有找到城市万花筒入口')

        if target:
            target.click()
            time.sleep(3)
            delay = random.randint(5, 15)
            logger.info(f"在本地学习平台驻足 {delay} 秒")
            time.sleep(delay)
            self.app.safe_back('学习平台 -> 文章列表')

    def read(self):
        g, t = self.app.score["我要选读文章"]
        if t == g:
            logger.info(f'新闻阅读已达成，无需重复阅读')
            return
        logger.debug(f'正在进行新闻学习...')
        self._kaleidoscope()
        vol_not_found = True
        while vol_not_found:
            volumns = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules['article_volumn'])))
            # volumns = self.find_elements(rules['article_volumn'])
            first_vol = volumns[1]
            for vol in volumns:
                title = vol.get_attribute("name")
                logger.debug(title)
                if self.volumn_title == title:
                    vol.click()
                    vol_not_found = False
                    break
            else:
                logger.debug(f'未找到 {self.volumn_title}，左滑一屏')
                self.app.driver.scroll(vol, first_vol, duration=500)
        
        self._read(self.read_count, self.star_share_comments_count)

