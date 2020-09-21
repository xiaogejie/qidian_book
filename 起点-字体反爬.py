import requests
from fontTools.ttLib import TTFont
from io import BytesIO
from lxml import etree
import re
import pymongo

HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
    }
URL = 'https://www.qidian.com/all?orderId=&style=1&pageSize=20&siteid=1&pubflag=0&hiddenField=0&page=1'


def ziti_jiexi(ziti_url):
    ziti = requests.get(ziti_url, headers=HEADERS)  # 下载ttf字体文件，然后通过BytesIO转化为内存文件，使用TTFont处理
    font = TTFont(BytesIO(ziti.content))
    cmap: dict = font.getBestCmap()
    dic = {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7',
           'eight': '8', 'nine': '9', 'period': '.'}
    new_dict = {}
    for key, value in cmap.items():
        new_dict[key] = dic[value]
    return new_dict


def get_zitiurl(response):
    html = etree.HTML(response)
    a: str = html.xpath('//li[@data-rid="1"]//p[@class="update"]//style/text()')[0]
    c = a.replace(' ', '')

    ziti_url = re.search(r"(?<=format\('woff'\),url\(\')(.*)(?=\'\)format\('truetype'\))", c).group(1)
    return ziti_url


def jiexi_html():
    '''
    在获取到html中时， 直接将被替换的文本解析出来
    :return: 被解析完的 response.text 文件
    '''
    _response = requests.get(URL, headers=HEADERS).text
    ziti_dict = ziti_jiexi(get_zitiurl(_response))
    response = _response.replace('&#', '').replace(';', '')
    for key, value in ziti_dict.items():
        response = response.replace(str(key), value)

    return response


def get_info(response):
    html = etree.HTML(response)
    items = html.xpath('//div[@class="all-book-list"]//li')
    for item in items:
        # 书籍详情地址
        info_url = item.xpath('./div[@class="book-img-box"]/a/@href')
        # 书籍简介
        name = item.xpath('./div[@class="book-mid-info"]/h4/a/text()')[0]
        author = item.xpath('./div[@class="book-mid-info"]/p[@class="author"]/a[@class="name"]/text()')[0]
        cate_1 = item.xpath('./div[@class="book-mid-info"]/p[@class="author"]/a[2]/text()')[0]
        cate_2 = '-'
        cate_3 = item.xpath('./div[@class="book-mid-info"]/p[@class="author"]/a[3]/text()')[0]
        cate = cate_1 + cate_2 + cate_3
        state = item.xpath('./div[@class="book-mid-info"]/p[@class="author"]/span/text()')[0]
        unit = item.xpath('./div[@class="book-mid-info"]/p[@class="update"]/span/text()')[0]
        nums = item.xpath('./div[@class="book-mid-info"]/p[@class="update"]/span/span/text()')[0]
        print(name, author, cate, state, nums+unit)
        yield {'书名': name, '作者': author, '类别': cate, '连载状态': state, '字数': nums+unit, '详细地址': info_url}


def save_mongodb(data):
    mongo_url = '192.168.234.128'
    mongo_db = 'qidian'

    client = pymongo.MongoClient(mongo_url)
    db = client[mongo_db]
    colletion = db['qidian_book']

    try:
        colletion.insert_many(data)
    except Exception as e:
        print('写入mongodb失败', e)


if __name__ == '__main__':
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
    }
    # 最多只能获取5页
    for i in range(1, 6):
        print('第{}页开始获取'.format(i))
        URL = 'https://www.qidian.com/all?page={}'.format(i)

        response = jiexi_html()

        data = get_info(response)
        save_mongodb(data)