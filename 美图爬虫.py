import requests
import os
import datetime,time
import threading
from queue import Queue
from bs4 import BeautifulSoup
from tqdm import tqdm

class ThreadPoolController(object):
    """线程池管理类,可以生成、启动或终止一个线程池"""
    def __init__(self, thread_pool_name, thread_number=1):
        """thread_pool_name参数是要开启的threading.Thread子类,thrad_number当然是生成的线程数,也就是线程池中的线程数目。初始化时生成线程池"""
        self.thread_pool_name = thread_pool_name
        self.thread_number = thread_number
        self.thread_list = []    #用于存放线程池中的线程,便于管理调用的操作,其实就是方便找到属于这个线程池的线程,对于本例,就是为了调用下面的off方法stop掉属于该线程池的线程
        for i in range(self.thread_number):
            self.thread_list.append(self.thread_pool_name())
    def on(self):    #启动线程池中的所有线程,线程开始工作
        for i in self.thread_list:
            i.start()
    def off(self):    #用于终止线程池内的所有线程
        for i in self.thread_list:
            i.stop()


class RequetsThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True    #覆盖父类变量成员,设为True表示为守护线程,主线程结束自动终止此线程
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            while not url_queue.empty():
                title,url = url_queue.get()
                try:
                    response = requests.get(url, headers=headers,proxies=proxies)
                    max_span = int(BeautifulSoup(response.text,'lxml').find(attrs={'id':'pages'}).find_all('a')[-2].get_text())
                    for i in range(1,max_span+1):
                        newUrl = url
                        if i!=1:
                            newUrl = url+str(i)+'.html'
                        newResponse = requests.get(newUrl, headers=headers,proxies=proxies)
                        img_url = BeautifulSoup(newResponse.text,'lxml').find('div',class_ ='content').find('img').get('src')
                        img_response = requests.get(img_url, headers=headers,proxies=proxies)
                        picture_url_and_response_queue.put((title,img_url,img_response))

                    print("{}: 已完成请求{}".format(self.name,title+'>>>>>>>>>'+url))
                except:
                    print("发生错误1")

    def stop(self):
        self.stop_flag = True



class DownloadThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            while not picture_url_and_response_queue.empty():
                try:
                    title,url,response = picture_url_and_response_queue.get()
                    #img_url = BeautifulSoup(response.text,'lxml').find('div',class_ ='main-image').find('img').get('src')
                    self.mkdir(downloadPath+title)
                    name = downloadPath+title+'/'+url.split('/')[-1]
                    #response = requests.get(img_url, headers=headers,proxies=proxies)
                    with open(name,'wb') as f:
                        f.write(response.content)
                except:
                    print("发生错误2")

    def mkdir(self, path):
        #path = 'D:/11MM/'+ path.strip()
        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)
            print(u'已建立 ', path, u'的文件夹')

    def stop(self):
        self.stop_flag = True




if __name__ == '__main__':

    url_queue = Queue()#创建队列，用于存放每组图的url地址,存入的为元组。为标题与url组合
    picture_url_and_response_queue = Queue()#创建队列，用于存放每张图片的URL网址。为标题与URL与response组合
    #picture_download_url_queue = Queue()#创建队列，用于存放每张图片的URL下载地址。为标题与URL组合

    #headers设置"User-Agent"用于伪装成普通的浏览器
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    # 填写代理
    proxies={
        #'https':'221.7.255.168:80'
    }

    url = 'https://www.meituri.com/zhongguo/'
    downloadPath = 'D:/11MM/'
    date_day=datetime.date.today()
    response = requests.get(url,headers=headers,proxies=proxies)
    response.encoding = 'utf-8'  # 解决BeautifulSoup中文乱码问题
    max_span = BeautifulSoup(response.text,'lxml').find('div',id='pages').find_all('a')
    groupAll = int(max_span[0].text[:-1])#总组数
    print('''注意事项：
    1、截至目前（%s），妹子图网站共计有%s组妹子套图...
    2、每组不到5M，请自行选择下载..
    3、将从最新日期的的套图开始下载...
    4、本文件将放入 D:/11MM 文件夹下面 \n'''%(date_day,groupAll))
    allNum=input('请输入需要下载的组数：')
    while not allNum.isdigit() or int(allNum)<=0:
        allNum = input('输入有误，请重新输入需要下载的组数(需大于0)：')
    allNum = int(allNum)
    ratio = 40  # 每页有40组妹子图片
    mod = allNum%ratio
    pagination = allNum//ratio#计算需要下载的组数在网站中多少页
    #余数不为0，说明还要加上一页
    if mod != 0 :
        pagination += 1
    startTime = time.time()
    print('正在进行任务分配...')
    for i in tqdm(range(1,pagination+1)):
        yeUrl = 'https://www.meituri.com/zhongguo/'
        if i!=1:
            yeUrl = 'https://www.meituri.com/zhongguo/' + str(i) + '.html'
        response = requests.get(yeUrl,headers=headers,proxies=proxies)
        response.encoding = 'utf-8' #解决BeautifulSoup中文乱码问题
        pAll = BeautifulSoup(response.text, 'lxml').find_all(attrs={"class":'hezi'})[1].find_all(attrs={'class':'biaoti'})
        for p in pAll:
            # 判断是否为最后一页解析
            if i == pagination:
                # 判断有没有余数
                if mod == 0:
                    url_queue.put((p.text, p.contents[0]['href']))
                else:
                    # 判断当前a标签的下标是否超过了余数
                    if pAll.index(p) < mod:
                        url_queue.put((p.text, p.contents[0]['href']))
            else:
                url_queue.put((p.text, p.contents[0]['href']))

    url_request_thread_pool = ThreadPoolController(RequetsThread,50)    #生成50个用于页面请求任务的线程的线程池
    download_thread = DownloadThread()
    time.sleep(1)
    print('已成功分配任务...')
    url_request_thread_pool.on()
    download_thread.start()

    while True:
        #由于该网站解析速度较慢，设置睡眠时间长点，否则会提前结束线程
        time.sleep(50)
        if url_queue.empty() and picture_url_and_response_queue.empty():
            break

    url_request_thread_pool.off()
    download_thread.stop()
    download_thread.join()
    print("已运行完毕 ")
    print("本次爬取时间为%d" % (time.time() - startTime))



