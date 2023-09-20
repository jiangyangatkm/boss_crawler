import datetime
import json
import os
import time
import urllib.parse
import redis
from BossCrawler import BossCrawler
from Crawler import GeneralPageCrawler
from JobAnalyzer import JobAnalyzer

from selenium import webdriver
import re
import Test


if __name__ == '__main__':
    # Test.test_webdriver_helper()
    # Test.test_crawler_redis_helper()
    # Test.test_general_page_crawler()
    # Test.test_general_page_parser()
    # Test.test_detail_page_crawler()
    # Test.test_detail_page_parser()
    # Test.test_giant_flow()
    Test.test_job_analyzer()
    pass
