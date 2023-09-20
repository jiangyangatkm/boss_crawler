import re
import struct


class JobInfo(object):
    name = ''
    salary = 0
    keywords = ''
    describe = ''
    company = ''


class JobAnalyzer(object):
    job_json = None
    job_info_list = []
    salary_keyword_table = None

    min_salary = 200
    max_salary = 1500
    step = 100
    key_salary_table = None  # {薪资区间字串: 薪资区间}

    def __init__(self, job_json):
        # 生成job_info_list
        self.job_json = job_json
        for item in job_json:
            job_info = JobInfo()
            job_info.name = item['job_name']
            job_info.salary = self.parse_salary(item['salary'])
            job_info.keywords = item['job_keywords']
            job_info.describe = self.parse_key_words(item['job_describe'])
            job_info.company = self.parse_company(item['company'])
            self.job_info_list.append(job_info)
        # 生成薪资区间字典
        self.key_salary_table = self.get_key_salary_table()

    def get_key_salary_table(self):
        key_salary_table = {}
        for salary in range(self.min_salary, self.max_salary, self.step):
            key = str(salary) + '~' + str(salary + self.step) + 'K'
            key_salary_table[key] = [salary, salary + self.step]
        return key_salary_table

    def get_salary_key(self, salary):
        salary_lower = self.min_salary + int((salary - self.min_salary) / self.step) * self.step
        key = str(salary_lower) + '~' + str(salary_lower + self.step) + 'K'
        return key

    def get_salary_none_table(self, init_value=None):
        table = {}
        for salary in range(self.min_salary, self.max_salary, self.step):
            key = str(salary) + '~' + str(salary + self.step) + 'K'
            table[key] = init_value
        return table

    def parse_salary(self, str_salary):
        """
        解析薪资字符串
        :param str_salary: 薪资字符串
        :return: 年薪[最小值,最大值,平均值]
        """
        str_salary_list = re.findall(r'\d+', str_salary)
        salary = [0, 0, 0]
        salary_min = 0
        salary_max = 0
        salary_num = 12  # 默认12个月
        # 计算月薪区间
        if len(str_salary_list) == 1:
            salary_max = salary_min = int(str_salary_list[0])
        elif len(str_salary_list) == 2 or 3:
            salary_min = int(str_salary_list[0])
            salary_max = int(str_salary_list[1])
        # 计算薪数
        if len(str_salary_list) == 3:
            salary_num = int(str_salary_list[2])
        # 计算年薪（最低、最高、平均）
        if len(str_salary_list) == 1 or 2 or 3:
            salary[0] = salary_min * salary_num
            salary[1] = salary_max * salary_num
            salary[2] = (salary[0] + salary[1]) / 2

        return salary

    def parse_key_words(self, text):
        """
        解析文本中的关键字
        :param text: 待解析文本
        :return: 解析得到的关键字列表
        """
        words = re.findall(r'[A-Za-z]+[0-9A-Za-z_+]*', text)  # 提取英文单词
        words = list(map(lambda w: w.replace('_', '').strip().lower(), words))  # 删除多余的字符
        ret_words = []
        for word in words:
            if ret_words.__contains__(word) is False:
                ret_words.append(word)

        return ret_words

    def parse_company(self, str_company: str):
        """
        解析公司名称
        :param str_company: 公司名称字符串，可包含其他无用信息
        :return: 公司名称
        """
        target_company_list = ['华为', '腾讯', '字节', '阿里', '美团', '抖音']
        for target_company in target_company_list:
            if str_company.__contains__(target_company):
                return target_company
        return str_company

    def get_all_key_words(self):
        """
        获得所有关键词（去除重复）
        :return: 关键词列表
        """
        # 统计关键字
        all_kw = dict()
        for job_info in self.job_info_list:
            for kw in job_info.describe:
                if all_kw.keys().__contains__(kw) is False:
                    all_kw[kw] = 1
                else:
                    all_kw[kw] += 1
        # 删除出现次数小于等于1的关键字
        del_keys = []
        for key, value in all_kw.items():
            if value <= 1:
                del_keys.append(key)
        for key in del_keys:
            all_kw.pop(key)

        return all_kw

    def get_salary_keyword_table(self):
        all_kw = self.get_all_key_words()
        for key in all_kw.keys():
            all_kw[key] = 0

        # 创建salary_keyword_table表格框架
        min_salary = self.min_salary
        max_salary = self.max_salary
        step = self.step
        salary_keyword_table = {}
        for salary in range(min_salary, max_salary, step):
            key = str(salary) + '~' + str(salary + step) + 'K'
            salary_keyword_table[key] = all_kw.copy()

        # 填写salary_keyword_table
        for job_info in self.job_info_list:
            # 获得薪资key值
            key = self.get_salary_key(job_info.salary[2])
            # 遍历关键字，并更新薪资-关键字表中对应统计值
            for kw in job_info.describe:
                if salary_keyword_table.keys().__contains__(key):
                    if salary_keyword_table[key].keys().__contains__(kw):
                        salary_keyword_table[key][kw] += 1
        # 保存统计结果
        self.salary_keyword_table = salary_keyword_table
        # self.key_salary_table = key_salary_table

        return salary_keyword_table, self.key_salary_table

    def get_top10(self):
        if self.salary_keyword_table is None:
            self.get_salary_keyword_table()
        #  统计各个薪资区间的前10个关键词
        top10_table = {}
        for key, zone in self.salary_keyword_table.items():
            top10 = sorted(zone.items(), key=lambda it: it[1], reverse=True)[:10]
            top10_table[key] = top10
        return top10_table

    def get_job_info_by_word(self, word):
        salary_table = self.get_salary_none_table(0)
        job_num = 0
        for job_info in self.job_info_list:
            # 判断是否包含word
            if job_info.name.__contains__(word) or \
                    job_info.keywords.__contains__(word) or \
                    job_info.describe.__contains__(word):
                key = self.get_salary_key(job_info.salary[2])
                if salary_table.keys().__contains__(key):
                    salary_table[key] += 1
                    job_num += 1
        return salary_table, job_num
