from abc import abstractmethod, ABCMeta


class ICrawlerDbHelper(metaclass=ABCMeta):
    """
    页面抓取器的数据库操作接口
    """

    @abstractmethod
    def create_table(self, name):
        """
        创建表
        :param name: 表名
        """
        pass

    @abstractmethod
    def delete_table(self, name):
        """
        删除表
        :param name: 表名
        """
        pass

    @abstractmethod
    def save_page(self, name, url, page_code):
        """
        保存页面
        :param name: 表名
        :param url: url
        :param page_code: 页面源码
        """
        pass

    @abstractmethod
    def save_pages(self, name, page_dict: dict):
        """
        保存页面组
        :param name: 表名
        :param page_dict: 页面组
        """
        pass

    @abstractmethod
    def read_page(self, name, url):
        """
        读取页面
        :param name: 表名
        :param url: url
        """
        pass

    @abstractmethod
    def read_pages(self, name, urls: list) -> list:
        """
        读取页面组
        :param name: 表名
        :param urls: 页面组
        """
        pass

    @abstractmethod
    def read_all(self, name) -> list:
        """
        读取所有页面
        :param name: 表名
        """
        pass


class IPipeItem(metaclass=ABCMeta):

    @abstractmethod
    def execute(self):
        """
        PipeItem的回调接口，通过该接口执行业务
        """
        pass


def singleton(cls):
    """
    单例修饰器
    :param cls:
    :return:
    """
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]
    return inner
