import time
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from xxunit import logger,cfg,rules
from secureRandom import SecureRandom as random
from xxQuestionBank import localmodel,LocalBank,LocalModel

class xxWeekly():
    def __init__(self,app,xxdaily):
        self.app=app
        self.daily=xxdaily
        self.workdays = cfg.get("prefers", "workdays")
        logger.debug(f"每周答题: {self.workdays}")

    def _weekly(self):
        self.app.safe_click(rules["weekly_entry"])
        titles= self.app.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, rules["weekly_titles"])))

        states= self.app.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, rules["weekly_states"])))
        
        # first, last = None, None
        for title, state in zip(titles, states):
            # if not first and title.location_in_view["y"]>0:
            #     first = title
            if self.app.size["height"] - title.location_in_view["y"] < 10:
                logger.debug(f'屏幕内没有未作答试卷')
                break
            logger.debug(f'{title.get_attribute("name")} {state.get_attribute("name")}')
            if "未作答" == state.get_attribute("name"):
                logger.info(f'{title.get_attribute("name")}, 开始！')
                state.click()
                time.sleep(random.randint(5,9))
                self.daily._dispatch(5) # 这里直接采用每日答题
                break
        self.app.safe_back('weekly report -> weekly list')
        self.app.safe_back('weekly list -> quiz')

        


    def weekly(self):
        ''' 每周答题
            复用每日答题的方法，无法保证每次得满分，如不能接受，请将配置workdays设为0
        '''      
        day_of_week = datetime.now().isoweekday()
        if str(day_of_week) not in self.workdays:
            logger.debug(f'今日不宜每周答题 {day_of_week} / {self.workdays}')
            return
        if self.app.back_or_not("每周答题"):
            return

        self.app.safe_click(rules['mine_entry'])
        self.app.safe_click(rules['quiz_entry'])
        time.sleep(3)
        self._weekly()
        self.app.safe_back('quiz -> mine')
        self.app.safe_back('mine -> home')
        
    #专项答题
    def _special(self):
        self.app.safe_click(rules["special_entry"])
        self.app.safe_click(rules["special_current"])

        time.sleep(5)
        for i in range(10):
            logger.debug(f'专项答题 第 {i+1} 题')
            try:
                category = self.app.driver.find_element_by_xpath(rules["special_category"]).get_attribute("name")
                print(category)
            except NoSuchElementException as e:
                logger.error(f'无法获取题目类型')
                raise e
            if "填空题 (10分)" == category:
                self.daily._blank()
            elif "单选题 (10分)" == category:
                self.daily._radio()
            elif "多选题 (10分)" == category:
                self.daily._check()
            else:
                logger.error(f"未知的题目类型: {category}")
                raise('未知的题目类型')
        logger.debug(f'专项答题循环结束')
        self.app.safe_back('speical report -> special list')
        self.app.safe_back('special list -> quiz')
