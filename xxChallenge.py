# 挑战答题模块
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from xxunit import logger,cfg,rules
from secureRandom import SecureRandom as random
from xxQuestionBank import localmodel,LocalBank,LocalModel

class xxChallenge():
    def __init__(self,app):
        self.app=app
        try:
            self.challenge_count = cfg.getint('prefers', 'challenge_count')
        except:

                self.challenge_count = random.randint(
                        cfg.getint('prefers', 'challenge_count_min'), 
                        cfg.getint('prefers', 'challenge_count_max'))

        self.challenge_delay_bot = cfg.getint('prefers', 'challenge_delay_min')
        self.challenge_delay_top = cfg.getint('prefers', 'challenge_delay_max')
        logger.debug(f'挑战答题: {self.challenge_count}')

    def _challenge_cycle(self, num):
        self.app.safe_click(rules['challenge_entry'])
        offset = 0 # 自动答错的偏移开关
        while num>-1:
            print('')
            print('') 

            content = self.app.wait.until(EC.presence_of_element_located(
                (By.XPATH, rules['challenge_content']))).get_attribute("name")
            # content = self.find_element(rules["challenge_content"]).get_attribute("name")
            option_elements = self.app.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, rules['challenge_options'])))
            # option_elements = self.find_elements(rules['challenge_options'])
            options = [x.get_attribute("name") for x in option_elements]
            length_of_options = len(options)
            logger.info(f'<{num}> {content}')

            answer = self.challenge_verify(category='挑战题', content=content, options=options)
            
            delay_time = random.randint(self.challenge_delay_bot, self.challenge_delay_top)            
            if 0 == num:
                offset = random.randint(1, length_of_options-1) # randint居然包含上限值，坑爹！！！
                logger.info(f'已完成指定题量，设置提交选项偏移 -{offset}')
                logger.info(f'随机延时 {delay_time} 秒提交答案: {chr((ord(answer)-65-offset+length_of_options)%length_of_options+65)}')
            else:
                logger.info(f'随机延时 {delay_time} 秒提交答案: {answer}')
            time.sleep(delay_time)    
            # 利用python切片的特性，即使索引值为-offset，可以正确取值
            option_elements[ord(answer)-65 - offset].click()
            try:
                time.sleep(5)
                wrong=None
                wrong = self.app.driver.find_element_by_xpath(rules["challenge_over"])
            except:
                logger.info(f'恭喜本题回答正确')

            if wrong is None:
                num -= 1            
                localmodel.update_bank('挑战题', content, options,answer,'','')
            else:    
                logger.info(f'很遗憾本题回答错误')
                if num>0:  
                    localmodel.update_bank('挑战题', content, options,'',answer,'')
                logger.debug("点击结束本局")              
                wrong.click() # 直接结束本局
                time.sleep(5)
                break


        else:
            logger.debug("通过选项偏移，应该不会打印这句话，除非碰巧答案有误")
            logger.debug("那么也好，延时30秒后结束挑战")
            time.sleep(30)
            self.app.safe_back('challenge -> share_page') # 发现部分模拟器返回无效
        # 更新后挑战答题需要增加一次返回
        time.sleep(5)
        self.app.safe_back('share_page -> quiz') # 发现部分模拟器返回无效
        return num


    def _challenge(self):
        
        logger.info(f'挑战答题 目标 {self.challenge_count} 题, Go!')
        while True:
            result = self._challenge_cycle(self.challenge_count)
            if 0 >= result:
                logger.info(f'已成功挑战 {self.challenge_count} 题，正在返回')
                break
            else:
                delay_time = random.randint(1,3)
                logger.info(f'本次挑战 {self.challenge_count - result} 题，{delay_time} 秒后再来一组')
                time.sleep(delay_time)
                continue

        

    def challenge(self):
        g, t = self.app.score["挑战答题"]
        if t == g:
            logger.info(f'挑战答题积分已达成，无需重复挑战')
            #self.challenge_count=2222
            return
        self.app.safe_click(rules['mine_entry'])
        self.app.safe_click(rules['quiz_entry'])
        time.sleep(3)
        self._challenge()
        self.app.safe_back('quiz -> mine')
        self.app.safe_back('mine -> home')

    def challenge_verify(self, category, content, options):
        # 检索题库 
        mybank=None
        mybank=localmodel.query(content,options[0],category)

        if mybank:
            logger.info(f'题库中查到题目,id:{mybank.id}')
            if mybank.answer:
                logger.info(f'已知的正确答案: {mybank.answer}')
                return mybank.answer
            else:
                excludes = mybank.excludes if mybank else ""     # 当if为真时，VAR = VALUE1, 否则VAR=VALUE2  VAR = VALUE1 if CONDITION else VALUE2
                logger.info(f'题目类型: {category}')
                return self.app._search(content, options, excludes)
        else:
            logger.info(f'添加新题目')
            localmodel.add(content,category,options)

            return self.app._search(content, options)