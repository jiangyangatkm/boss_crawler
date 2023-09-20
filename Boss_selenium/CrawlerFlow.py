from Crawler import GeneralPageCrawler, CrawlerPipe, DelayItem, GeneralPageParser, DetailPageCrawler, DetailPageParser
from CrawlerInterface import IPipeItem


class GiantFlow(IPipeItem):
    """
    巨头公司的爬取流程
    """
    name = 'Giant'
    detail_name = 'Giant_Detail'
    company_filter = ['华为', '腾讯', '字节', '阿里', '美团', '抖音', '头条']

    def gen_general_crawler(self, industry, salary):
        """
        生成概要网页爬取器
        """
        crawler = GeneralPageCrawler(name=self.name)
        crawler.params['industry'] = industry
        crawler.params['salary'] = salary
        return crawler

    def execute(self):
        # 创建流程
        pipe = CrawlerPipe()
        # 创建概要页爬取器
        for i in range(100001, 100027 + 1):
            for s in range(406, 407 + 1):
                pipe.add_item(self.gen_general_crawler(i, s))
                pipe.add_item(DelayItem())
        pipe.get_item(0).is_delete_table = True
        # 创建概要页解析器
        paser = GeneralPageParser(from_name=self.name, to_name=self.name, is_overwrite=True)
        pipe.add_item(paser)
        # 创建详细页爬取器
        crawler = DetailPageCrawler(
            from_names=[self.name], to_name=self.detail_name, company_filer=self.company_filter, is_delete_table=True)
        pipe.add_item(crawler)
        # 创建详细页解析器
        detail_parser = DetailPageParser(from_names=[self.detail_name], to_name=self.name, is_overwrite=True)
        pipe.add_item(detail_parser)

        pipe.execute()
