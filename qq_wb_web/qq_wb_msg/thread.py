#coding=utf-8
__author__ = 'shifeixiang'
import time
import thread
import threading
from qq_wb_msg.msg import qq_login, redis_connect, connect_mongodb,pop_redis_list, get_msg, load_mongodb

from log.views import log_setting
from log.rtx import rtx,get_ip
from qq_wb_msg.models import ThreadMsg

# from log.rtx import rtx


#单例模式
# class Singleton(type):
#     def __init__(cls, name, bases, dict):
#         super(Singleton, cls).__init__(name, bases, dict)
#         cls._instance = None
#     def __call__(cls, *args, **kw):
#         if cls._instance is None:
#             cls._instance = super(Singleton, cls).__call__(*args, **kw)
#         return cls._instance

class Spider(threading.Thread):
    # __metaclass__ = Singleton
    thread_stop = False
    thread_num = 0
    interval = 0
    behavior = None
    def run(self):
        self.behavior(self,self.thread_num,self.interval)
    def stop(self):
        self.thread_stop = True

class ThreadControl():
    thread_stop = False
    current_thread = {}
    def start(self,thread_num,interval):
        spider = Spider()
        spider.behavior = loaddata
        spider.thread_num = thread_num
        spider.interval = interval
        spider.start()
        self.current_thread[str(thread_num)] = spider
    #判断进程是否活跃
    def is_alive(self,thread_num):
        tt = self.current_thread[str(thread_num)]
        return tt.isAlive()
    #获取当前线程名称
    # def get_name(self):
    def stop(self,thread_num):
        print "stop"
        spider = self.current_thread[str(thread_num)]
        spider.stop()

def loaddata(c_thread,thread_num,interval):
    log_name_title = "tencent_wb_msg_"
    ip = get_ip()
    base_date = time.strftime("%Y%m%d", time.localtime())
    log = log_setting(log_name_title + base_date + ".log")
    log.info("run......")
    driver = qq_login()
    time.sleep(3)

    if driver == None :
        log.info("phantomjs error!quit")
        return 0
    else:
        pass
    #出队
    conn_redis = redis_connect()
    conn_mongo = connect_mongodb()

    if conn_redis == 0 or conn_mongo == 0:
        log.info("redis or mongodb connect error")
    else:
        log.info("connect redis ok")
        log.info("connect mongodb ok")
        while not c_thread.thread_stop:
            current_date = time.strftime("%Y%m%d", time.localtime())
            if current_date == base_date:
                pass
            else:
                base_date = current_date
                log = log_setting(log_name_title + base_date + ".log")
            log.info('Thread:(%s)'%(thread_num))
            url = pop_redis_list(conn_redis)
            #判断队列是否为空
            if url == None:
                log.info("msg queue is NULL")
                break
            else:
                #获取详细信息
                msg = get_msg(driver,url,log)
                # print "load to mongodb"
                try:
                    load_mongodb(conn_mongo,url,msg)
                except:
                    rtx('ip',ip+ "机器mongodb失败")
                    log.info('ip' + ip + "机器mongodb失败")
                    log.info("mongodb error")
                    break
        # rtx('IP','正常停止')
        log.info(thread_num + "quit phantomjs")
        driver.quit()
        #rtx提醒
        rtx('ip',ip+ "机器" + thread_num +"停止运行")
        log.info('ip'+ ip + "机器" + thread_num + "停止运行")
        #数据库状态更新,根据线程名称
        log.info("更新数据库线程状态")
        thread = ThreadMsg.objects.get(thread_name=thread_num)
        thread.thread_status = 0
        thread.save()
