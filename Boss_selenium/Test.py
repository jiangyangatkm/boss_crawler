import json
import time

import WebdriverHelper
from Crawler import GeneralPageCrawler, GeneralPageParser, DetailPageCrawler, DetailPageParser
from CrawlerFlow import GiantFlow
from CrawlerRedisHelper import CrawlerRedisHelper
from JobAnalyzer import JobAnalyzer


def test_webdriver_helper():
    driver = WebdriverHelper.start_webdriver()
    WebdriverHelper.open_start_page(driver)
    WebdriverHelper.open_url_by_js(driver, 'https://www.baidu.com')
    WebdriverHelper.wait_all_pages_complete(driver)
    time.sleep(5)
    WebdriverHelper.close_all_pages(driver)


def test_crawler_redis_helper():
    dbh = CrawlerRedisHelper()
    dbh.save_pages('test1', {'t1': 'p1', 't2': 'p2', 't3': 'p3'})
    dbh.save_page('test1', 't4', 'p4')
    print(dbh.read_page('test1', 't3'))
    print(dbh.read_pages('test1', ['t3', 't4']))
    print(dbh.read_all('test1'))
    dbh.delete_table('test1')
    print(dbh.read_all('test1'))


def test_general_page_crawler():
    crawler = GeneralPageCrawler('test1', True)
    crawler.execute()
    rh = CrawlerRedisHelper()
    print(bytes.decode(list(rh.read_all('test1').values())[0]))


def test_general_page_parser():
    paser = GeneralPageParser('test1', 'test1')
    paser.execute()
    with open('./test1/boss_detail_urls.json', 'r') as f:
        urls = json.load(f)
    print(len(urls))
    i = 0
    for url, company in urls.items():
        if i == 10:
            break
        print(url)
        print(company)
        i += 1


def test_detail_page_crawler():
    crawler = DetailPageCrawler(from_names=['test1'], to_name='test1_detail', company_filer=['华为'], is_delete_table=True)
    crawler.execute()
    rh = CrawlerRedisHelper()
    print(bytes.decode(list(rh.read_all('test1_detail').values())[0]))


def test_detail_page_parser():
    parser = DetailPageParser(from_names=['test1_detail'], to_name='test1', is_overwrite=True)
    parser.execute()
    with open('./test1/job_info.json', 'r') as f:
        job_info_list = json.load(f)
    for i, job_info in enumerate(job_info_list):
        if i == 10:
            break
        print(job_info)


def test_giant_flow():
    flow = GiantFlow()
    flow.execute()
    # 打印url信息
    with open('./Giant/boss_detail_urls.json', 'r') as f:
        urls = json.load(f)
    print(len(urls))
    i = 0
    for url, company in urls.items():
        if i == 10:
            break
        print(url)
        print(company)
        i += 1
    # 打印数据库信息
    rh = CrawlerRedisHelper()
    print('db=' + str(len(rh.read_all('Giant_Detail').values())))
    # 打印职位信息
    with open('./Giant/job_info.json', 'r') as f:
        job_info_list = json.load(f)
    print('job_info=' + str(len(job_info_list)))
    for i, job_info in enumerate(job_info_list):
        if i == 10:
            break
        print(job_info)


def test_job_analyzer():
    data = []
    with open('./Giant/job_info.json', 'r') as f:
        data = json.load(f)
    analyzer = JobAnalyzer(data)
    # 统计不同薪资区间前十的关键词
    top10 = analyzer.get_top10()
    for salary, words in top10.items():
        print(salary + ":" + str(words))
    # 统计包含'云'的职位信息
    kw_salary, job_num = analyzer.get_job_info_by_word('云')
    print('云:job_num:' + str(job_num))
    print(kw_salary)
    # 统计包含'算法'的职位信息
    kw_salary, job_num = analyzer.get_job_info_by_word('算法')
    print('算法:job_num:' + str(job_num))
    print(kw_salary)
