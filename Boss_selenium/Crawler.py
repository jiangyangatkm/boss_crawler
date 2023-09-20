import json
import os
import time
import urllib

from lxml import etree
from selenium.webdriver.common.by import By

import WebdriverHelper
from CrawlerInterface import IPipeItem
from CrawlerRedisHelper import CrawlerRedisHelper


def first(node_list):
    """
    获取列表的第一个节点
    """
    if len(node_list) > 0:
        return node_list[0]
    else:
        return ''


class CrawlerPipe(IPipeItem):
    _pipe_item_queue = []

    def execute(self):
        for pipe_item in self._pipe_item_queue:
            pipe_item.execute()

    def add_item(self, item: IPipeItem):
        self._pipe_item_queue.append(item)

    def remove_item(self, item: IPipeItem):
        self._pipe_item_queue.remove(item)

    def get_item(self, index):
        return self._pipe_item_queue[index]

    def clear(self):
        self._pipe_item_queue.clear()


class DelayItem(IPipeItem):
    """
    延时，单位1s
    """
    delay = 1

    def __init__(self, delay=1):
        self.delay = delay

    def execute(self):
        time.sleep(self.delay)


class GeneralPageCrawler(IPipeItem):
    """
    概要页爬取器
    """
    name = None
    is_delete_table = False
    url_base = 'https://www.zhipin.com/web/geek/job?'
    params = {}
    urls = None  # 保存生存的url列表
    page_num = 10  # 翻页总数

    driver = None
    redis_db = None

    def __init__(self, name, is_delete_table=False):
        self.name = name
        self.is_delete_table = is_delete_table
        self.driver = WebdriverHelper.start_webdriver()
        self.redis_db = CrawlerRedisHelper()
        self.params = {
            'city': 101270100,  # 成都
            'degree': 203,  # 本科
            'scale': 306,  # 10000以上
            'jobType': 1901,  # 全职
            'salary': 406,  # 20~50K
            }

    def create_urls(self, num: 1):
        """
        创建boss网站上符合过滤条件的职位列表页面的url
        :param num: 要获取的页面数目
        :return: 职位列表页面的url集合
        """
        urls = []
        for i in range(num):
            self.params['page'] = i + 1  # 添加页面查询条件
            urls.append(self.url_base + urllib.parse.urlencode(self.params))
        return urls

    def open_first_url(self, url):
        start_window = self.driver.current_window_handle
        # 用js打开链接
        WebdriverHelper.open_url_by_js(self.driver, url)
        # 等待1s
        time.sleep(1)
        # 等待所有页面打开完成
        WebdriverHelper.wait_all_pages_complete(self.driver)
        # 查找目标页面
        for wh in self.driver.window_handles:
            self.driver.switch_to.window(wh)
            if self.driver.current_url == url:
                break
        # 获得页面数
        nodes = self.driver.find_elements(by=By.XPATH, value='//div[@class="options-pages"]/a')
        max_page_code = 0
        for node in nodes:
            if node.text.isdigit():
                if max_page_code < int(node.text):
                    max_page_code = int(node.text)
        # 切换回start页面
        self.driver.switch_to.window(start_window)
        return max_page_code

    def execute(self):
        self.urls = self.create_urls(self.page_num)
        # 打开第一个页面并获取页面总数
        WebdriverHelper.open_start_page(self.driver)
        page_num = min(self.open_first_url(self.urls[0]), self.page_num)
        # 如果页面数小于1，则关闭所有页面并返回
        if page_num < 1:
            WebdriverHelper.close_all_pages(self.driver)
            return
        # 打开所有页面
        for url in self.urls[1:page_num - 1]:
            # 用js打开链接
            WebdriverHelper.open_url_by_js(self.driver, url)
            # 等待1s
            time.sleep(1)
        # 等待所有页面打开完成
        WebdriverHelper.wait_all_pages_complete(self.driver)
        # 删除原表
        if self.is_delete_table is True:
            self.redis_db.delete_table(self.name)
        # 将页面保存到redis
        for wh in self.driver.window_handles:
            self.driver.switch_to.window(wh)
            if self.urls.__contains__(self.driver.current_url):
                self.redis_db.save_page(self.name, self.driver.current_url, str.encode(self.driver.page_source))
        # 关闭所有页面
        WebdriverHelper.close_all_pages(self.driver)


class GeneralPageParser(IPipeItem):
    """
    解析页面数据，提取详细页面的url列表
    """
    from_name = None
    to_name = None
    is_overwrite = False
    redis_db = None
    _file_name = 'boss_detail_urls.json'  # 保存链接数据的文件名

    def __init__(self, from_name, to_name, is_overwrite=False):
        self.from_name = from_name
        self.to_name = to_name
        self.is_overwrite = is_overwrite
        self.redis_db = CrawlerRedisHelper()

    def execute(self):
        # 解析url列表
        urls = {}
        for url, page in self.redis_db.read_all(self.from_name).items():
            # 获取url基路径
            parse_res = urllib.parse.urlparse(url)
            base_path = bytes.decode(parse_res.scheme) + '://' + bytes.decode(parse_res.netloc)
            # 解析相对路径及公司
            html = etree.HTML(bytes.decode(page))
            node_list = html.xpath('//div[@class="search-job-result"]/ul/li/div[1]')
            temp_urls = dict()
            for item in node_list:
                detail_url = base_path + first(item.xpath('./a/@href'))
                company = first(item.xpath('.//div[@class="company-info"]//a/text()'))
                temp_urls[detail_url] = company
            urls.update(temp_urls)
        # 创建文件夹
        is_folder = os.path.isdir(self.to_name)
        if not is_folder:
            os.makedirs(self.to_name)
        # 保存url列表
        url_json = {}
        path_name = self.to_name + r'\\' + self._file_name
        if not self.is_overwrite and os.path.isfile(path_name):
            with open(path_name, 'r') as f:
                url_json = json.load(f)
        url_json.update(urls)  # 自动合并相同的url
        with open(path_name, 'w') as f:
            json.dump(url_json, f)


