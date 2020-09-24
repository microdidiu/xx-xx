
# -*- coding:utf-8 -*-

from argparse import ArgumentParser
import time
from xxAppium import App
from xxunit import logger
from secureRandom import SecureRandom as random
import sys
from xxRead import xxRead
from xxChallenge import xxChallenge
from xxWatch import xxWatch
from xxDaily import xxDaily
from xxweekly import xxWeekly

def shuffle(funcs):
    random.shuffle(funcs)
    for func in funcs:
        func()
        time.sleep(5)

def start():
    try:
      if random.random() > 0.5:
        logger.debug(f'视听学习优先')
        app.watch()
        app.music()
        shuffle([app.read, app.daily, app.challenge, app.weekly])
      else:
        logger.debug(f'视听学习置后')
        app.music()
        shuffle([app.read, app.daily, app.challenge, app.weekly])
        app.watch()
      app.logout_or_not()
    except:
        print("发生异常")
        return 1;
    else:
        return 0;  
#    
    sys.exit(0)

if __name__ == "__main__":
    parse = ArgumentParser(description="Accept username and password if necessary!")
    parse.add_argument("-u", "--username", metavar="username", type=str, default='', help='User Name')
    parse.add_argument("-p", "--password", metavar="password", type=str, default='', help='Pass Word')
    args = parse.parse_args()
    app = App(args.username, args.password)

    xxwatch=xxWatch(app)
    xxread=xxRead(app)
    xxchallenge=xxChallenge(app)
    xxdaily=xxDaily(app)
    xxWeekly=xxWeekly(app,xxdaily)

    xxwatch.music()
    xxread.read()


    app.view_score()
    xxdaily.daily()

    app.view_score()
    xxchallenge.challenge()

    app.view_score()
    xxwatch.watch()
#    xxWeekly.weekly()    #无法保证满分

    import os
    os.system('pause') #按任意键继续
    app.logout_or_not()
    sys.exit(0)

