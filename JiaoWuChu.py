import requests
import re
from lxml import etree
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from decimal import Decimal
import csv


class Jiaowuchu:
    def __init__(self):
        self.index_url = 'http://202.115.194.60/default.aspx'
        self.index_response = requests.get(url=self.index_url)
        self.url_code = re.search(r'\(.+\)', self.index_response.url).group()
        self.login_cookie = None
        self.progress_url = 'http://202.115.194.60/{}/ScoreQuery/wp_MyLearnProgress_Query.aspx'.format(self.url_code)
        self.check_url = 'http://202.115.194.60/{}/CheckCode.aspx'.format(self.url_code)
        self.login_url = 'http://202.115.194.60/{}/default.aspx'.format(self.url_code)
        self.user_name = '学号'
        self.password = '密码'

    def get_check_code_cookie_and_text(self):
        response = requests.get(url=self.check_url)
        img = Image.open(BytesIO(response.content))
        plt.imshow(img)
        plt.axis('off')
        plt.show()
        text = input('请输入验证码：')
        return text, response.cookies

    def get_login_paramater(self):
        content = self.index_response.text
        xpaht_content = etree.HTML(content)
        view_state = xpaht_content.xpath('//input[@id="__VIEWSTATE"]/@value')[0]
        view_state_gengerator = xpaht_content.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')[0]
        event_validation = xpaht_content.xpath('//input[@id="__EVENTVALIDATION"]/@value')[0]
        return view_state, view_state_gengerator, event_validation

    def produce_login_data(self):
        view_state, view_state_gengerator, event_validation = self.get_login_paramater()
        text, cookie = self.get_check_code_cookie_and_text()
        login_data = {
            '__LASTFOCUS': '',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_state_gengerator,
            '__EVENTVALIDATION': event_validation,
            'tbUserName': self.user_name,
            'tbPassWord': self.password,
            'txtCode': text,
            'btnLogin': ''
        }
        return login_data, cookie

    def set_login_cookie(self):
        login_data, login_cookie = self.produce_login_data()
        response = requests.post(url=self.login_url, data=login_data, cookies=login_cookie)
        self.login_cookie = response.cookies
        print(self.login_cookie)

    def get_jidian(self):
        response = requests.get(self.progress_url, cookies=self.login_cookie)
        content = response.text
        xpath_content = etree.HTML(content)
        tr_list = xpath_content.xpath('//tr[@class!="p_item_3" and @onmouseover="c=this.classNa'
                                      'me;this.className=\'p_item_hover\';"]')
        td_text_list = []
        for tr in tr_list:
            td_text = tr.xpath('./td/text()')
            td_text_list.append(td_text)
        td_text_list = list(map(lambda x: list(map(lambda y: y.strip(), x)), td_text_list))
        td_text_list = list(map(lambda x: list(filter(lambda y: y != '', x)), td_text_list))
        td_text_list = list(filter(lambda x: len(x) == 10, td_text_list))
        for td in td_text_list:
            td.pop(0)
            td.pop(3)
            td.pop(3)
            td.pop(3)
            td.pop(4)
        # 课程号，课程，学分，成绩，绩点
        sum_xuefen = Decimal(12)
        mul_xuefen_jidian = Decimal(0)
        current_jidian = 0
        for td in td_text_list:
            sum_xuefen += Decimal((td[2]))
            mul_xuefen_jidian += Decimal(td[4]) * Decimal(td[2])
            if sum_xuefen != 0:
                current_jidian = mul_xuefen_jidian/sum_xuefen
            td.append(sum_xuefen)
            td.append(mul_xuefen_jidian)
            td.append(current_jidian)
            print('课程号:{:<10}绩点:{:<10}学分:{:<10}当前总学分:{:<10}当前总学分绩点:{:<10}当前总绩点:{:<10}'
                  .format(td[0], td[4], td[2], td[5], td[6], td[7]))
        with open('result.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['课程号', '课程名', '学分', '成绩', '绩点', '总学分', '总学分绩点', '平均学分绩点'])
            writer.writerows(td_text_list)


    def run(self):
        self.set_login_cookie()
        self.get_jidian()


j = Jiaowuchu()
j.run()