class DetailPageCrawler(IPipeItem):
    """
    详细页面爬取器
    """
    from_names = []
    to_name = None
    company_filter = []
    is_delete_table = False

    page_num = 20  # 每次打开的页面数量

    driver = None
    redis_db = None

    def __init__(self, from_names: list, to_name, company_filer=[], is_delete_table=False):
        self.from_names = from_names
        self.to_name = to_name
        self.company_filter = company_filer
        self.is_delete_table = is_delete_table
        self.driver = WebdriverHelper.start_webdriver()
        self.redis_db = CrawlerRedisHelper()

    def execute(self):
        # 判断可执行条件
        if len(self.from_names) == 0 or self.to_name is None:
            return
        if self.driver is None or self.redis_db is None:
            return
        # 加载并过滤json中的url
        urls = []
        for from_name in self.from_names:
            with open(from_name + r'\boss_detail_urls.json', 'r') as f:
                temp = json.load(f)
                for url, company in temp.items():
                    if len(self.company_filter) > 0:
                        # 判断是否满足过滤
                        is_match = False
                        for target_company in self.company_filter:
                            if company.__contains__(target_company):
                                is_match = True
                                break
                        # 满足过滤条件，加入urls
                        if is_match:
                            urls.append(url)
                    else:
                        urls.append(url)
        # url分组
        step = self.page_num
        url_groups = [urls[i:i + step] for i in range(0, len(urls), step)]
        # 删除原表
        if self.is_delete_table is True:
            self.redis_db.delete_table(self.to_name)
        # 遍历链接，并保存网页
        for group in url_groups:
            # 打开start_page页，以获得弹窗权限
            WebdriverHelper.open_start_page(self.driver)
            # 打开一组页面
            urls = []
            for url in group:
                urls.append(url)
                # 用js打开链接
                WebdriverHelper.open_url_by_js(self.driver, url)
                # 等待1秒钟
                time.sleep(1)
            # 等待页面加载完毕
            WebdriverHelper.wait_all_pages_complete(self.driver)
            # 保存页面到redis
            for wh in self.driver.window_handles:
                self.driver.switch_to.window(wh)
                if urls.__contains__(self.driver.current_url):
                    self.redis_db.save_page(self.to_name, self.driver.current_url, str.encode(self.driver.page_source))
            # 关闭所有页面
            WebdriverHelper.close_all_pages(self.driver)


class DetailPageParser(IPipeItem):
    """
    解析详细页面数据
    """
    from_names = []
    to_name = None
    is_overwrite = False
    redis_db = None
    _file_name = 'job_info.json'  # 保存工作数据的文件名

    def __init__(self, from_names: list, to_name, is_overwrite=False):
        self.from_names = from_names
        self.to_name = to_name
        self.is_overwrite = is_overwrite
        self.redis_db = CrawlerRedisHelper()

    def execute(self):
        # 从redis加载数据
        page_dict = {}
        for from_name in self.from_names:
            page_dict.update(self.redis_db.read_all(from_name))
        # 遍历页面，获取数据
        job_info = []
        for page in page_dict.values():
            html = etree.HTML(bytes.decode(page))
            job_name = first(html.xpath('//div[@class="job-banner"]//div[@class="name"]/h1/text()'))
            salary = first(html.xpath('//div[@class="job-banner"]//div[@class="name"]/span/text()'))
            experience = first(html.xpath('//div[@class="job-banner"]//p/span/text()'))
            company = first(html.xpath(
                '//div[@class="detail-section-item business-info-box"]//li[@class="company-name"]/text()'))
            scale = first(html.xpath('//div[@class="sider-company"]/p[3]/text()'))
            job_keywords = ','.join(html.xpath('//div[@class="job-box"]//ul[@class="job-keyword-list"]/li/text()'))
            job_describe = ''.join(html.xpath('//div[@class="job-box"]//div[@class="job-sec-text"]/text()'))
            job_dic = {
                'job_name': job_name,
                'salary': salary,
                'experience': experience,
                'company': company,
                'scale': scale,
                'job_keywords': job_keywords,
                'job_describe': job_describe,
            }
            job_info.append(job_dic)
        # 保存数据
        # 创建文件夹
        is_folder = os.path.isdir(self.to_name)
        if not is_folder:
            os.makedirs(self.to_name)
        # 保存url列表
        job_info_to_save = []
        path_name = self.to_name + r'\\' + self._file_name
        if not self.is_overwrite and os.path.isfile(path_name):
            # 加载原来的数据，以防止覆盖
            with open(path_name, 'r') as f:
                job_info_to_save = json.load(f)
        job_info_to_save += job_info
        with open(path_name, 'w') as f:
            json.dump(job_info_to_save, f)
