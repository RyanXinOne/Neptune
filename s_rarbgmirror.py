import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
import selenium.webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import re
from lxml import etree
import threading
import json

#获取cookie
def get_cookie():
    try:
        options = Options()
        #关闭日志
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        #关闭自动测试提示
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        capa = DesiredCapabilities.CHROME
        capa["pageLoadStrategy"] = "none"  # 懒加载模式，不等待页面加载完毕
        try:
            driver = selenium.webdriver.Chrome(options=options, desired_capabilities=capa)
        except WebDriverException:
            return 'ChromeDriver配置错误！\nChromeDriver下载地址：\nhttp://chromedriver.storage.googleapis.com/index.html\n安装步骤：1. 将对应版本的ChromeDriver放至Chrome所在目录；2. 将Chrome所在目录加入环境变量。'
        #设置navigator.webdriver属性为undefined
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            delete navigator.__proto__.webdriver;
            """
        })
        userAgent = driver.execute_script("return navigator.userAgent")
        with open('agent.txt', 'w') as f:
            f.write(userAgent)
        driver.get('http://rarbgmirror.com/threat_defence.php?&defence=1')
        WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CLASS_NAME, "icon-search"))) #显式等待
        driver.execute_script('window.stop()')
        cookies = driver.get_cookies()
        jsonCookies = json.dumps(cookies)
        with open('cookie.json', 'w') as f:
            f.write(jsonCookies)
        driver.close()
    except:
        return 'rarbg初始化失败'
    return 'rarbg初始化完成'
    #print(driver.page_source)

def match(kw,lim,film_only,windows):
    #忽略SSL安全警告
    disable_warnings(InsecureRequestWarning)
    #lim条数转换为页面数
    if lim == 0 or lim > 2500:
        lim = 2500
        page_lim = 100
    else:
        page_lim = (lim - 1) // 25 + 1
    
    try:
        with open('cookie.json', 'r', encoding='utf-8') as f:
            listCookies = json.loads(f.read())
        with open('agent.txt', 'r', encoding='utf-8') as f:
            userAgent = f.read()
    except:
        return '请先完成初始化'
    global sess
    sess = requests.session()
    global headers
    headers = {'User-Agent': userAgent}
    
    for cookie in listCookies:
        sess.cookies.set(cookie['name'],cookie['value'], domain=cookie['domain'], path=cookie['path'])

    if film_only == 0:
        url = 'http://rarbgmirror.com/torrents.php?search=' + kw
    else:
        url = 'http://rarbgmirror.com/torrents.php?search=' + kw + '&category%5B%5D=14&category%5B%5D=48&category%5B%5D=17&category%5B%5D=44&category%5B%5D=45&category%5B%5D=47&category%5B%5D=50&category%5B%5D=51&category%5B%5D=52&category%5B%5D=42&category%5B%5D=46'

    #获取页面总数
    windows.return_info('step 1/2 getpagenum...')
    try:
        r0 = sess.get(url + '&page=100', headers=headers, verify=False)
    except:
        windows.return_info("step error")
        return '未知错误.../错误代码：201'
    so = r0.text
    #open('tmp.html','w').write(so)
    so = etree.HTML(so)
    success = so.xpath('//i[@class=\"icon-search\"]')
    if not success:
        windows.return_info('step failed')
        return '请先完成初始化'
    page_num = so.xpath('//*[@id="pager_links"]/b')
    if page_num:
        page_num = page_num[0]
        page_num = etree.tostring(page_num).decode()
        page_num = int(re.search('\\d+',page_num).group(0))
        if page_num > page_lim:
            page_num = page_lim
    else:
        page_num = 1

    tmp = []
    for x in range(page_num+1):
        tmp.append([])
    
    def sou(a):
        with sep:
            try:
                r = sess.get(url+'&page='+str(a), headers=headers, verify=False)
            except:
                return 0
            source = r.text
            result0 = re.findall('<a onmouseover=".*?onmouseout="return nd.*?href=\"(.*?)\" title=".*?">(.*?)</a>',source)
            for z in range(len(result0)):
                tmp[a].append(result0[z][1] + '---->' + 'http://rarbgmirror.com' + result0[z][0])
    
    windows.return_info("step 2/2 getinfo...")
    threading_list = []
    sep = threading.Semaphore(windows.sep_ceil)  # 线程信号量，锁定数量
    for i in range(1, page_num+1):
        t = threading.Thread(target=sou,args=(i,))
        t.setDaemon(True)
        t.start()
        threading_list.append(t)

    for i in threading_list:
        i.join()

    result1 = []                          #排序
    for x in range(1, page_num+1):
        result1 += tmp[x]

    if len(result1) > lim:
        total = lim
    else:
        total = len(result1)
    res = '共找到' + str(total) + '条结果\n'
    for i in range(total):
        res += '[' + str(i+1) + ']' + result1[i] + '\n'
    
    windows.return_info('step finished')
    return res

def get_download_address(url, windows):
    global sess
    global headers
    windows.return_info('step 1/1 loading...')
    try:
        so = sess.get(url, headers=headers, verify=False).text
    except:
        windows.return_info('step error')
        return '未知错误.../错误代码：202'
    xml = etree.HTML(so)
    terms = xml.xpath("/html/body/table[3]/tr/td[2]/div/table/tr[2]/td/div/table/tr[1]/td[2]//@href")
    if not terms:
        windows.return_info('step failed')
        return '请重新完成初始化.../错误代码：203'
    res = 'BT torrent---->https://rarbgmirror.com/' + terms[0] + '\nmagnet link---->' + terms[1] + '\n'
    windows.return_info('step finished')
    return res


if __name__ == '__main__':
    #get_cookie()
    #print(match('game of thrones',100,0))
    pass
