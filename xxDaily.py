# 每日答题模块
import time
import re
import string
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from xxunit import logger,cfg,rules
from secureRandom import SecureRandom as random
from xxQuestionBank import localmodel,LocalBank,LocalModel

class xxDaily():
    def __init__(self,app):
        self.app=app
        self.g, self.t = 0, 6
        self.count_of_each_group = cfg.getint('prefers', 'daily_count_each_group')
        try:
            self.daily_count = cfg.getint('prefers', 'daily_count')
            self.daily_force = self.daily_count > 0
        except:
            self.g, self.t = self.app.score["每日答题"]
            self.daily_count = self.t - self.g
            self.daily_force = False

        self.daily_delay_bot = cfg.getint('prefers', 'daily_delay_min')
        self.daily_delay_top = cfg.getint('prefers', 'daily_delay_max')

        self.delay_group_bot = cfg.getint('prefers', 'daily_group_delay_min')
        self.delay_group_top = cfg.getint('prefers', 'daily_group_delay_max')
        logger.debug(f"每日答题: {self.daily_count}")

    def _submit(self, delay=None):
        if not delay:
            delay = random.randint(self.daily_delay_bot, self.daily_delay_top)
            logger.info(f'随机延时 {delay} 秒...')
        time.sleep(delay)
        self.app.safe_click(rules["daily_submit"])
        time.sleep(random.randint(1,3))

    def _view_tips(self):
        content = ""
        try:
            tips_open = self.app.driver.find_element_by_xpath(rules["daily_tips_open"])
            tips_open.click()
        except NoSuchElementException as e:
            logger.debug("没有可点击的【查看提示】按钮")
            return ""
        time.sleep(2)
        try:
            tips = self.app.wait.until(EC.presence_of_element_located((
                By.XPATH, rules["daily_tips"]
            )))     
            content = tips.get_attribute("name")
            logger.debug(f'提示 {content}')
        except NoSuchElementException as e:
            logger.error(f'无法查看提示内容')
            return ""
        time.sleep(2)
        try:
            tips_close = self.app.driver.find_element_by_xpath(rules["daily_tips_close"])
            tips_close.click()
            
        except NoSuchElementException as e:
            logger.debug("没有可点击的【X】按钮")
        time.sleep(2)
        return content

    def _blank_answer_divide(self, ans:str, arr:list):
        accu_revr = [x for x in accumulate(arr)]
        print(accu_revr)
        temp  = list(ans)
        for c in accu_revr[-2::-1]:
            temp.insert(c, " ")
        return "".join(temp)        

    def _blank(self):
        contents = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_blank_content"])))
        # contents = self.find_elements(rules["daily_blank_content"])
        # content = " ".join([x.get_attribute("name") for x in contents])
        logger.debug(f'len of blank contents is {len(contents)}')
        if 1 < len(contents):
            # 针对作妖的UI布局某一版            
            content, spaces = "", []
            for item in contents:
                content_text = item.get_attribute("name")
                if "" != content_text:
                    content += content_text
                else:
                    length_of_spaces = len(item.find_elements(By.CLASS_NAME, "android.view.View"))-1
                    
                    spaces.append(length_of_spaces)
                    content += " " * (length_of_spaces)
                
        
        else:
            # 针对作妖的UI布局某一版
            contents = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_blank_container"])))
            content, spaces, _spaces = "", [], 0
            for item in contents:
                content_text = item.get_attribute("name")
                if "" != content_text:
                    content += content_text
                    if _spaces:
                        spaces.append(_spaces)
                        _spaces = 0
                else:
                    content += " "
                    _spaces += 1
            else: # for...else...
                # 如果填空处在最后，需要加一个判断
                if _spaces:
                    spaces.append(_spaces)
                logger.debug(f'[填空题] {content} [{" ".join([str(x) for  x in spaces])}]')
            logger.debug(f'空格数 {spaces}')
        blank_edits = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_blank_edits"])))
        # blank_edits = self.find_elements(rules["daily_blank_edits"])
        length_of_edits = len(blank_edits)
        logger.info(f'填空题 {content}')
        answer = self._verify("填空题", content, []) # 
        if not answer:
            words = (''.join(random.sample(string.ascii_letters + string.digits, 8)) for i in range(length_of_edits))
        else:
            words = answer.split(" ")
        logger.debug(f'提交答案 {words}')
        for k,v in zip(blank_edits, words):
            k.send_keys(v)
            time.sleep(1)

        self._submit()
        try:            
            wrong_or_not = self.app.driver.find_element_by_xpath(rules["daily_wrong_or_not"])
            right_answer = self.app.driver.find_element_by_xpath(rules["daily_answer"]).get_attribute("name")
            answer = re.sub(r'正确答案： ', '', right_answer)
            logger.info(f"答案 {answer}")
            notes = self.app.driver.find_element_by_xpath(rules["daily_notes"]).get_attribute("name")
            logger.debug(f"解析 {notes}")
            self._submit(2)
            if 1 == length_of_edits:
                localmodel.update_bank('挑战题', content, [""],answer,'',notes)

            else:
                logger.error("多位置的填空题待验证正确性")
                localmodel.update_bank('填空题', content, [""],self._blank_answer_divide(answer, spaces),'',notes)

        except:
            logger.debug("填空题回答正确")

        
    def _radio(self):
        content = self.app.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_content"]))).get_attribute("name")
        # content = self.find_element(rules["daily_content"]).get_attribute("name")
        option_elements = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_options"])))
        # option_elements = self.driver.find_elements(rules["daily_options"])
        options = [x.get_attribute("name") for x in option_elements]
        length_of_options = len(options)
        logger.info(f"单选题 {content}")
        logger.info(f"选项 {options}")
        answer = self._verify("单选题", content, options)
        choose_index = ord(answer) - 65
        logger.info(f"提交答案 {answer}")
        option_elements[choose_index].click()
        # 提交答案
        self._submit()
        try:            
            wrong_or_not = self.app.driver.find_element_by_xpath(rules["daily_wrong_or_not"])
            right_answer = self.app.driver.find_element_by_xpath(rules["daily_answer"]).get_attribute("name")
            right_answer = re.sub(r'正确答案： ', '', right_answer)
            logger.info(f"答案 {right_answer}")
            # notes = self.driver.find_element_by_xpath(rules["daily_notes"]).get_attribute("name")
            # logger.debug(f"解析 {notes}")
            self._submit(2)
            localmodel.update_bank("单选题", content, options,right_answer,"","")

        except:
            localmodel.update_bank("单选题", content, options,answer,"","")

    def _check(self):
        content = self.app.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_content"]))).get_attribute("name")
        # content = self.find_element(rules["daily_content"]).get_attribute("name")
        option_elements = self.app.wait.until(EC.presence_of_all_elements_located((By.XPATH, rules["daily_options"])))
        # option_elements = self.driver.find_elements(rules["daily_options"])
        options = [x.get_attribute("name") for x in option_elements]
        length_of_options = len(options)
        logger.info(f"多选题 {content}\n{options}")
        answer = self._verify("多选题", content, options)
        logger.debug(f'提交答案 {answer}')
        for k, option in zip(list("ABCDEFG"), option_elements):
            if k in answer:
                option.click()
                time.sleep(1)
            else:
                continue
        # 提交答案
        self._submit()
        try:
            wrong_or_not = self.app.driver.find_element_by_xpath(rules["daily_wrong_or_not"])
            right_answer = self.app.driver.find_element_by_xpath(rules["daily_answer"]).get_attribute("name")
            right_answer = re.sub(r'正确答案： ', '', right_answer)
            logger.info(f"答案 {right_answer}")
            # notes = self.driver.find_element_by_xpath(rules["daily_notes"]).get_attribute("name")
            # logger.debug(f"解析 {notes}")
            self._submit(2)
            localmodel.update_bank("多选题", content, options,right_answer,"","")

        except:
            localmodel.update_bank("多选题", content, options,answer,"","")


    def _dispatch(self, count_of_each_group):
        time.sleep(3) # 如果模拟器比较流畅，这里的延时可以适当调短
        for i in range(count_of_each_group):
            logger.debug(f'正在答题 第 {i+1} / {count_of_each_group} 题')
            try:
                category = self.app.driver.find_element_by_xpath(rules["daily_category"]).get_attribute("name")
            except NoSuchElementException as e:
                logger.error(f'无法获取题目类型')
                raise e
            print(category)
            if "填空题" == category:
                self._blank()
            elif "单选题" == category:
                self._radio()
            elif "多选题" == category:
                self._check()
            else:
                logger.error(f"未知的题目类型: {category}")
            

    def _daily(self, num):
        self.app.safe_click(rules["daily_entry"])
        while num:
            num -= 1
            logger.info(f'每日答题 第 {num}# 组')
            self._dispatch(self.count_of_each_group)
            if not self.daily_force:
                score = self.app.wait.until(EC.presence_of_element_located((By.XPATH, rules["daily_score"]))).get_attribute("name")
                # score = self.find_element(rules["daily_score"]).get_attribute("name")
                try:
                    score = int(score)
                except:
                    raise TypeError('integer required')
                self.g += score
                if self.g == self.t:
                    logger.info(f"今日答题已完成，返回")
                    break
            if num == 0:
                logger.debug(f'今日循环结束 <{self.g} / {self.t}>')
                break
            delay = random.randint(self.delay_group_bot, self.delay_group_top)
            logger.info(f'每日答题未完成 <{self.g} / {self.t}> {delay} 秒后再来一组')
            time.sleep(delay)
            self.app.safe_click(rules['daily_again'])
            continue
        else:
            logger.debug("应该不会执行本行代码")

        self.app.safe_back('daily -> quiz')
        try:
            back_confirm = self.app.driver.find_element_by_xpath(rules["daily_back_confirm"])
            back_confirm.click()
        except:
            logger.debug(f"无需点击确认退出")
    
    def daily(self):
        if 0 == self.daily_count:
            logger.info(f'每日答题积分已达成，无需重复答题')
            return
        self.app.safe_click(rules['mine_entry'])
        self.app.safe_click(rules['quiz_entry'])
        time.sleep(3)
        self._daily(self.daily_count)
        self.app.safe_back('quiz -> mine')
        self.app.safe_back('mine -> home')


    def _verify(self, category, content, options):
        # 职责: 检索题库 查看提示
        letters = list("ABCDEFGHIJKLMN")
        print('')

        print('题目类型:',category)
        print('题目内容:',content)
        print('选项：',options)

        mybank=None
        if len(options)>1:
            mybank=localmodel.query(content,options[0],category)
        else:
            mybank=localmodel.query(content,'',category)    
        
        if mybank and mybank.answer:
            logger.info(f'已知的正确答案: {mybank.answer}')
            return mybank.answer
  
        excludes = mybank["excludes"] if mybank else ""
        logger.info(f'题目类型: {category}')
        tips = self._view_tips()
        if not tips:
            logger.debug("本题没有提示")
            if "填空题" == category:
                return None
            elif "多选题" == category:
                return "ABCDEFG"[:len(options)]
            elif "单选题" == category:
                return self.app._search(content, options, excludes)
            else:
                logger.debug("题目类型非法")            
        else:
            if "填空题" == category:
                dest = re.findall(r'.{0,2}\s+.{0,2}', content)
                logger.debug(f'dest: {dest}')
                if 1 == len(dest):
                    dest = dest[0]
                    logger.debug(f'单处填空题可以尝试正则匹配')
                    pattern = re.sub(r'\s+', '(.+?)', dest)
                    logger.debug(f'匹配模式 {pattern}')
                    res = re.findall(pattern, tips)
                    if 1 == len(res):
                        return res[0]
                logger.debug(f'多处填空题难以预料结果，索性不处理')
                return None
                
            elif "多选题" == category:
                check_res = [letter for letter, option in zip(letters, options) if option in tips]
                if len(check_res) > 1:
                    logger.debug(f'根据提示，可选项有: {check_res}')
                    return "".join(check_res)
                return "ABCDEFG"[:len(options)]
            elif "单选题" == category:
                radio_in_tips, radio_out_tips = "", ""
                for letter, option in zip(letters, options):
                    if option in tips:
                        logger.debug(f'{option} in tips')
                        radio_in_tips += letter
                    else:
                        logger.debug(f'{option} out tips')
                        radio_out_tips += letter

                logger.debug(f'含 {radio_in_tips} 不含 {radio_out_tips}')
                if 1 == len(radio_in_tips) and radio_in_tips not in excludes:
                    logger.debug(f'根据提示 {radio_in_tips}')
                    return radio_in_tips
                if 1 == len(radio_out_tips) and radio_out_tips not in excludes:
                    logger.debug(f'根据提示 {radio_out_tips}')
                    return radio_out_tips
                return self.app._search(content, options, excludes)
            else:
                logger.debug("题目类型非法")
