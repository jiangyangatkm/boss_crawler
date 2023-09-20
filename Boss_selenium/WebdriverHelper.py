import os
import time

from selenium import webdriver
import psutil


def path2url(pathname: str):
    """
    将文件路径转换为url
    :param pathname: 文件路径
    :return: url
    """
    return 'file:///' + os.path.abspath(pathname).replace('\\', '/')


def is_chrome_running():
    """
    判断chrome是否在正在运行
    :return:
    """
    for proc in psutil.process_iter(['pid', 'name']):
        if 'chrome.exe' in proc.name():
            return True
    return False


_driver = None


def start_webdriver():
    """
    返回webdriver
    :return: webdriver
    """
    global _driver
    # 启动浏览器
    if not is_chrome_running():
        os.startfile(r"C:\Users\Public\Desktop\Google Chrome.lnk")
    # 启动webdriver
    if _driver is None:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        _driver = webdriver.Chrome(options=options)
    return _driver


def close_all_pages(driver: webdriver):
    """
    关闭所有页面
    :param driver: webdriver实例
    """
    # 打开一个新窗口，并记录窗口句柄
    driver.switch_to.new_window('New Page')
    new_page_wh = driver.current_window_handle
    # 关闭新页面以外的所有页面
    for wh in driver.window_handles:
        if wh != new_page_wh:
            driver.switch_to.window(wh)
            driver.close()
    # 将窗口切换到新建的窗口
    driver.switch_to.window(new_page_wh)


def wait_all_pages_complete(driver: webdriver, timeout=10):
    """
    等待所有页面加载完成
    :param driver: webdriver实例
    :param timeout: 等待超时时长
    :return: 超时时间内，所有页面是否加载完成
    """
    for i in range(timeout):
        # 每隔1s扫描一次
        time.sleep(1)
        # 扫描所有页面的完成状态
        is_all_complete = True
        for wh in driver.window_handles:
            driver.switch_to.window(wh)
            if driver.execute_script('return document.readyState') != 'complete':
                is_all_complete = False
                break
        # 所有页面完成，则退出扫描
        if is_all_complete:
            break
    return is_all_complete


def open_start_page(driver: webdriver):
    """
    打开启动页面，以获得弹窗权限
    :param driver:
    """
    driver.get(url=path2url('start_page.html'))


def open_url_by_js(driver: webdriver, url):
    """
    用js打开页面（反爬需要）
    :param driver: webdriver实例
    :param url: 要打开的url
    """
    str_js = 'window.open("%url", "_blank")'.replace('%url', url)
    driver.execute_script(str_js)


def open_url(url):
    """
    测试用函数，用于快速打开页面
    :param url:
    """
    driver = start_webdriver()
    open_start_page(driver)
    open_url_by_js(driver, url)
