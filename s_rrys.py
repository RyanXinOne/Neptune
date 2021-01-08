import requests
from lxml import etree
import re
import threading
import json

global rootURL
rootURL = ''

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

def search(key, mode, windows):
    #获取rrys可能不定变换的url
    global rootURL
    if not rootURL:
        windows.return_info('step 0/2 geturl...')
        try:
            source = requests.get('http://www.rrys.tv/', headers=headers).text
            rootURL = re.findall('window\\.location\\.href="(.*)/"', source)[0]
        except:
            windows.return_info('step error')
            return '未知错误.../错误代码：301'
    
    #搜索模式，0为影视，1为字幕
    if mode == 0:
        mode = 'resource'
    else:
        mode = 'subtitle'
    
    url = rootURL+'/search?keyword='+key+'&type='+mode
    windows.return_info('step 1/2 getinfo...')
    try:
        source = requests.get(url,headers=headers).text
    except:
        windows.return_info('step error')
        return '未知错误.../错误代码：302'
    so = etree.HTML(source)

    #获取页数
    page_num = so.xpath('/html/body/div[2]/div/div[1]/div/div[3]/div')
    page_num = etree.tostring(page_num[0]).decode()
    page_num = re.findall('\\.\\.\\.(\\d+)', page_num)
    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num[0])

    #结果条目列表
    terms = []
    for i in range(page_num):
        terms.append([])

    #首页条目加入列表
    elements = so.xpath('//strong[@class="list_title"]/..')
    for i in elements:
        url_ = rootURL + i.attrib['href']
        i = etree.tostring(i,encoding='utf-8').decode()
        i = re.findall('<a href=.*?><strong class="list_title">(.*?)</strong>(.*?)</a>', i)
        i = i[0][0] + i[0][1]
        try:
            i = i.replace('<strong class="f1">','')
            i = i.replace('</strong>','')
        except:
            pass
        terms[0].append(i + '---->' + url_)

    #加载更多页内容
    windows.return_info('step 2/2 getmoreinfo...')
    if page_num > 1:
        def sou(a):
            with sep:
                try:
                    source = requests.get(url+'&page='+str(a),headers=headers).text
                except:
                    return 0
                so = etree.HTML(source)
                elements = so.xpath('//strong[@class="list_title"]/..')
                for j in elements:
                    url_ = rootURL + j.attrib['href']
                    j = etree.tostring(j,encoding='utf-8').decode()
                    j = re.findall('<a href=.*?><strong class="list_title">(.*?)</strong>(.*?)</a>', j)
                    j= j[0][0] + j[0][1]
                    try:
                        j = j.replace('<strong class="f1">','')
                        j = j.replace('</strong>','')
                    except:
                        pass
                    terms[a-1].append(j + '---->' + url_)
        
        threading_list = []
        sep = threading.Semaphore(windows.sep_ceil)  # 线程信号量，锁定数量
        for i in range(2, page_num+1):
            t = threading.Thread(target=sou,args=(i,))
            t.setDaemon(True)
            t.start()
            threading_list.append(t)

        for i in threading_list:
            i.join()
            
    result1 = []                          #排序
    for x in range(0, page_num):
        result1 += terms[x]

    total = len(result1)
    res = '共找到' + str(total) + '条结果\n'
    for i in range(total):
        res += '[' + str(i+1) + ']' + result1[i] + '\n'
    
    windows.return_info('step finished')
    return res

def get_download_address(url, windows):
    movie_id = re.findall('resource/(\\d+)$', url)[0]
    windows.return_info('step 1/2 getResourceCode...')
    address_link = rootURL + '/resource/index_json/rid/' + movie_id + '/channel/movie'  #拼出包含资源下载页链接的js请求
    try:
        source = requests.get(address_link, headers=headers).text
    except:
        windows.return_info('step error')
        return '未知错误.../错误代码：303'
    if r'\u70b9\u51fb\u67e5\u770b\u672c\u7247\u5168\u90e8\u8d44\u6e90\u4e0b\u8f7d\u9875' in source:  #判断是否存在资源下载页
        address_link = re.findall('href=\\\\"(.*?)\\\\"', source)[0].replace('\\','')  #解析出下载地址页链接
        address_link = address_link.replace('/resource.html', '/api/v1/static/resource/detail')  #拼出ajax请求json格式资源数据地址
        windows.return_info('step 2/2 getResources...')
        try:
            source = requests.get(address_link, headers=headers).text
        except:
            windows.return_info('step error')
            return '未知错误.../错误代码：304'
        resource_info = json.loads(source)
        try:
            res = ''
            for item in resource_info['data']['list']:  #item为list列表中字典(正常仅1个)
                for group, value in item['items'].items():  # group为资源类型组
                    res += group + '：---->\n'
                    for resource in value:  # resource为单个资源
                        name = resource['name']
                        size = resource['size']
                        res += ' '*8 + name + '  ' + size + '---->\n'
                        files = resource['files']
                        if group == 'APP':
                            res += ' '*16 + '人人下载器---->' + name + '\n'
                        if files:
                            for file in files:  #file为单个下载方式及链接
                                if file['passwd']:
                                    res += ' '*16 + file['way_cn'] + '  密码：' + file['passwd'] + '---->' + file['address'] + '\n'
                                else:
                                    res += ' '*16 + file['way_cn'] + '---->' + file['address'] + '\n'
        except:
            windows.return_info('step error')
            return 'rrys资源解析错误.../错误代码：305'
        windows.return_info('step finished')
        return res
    else:
        windows.return_info('step failed')
        return '可能由于版权原因，该资源暂时无法提供下载链接。---->\n'

def zimuzu_download_address(url, windows):
    windows.return_info('step 1/2 getResourceLink...')
    try:
        source = requests.get(url, headers=headers).text
    except:
        windows.return_info('step error')
        return '未知错误.../错误代码：306'
    so = etree.HTML(source)
    resourceLink = so.xpath('//div[@class="subtitle-links tc"]/a/@href')[0]  #解析出下载地址页链接
    resourceLink = resourceLink.replace('/subtitle.html', '/api/v1/static/subtitle/detail')  #拼出ajax请求json格式资源数据地址
    windows.return_info('step 2/2 getResources...')
    try:
        source = requests.get(resourceLink, headers=headers).text
    except:
        windows.return_info('step error')
        return '未知错误.../错误代码：307'
    resource_info = json.loads(source)
    res = ''
    res += resource_info['data']['info']['category'] + ' ' + resource_info['data']['info']['cnname'] + ' ' + resource_info['data']['info']['enname'] + '---->\n'
    res += resource_info['data']['info']['filename'] + '---->' + resource_info['data']['info']['file'] + '\n'
    windows.return_info('step finished')
    return res

if __name__ == "__main__":
    rootURL = 'http://www.rrys2020.com'
    zimuzu_download_address('http://www.rrys2020.com/subtitle/60710', None)
