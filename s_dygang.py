import requests
import urllib.parse
import re
from lxml import etree
import threading

def match(key, windows):
    data = {"keyboard": key}
    data = urllib.parse.urlencode(data, encoding='gbk')
    data = "tempid=1&tbname=article&" + data + "&show=title%2Csmalltext&Submit=%CB%D1%CB%F7"
    data = data.encode('gbk')

    headers = {'Accept-Encoding': 'identity',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(data)),
            'Host': 'so.dygang.com',
            "Referer": "http://www.dygang.com/",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
            }

    url = 'http://so.dygang.com/e/search/index.php'

    windows.return_info("step 1/2 getinfo...")
    #post并获取首页
    try:
        response = requests.post(url, headers=headers, data=data)
        response.encoding = 'gbk'
        sid = re.findall("searchid=(\\d*)", response.url)[0]         # 获取搜索id
        words = response.text                                        # 获取文本
    except:
        windows.return_info("step error")
        return '未知错误.../错误代码：101'

    if sid == '0':
        windows.return_info('step 2/2 nomoreinfo')
        windows.return_info('step finished')
        return '共找到0条结果\n'
    
    content = ['']
    content[0] = re.findall("<a.*?classlinkclass.*?</a>", words)         #首页结果

    all_num = re.findall("<a title=\"总数\">&nbsp;<b>(\\d*)</b> </a>", words)    #检查是否有更多页
    if all_num:
        all_num = int(all_num[0])
    else:
        all_num = len(content[0])

    if all_num > 20:             #检索更多页
        for i in range(1, all_num // 20 + 1):
            content.append([])

        def sou(i):                  #如果结果有多页，则进行循环
            with sep:
                url = "http://so.dygang.com/e/search/result/index.php?page="+str(i)+"&searchid="+sid
                headers = {"Referer": "http://www.dygang.com/",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
                        }
                try:
                    response = requests.get(url, headers=headers)
                    response.encoding = 'gbk'
                    words = response.text
                except:
                    words = ''
                content[i] = re.findall("<a.*?classlinkclass.*?</a>", words)

        windows.return_info('step 2/2 getmoreinfo...')
        sep = threading.Semaphore(windows.sep_ceil)  #线程信号量，锁定数量
        threading_list = []
        for i in range(1, all_num // 20 + 1):
            t = threading.Thread(target=sou,args=(i,))
            t.setDaemon(True)
            t.start()
            threading_list.append(t)

        for i in threading_list:
            i.join()
    else:
        windows.return_info('step 2/2 nomoreinfo')

    result1 = []
    for i in range(all_num // 20 + 1):
        result1 += content[i]                 # 排序得到的结果

    res = "共找到" + str(all_num) + "条结果"
    if len(result1) < all_num:
        res += "（部分结果可能因网络或解码错误显示不全）\n"
    else:
        res += "\n"
    for i in range(len(result1)):
        result = re.findall("href=\"(.*?)\".*?>(.*?)</a>", result1[i])
        res = res + '[' + str(i + 1) + ']' + result[0][1] + '---->' + result[0][0] + '\n'

    windows.return_info('step finished')
    return res

def get_download_address(url, windows):
    headers = {"Referer": "http://www.dygangs.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
            }
    windows.return_info('step 1/1 loading...')
    try:
        response = requests.get(url, headers=headers)
    except:
        windows.return_info('step error')
        return '未知错误.../错误代码：102'
    response.encoding = 'gbk'
    words = response.text
    terms = re.findall('(<td.*?bgcolor="#ffffbb".*?</td>)', words)
    if not terms:
        terms = re.findall('(<td.*?bgcolor="#ddedfb".*?</td>)', words)
    res = ''
    for term in terms:
        xml = etree.HTML(term)
        text = xml.xpath('//text()')
        text = ''.join(text)
        href = xml.xpath('//@href')
        if not href:
            res += text + '---->\n'
        elif len(href) == 1:
            res += text + '---->' + href[0] + '\n'
        else:
            res += text + '---->\n'
            for h in href:
                res += ' ---->' + h + '\n'
    windows.return_info('step finished')
    return res

#print(get_download_address('http://www.dygangs.com/dyzt/20190903/43310.htm'))
