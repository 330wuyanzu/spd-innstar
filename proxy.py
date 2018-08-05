#encode: utf-8
#coding: utf-8

import pathlib
import sqlite3 as DB
import requests
from selenium import webdriver
from bs4 import BeautifulSoup as BS
import requests_html as HTML
import traceback
import time


class XiCi(object):
    def __init__(self):
        self.__browser = webdriver.Firefox()
        self.__db = './proxy.db'
        self.__page = 3059
        self.__count = 0
        db_path = pathlib.Path(self.__db)
        if not db_path.exists():
            db = open(self.__db, 'wb')
            db.close()
            db = DB.connect(self.__db)
            sql = '''CREATE TABLE proxy (
                     address CHAR NOT NULL UNIQUE,
                     is_http CHAR NOT NULL)'''
            db.cursor().execute(sql)
            db.commit()
            db.close()

    def get_page(self):
        url = 'http://www.xicidaili.com/nn/3060'
        self.__browser.get(url)
        self.__page += 1

    def get_table(self):
        src = self.__browser.page_source
        html = HTML.HTML(html=src)
        table = html.find('#ip_list',first=True)
        return table

    def get_trs(self, table):
        trs = table.find('tr')
        if trs[0].attrs == {}:
            return trs[1:]
        else:
             return trs

    def get_ip_td(self, tr):
        tds = tr.find('td')
        ip_td = tds[1]
        port_td = tds[2]
        type_td = tds[5]
        return (ip_td, port_td, type_td)

    def get_ip(self, ip_td):
        ip = ip_td[0].text.strip()
        port = ip_td[1].text.strip()
        http = ip_td[2].text.strip()
        return ('%s:%s'%(ip,port),http)

    def insert_db(self, ip):
        is_http = ip[1]
        ip = ip[0]
        conn = DB.connect(self.__db)
        cursor = conn.cursor()
        sql = 'INSERT INTO proxy VALUES (?,?)'
        try:
            cursor.execute(sql, (ip,is_http))
            conn.commit()
        except DB.IntegrityError:
            pass
        finally:
            conn.close()
            self.__count += 1
            print('page [%d] [%d] insert IP <%s://%s>'%(self.__page,self.__count,is_http,ip))
            open('./proxy.log','w',encoding='utf8').write('page [%d] [%d] insert IP <%s://%s>\n'%(self.__page,self.__count,is_http,ip))

    def next_page(self):
        css = '#body > div.pagination > a.next_page'
        button = self.__browser.find_element_by_css_selector(css)
        button.click()
        self.__page += 1

    def Run(self):
        self.get_page()
        while True:
            table = self.get_table()
            trs = self.get_trs(table)
            for tr in trs:
                ip_td = self.get_ip_td(tr)
                ip = self.get_ip(ip_td)
                self.insert_db(ip)
            script = 'window.scrollTo(0,document.body.scrollHeight)'
            self.__browser.execute_script(script)
            time.sleep(20)
            self.next_page()

    def Close(self):
        self.__browser.close()

class IP3366(object):
    def __init__(self):
        self.__browser = webdriver.Firefox()
        self.__db = './proxy.db'
        self.__count = 0
        db_path = pathlib.Path(self.__db)
        if not db_path.exists():
            db = open(self.__db, 'wb')
            db = DB.connect(self.__db)
            sql = '''CREATE TABLE proxy (
                     address CHAR NOT NULL UNIQUE,
                     is_http CHAR NOT NULL)'''.strip()
            db.cursor().execute(sql)
            db.commit()
            db.close()

    def get_page(self):
        url = 'http://www.ip3366.net/'
        self.__browser.get(url)

    def get_tbody(self):
        src = self.__browser.page_source
        html = HTML.HTML(html=src)
        tbody = html.find('.table > tbody:nth-child(2)',first=True)
        return tbody

    def get_trs(self, tbody):
        trs = tbody.find('tr')
        return trs

    def get_td(self, tr):
        tds = tr.find('td')
        ip_td = tds[0]
        port_td = tds[1]
        type_td = tds[3]
        return (ip_td, port_td, type_td)

    def get_ip(self, ip_td):
        ip = ip_td[0].text.strip()
        port = ip_td[1].text.strip()
        http = ip_td[2].text.strip()
        ip = '%s:%s'%(ip,port)
        return (ip,http)

    def insert_db(self, ip):
        is_http = ip[1]
        ip = ip[0]
        conn = DB.connect(self.__db)
        cursor = conn.cursor()
        sql = 'INSERT INTO proxy VALUES (?,?)'
        try:
            cursor.execute(sql, (ip, is_http))
            conn.commit()
        except DB.IntegrityError:
            pass
        finally:
            conn.close()
            self.__count += 1
            print('[%d] insert IP <%s>'%(self.__count,ip))

    def next_page(self):
        ul_css = '#listnav > ul'
        ul = self.__browser.find_element_by_css_selector(ul_css)
        aes = ul.find_elements_by_tag_name('a')
        button = aes[-2]
        button.click()

    def Close(self):
        self.__browser.close()

    def Run(self):
        self.get_page()
        while True:
            tbody = self.get_tbody()
            trs = self.get_trs(tbody)
            for tr in trs:
                ip_td = self.get_td(tr)
                ip = self.get_ip(ip_td)
                self.insert_db(ip)
            time.sleep(10)
            self.next_page()

if __name__ == '__main__':
    '''
    url = 'http://httpbin.org/ip'
    proxy = {
        'http':'125.115.91.116:8118'
    }
    req = requests.get(url,proxies=proxy)
    print(req.text)'''
    x = XiCi()
    try:
        x.Run()
    except:
        print(traceback.print_exc())
        x.Close()