# ==================== 登录配置 ====================
# 四川大学教务系统登录 URL
LOGIN_URL = "http://zhjw.scu.edu.cn/login"
# 课表 API URL
COURSE_URL = "http://zhjw.scu.edu.cn/student/courseSelect/thisSemesterCurriculum/ajaxStudentSchedule/callback"
# 学期列表 URL
SEMESTER_URL = "http://zhjw.scu.edu.cn/student/courseSelect/calendarSemesterCurriculum/index"


# 浏览器设置
HEADLESS = False  # 是否无头模式（不显示浏览器界面）
# ================================================

import requests
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json


def request_data(headers, plan_code=""):
    # 使用 requests 发送 POST 请求获取课表 JSON 数据
    data = {"planCode": plan_code}
    response = requests.post(COURSE_URL, headers=headers, data=data)
    if response.status_code == 200:
        print("成功获取课表数据！")
        # print("响应内容:", response.text)  # 打印响应内容以供调试
        if "欢迎登录四川大学教务管理系统" in response.text:
            print("登录信息已过期，请重新登录获取新的 Cookies 和 Headers")
            return {}, response.text
        
        if not response.text.strip():
            print("响应体为空")
            return {}, response.text
        
        course_data = response.json()
    else:
        print(f"获取课表数据失败，状态码: {response.status_code}")
        course_data = {}
    return course_data, response.text


def fetch_semester_list(headers):
    """获取学期列表"""
    response = requests.get(SEMESTER_URL, headers=headers)
    if response.status_code != 200:
        print(f"获取学期列表失败，状态码: {response.status_code}")
        return []
    
    if "欢迎登录四川大学教务管理系统" in response.text:
        print("登录信息已过期，请重新登录获取新的 Cookies 和 Headers")
        return []
    
    # 解析 HTML 中的 <option value="...">...</option> 标签
    semesters = []
    option_pattern = re.compile(r'<option\s+([^>]*?)>(.*?)</option>', re.IGNORECASE | re.DOTALL)
    
    for match in option_pattern.finditer(response.text):
        attrs_str = match.group(1)
        text = match.group(2).strip()
        
        # 去掉 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 去掉多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 从属性中提取 value
        value_match = re.search(r'value="(.*?)"', attrs_str, re.IGNORECASE)
        if value_match:
            value = value_match.group(1)
            semesters.append({"code": value, "name": text})
    
    return semesters


def select_semester(semesters):
    """在命令行中让用户选择学期，回车默认选择当前学期"""
    if not semesters:
        print("未获取到学期列表，将使用空 planCode")
        return ""
    
    # 查找默认项（带「当前」标记的）
    default_idx = 0
    for i, sem in enumerate(semesters):
        if "当前" in sem['name']:
            default_idx = i
            break
    
    print("\n可选学期列表：")
    for i, sem in enumerate(semesters):
        marker = " [默认]" if i == default_idx else ""
        print(f"  [{i}] {sem['name']} ({sem['code']}){marker}")
    
    while True:
        try:
            choice = input(f"\n请输入要选择的学期编号（直接回车默认选择 [{default_idx}]）: ").strip()
            if choice == "":
                selected = semesters[default_idx]
                print(f"已选择学期: {selected['name']} ({selected['code']})")
                return selected["code"]
            
            idx = int(choice)
            if 0 <= idx < len(semesters):
                selected = semesters[idx]
                print(f"已选择学期: {selected['name']} ({selected['code']})")
                return selected["code"]
            else:
                print(f"请输入 0 到 {len(semesters) - 1} 之间的数字")
        except ValueError:
            print("请输入有效的数字编号")
        except KeyboardInterrupt:
            print("\n用户取消选择")
            raise


def get_course_json(save=1):
    """使用 Selenium 登录并获取课表 JSON 数据"""

    # 导入如果 last_cookies_and_headers.json 存在则使用其中的 cookies 和 headers
    try:
        with open("last_cookies_and_headers.json", "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            print("已加载上次保存的 Cookies 和 Headers")
        
        # 先获取学期列表并让用户选择
        semesters = fetch_semester_list(saved_data)
        plan_code = select_semester(semesters)
        
        course_data = request_data(saved_data, plan_code)
        if course_data[0] == {}:
            print("使用上次保存的 Cookies 和 Headers 获取课表数据失败，可能是登录信息过期，将重新登录获取")
        else:
            # print(course_data[0])
            print("使用上次保存的 Cookies 和 Headers 成功获取课表数据！")
            return course_data[0]
    except FileNotFoundError:
        print("未找到上次保存的 Cookies 和 Headers，将重新登录获取")


    # 设置 Chrome 选项
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # 忽略 SSL 证书错误，跳过不安全连接提示
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--allow-running-insecure-content")

    # 启动浏览器
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 打开登录页面
        driver.get(LOGIN_URL)
        print("已打开登录页面，请登录...\n由于 SCU 教务系统使用的是 HTTP, 如果弹出了安全警告，请选择继续访问（不安全）以进入登录页面")

        # 等待登录成功 - 检测特定元素
        wait = WebDriverWait(driver, timeout=300)  # 最多等待 5 分钟

        # 等待登录成功后出现的特定元素
        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'small.span_bbzx[style*="font-weight:700;font-family:微软雅黑"]',
                )
            )
        )
        print("检测到登录成功标识，登录成功！")

        # 获取cookies并构造请求头
        cookies = driver.get_cookies()
        cookie_header = "; ".join(
            [f"{cookie['name']}={cookie['value']}" for cookie in cookies]
        )
        headers = {
            "Cookie": cookie_header,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        # 打印cookies和headers以供调试
        # print("获取到的 Cookies:", cookie_header)
        # print("构造的 Headers:", headers)

        # 将cokkies和headers保存到文件
        with open("last_cookies_and_headers.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(headers))

        print("已获取登录 cookies，浏览器即将关闭...")
    except Exception as e:
        print(f"发生错误：{e}")
        raise
    finally:
        driver.quit()
        print("浏览器已关闭")
    
    # 在命令行中选择学期并获取课表数据（浏览器已关闭）
    # 先获取学期列表并让用户选择
    semesters = fetch_semester_list(headers)
    plan_code = select_semester(semesters)
    
    # 使用 requests 发送 POST 请求获取课表 JSON 数据
    course_data = request_data(headers, plan_code)
    if course_data[0] == {}:
        print("FKED UP")
        raise Exception("无法获取课表数据，可能是登录信息过期或请求失败")

    # 保存到文件
    if save:
        content = course_data[1]
        output_file = "course_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"课表数据已保存到：{output_file}")
    return course_data[0]


if __name__ == "__main__":
    get_course_json()
