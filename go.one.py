#encode: utf-8
#coding: utf-8
from selenium import webdriver
import selenium.common.exceptions as EX
import urllib
import time
from requests_html import HTML
import re
import pathlib
import os
import hashlib as hashlib
import traceback
import copy
import json

'''FIXME:
    还没开始实现
'''


class Utils(object):
    '''对用户名MD5，防止某些字符不能作为文件夹名，以MD5作为文件夹名'''
    @staticmethod
    def UserMD5(user):
        md5 = hashlib.md5()
        md5.update(bytes(user, encoding='utf-8'))
        return md5.hexdigest()
    
    '''记录用户名及其对应的MD5'''
    @staticmethod
    def LogMD5(md5, user):
        value = {md5: user}
        if not pathlib.Path('./MD5.json').exists():
            fl = open('./MD5.json', 'w', encoding='utf8')
            what = json.dumps(value)
            fl.write(what)
            fl.close()
        else:
            fl = open('./MD5.json','r',encoding='utf8')
            data = fl.read()
            fl.close()
            old = json.loads(data)
            old.update(value)
            what = json.dumps(old)
            fl = open('./MD5.json','w',encoding='utf8')
            fl.write(what)
            fl.close()
    
    '''按标记，解析要爬取的用户，返回用户列表'''
    @staticmethod
    def GetUsers():
        fl = open('./user.json','r',encoding='utf8')
        data = fl.read()
        fl.close()
        user_dict = json.loads(data)
        users = user_dict.keys()
        r = []
        for user in users:
            if user_dict[user] == 0:
                r.append(user)
        return r

    '''检测下载路径，如果没有则创建'''
    @staticmethod
    def TestDownloadPath(usermd5):
        root = '../downloaded'
        if not pathlib.Path(root).exists():
            pathlib.os.mkdir(root)
        if not pathlib.Path(F'{root}/{usermd5}').exists():
            pathlib.os.mkdir(F'{root}/{usermd5}')

    '''获取下载信息JSON，没有则创建'''
    @staticmethod
    def GetUserInfo(usermd5):
        root ='../downloaded'
        path = F'{root}/{usermd5}/{usermd5}.json'
        if not pathlib.Path(path).exists():
            fl = open(path,'w',encoding='utf8')
            info = {
                'up-first':     'null',
                'up-last':      'null',
                'is-up-finish': 'not',
                'dn-first':     'null',
                'dn-last':      'null',
                'is-dn-finish': 'not'
            }
            fl.write(json.dumps(info))
            fl.close()
            return info
        else:
            fl = open(path,'r',encoding='utf8')
            info = fl.read()
            fl.close()
            info = json.loads(info)
            return info

    '''更新下载信息JSON'''
    @staticmethod
    def UpdateUserInfo(usermd5, infodict):
        root ='../downloaded'
        path = F'{root}/{usermd5}/{usermd5}.json'
        fl = open(path,'w',encoding='utf8')
        fl.write(json.dumps(infodict))
        fl.close()

    @staticmethod
    def SaveMedia(usermd5, name, data):
        root ='../downloaded'
        path = F'{root}/{usermd5}/{name}'
        fl = open(path,'wb')
        fl.write(data)
        fl.close()


class InsStar(object):
    def __init__(self, user):
        md5 = Utils.UserMD5(user)
        Utils.TestDownloadPath(md5)
        Utils.LogMD5(md5, user)
        self.user = user
        self.md5 = md5
        self.browser = webdriver.Chrome()
        self.download_info = Utils.GetUserInfo(md5)

    '''打开用户页面,http://www.insstar.cn/{user}'''
    def BrowseUser(self):
        url = F'http://www.insstar.cn/{self.user}'
        try:
            self.browser.get(url)
        except Exception as ex:
            print(ex.__str__())
            exit(0)

    def StartDownload(self):
        #up_first = self.download_info['up-first']
        #up_last = self.download_info['up-last']
        is_up_finish = self.download_info['is-up-finish']
        #dn_first = self.download_info['dn-first']
        #dn_last = self.download_info['dn-last']
        is_dn_finish = self.download_info['is-dn-finish']
        if is_dn_finish == 'not':
            self.DownloadDN()
        if is_up_finish == 'not':
            self.DownloadUP()
    
    '''下载下半部分'''
    def DownloadDN(self):
        dn_first = self.download_info['dn-first']
        dn_last = self.download_info['dn-last']
        is_dn_finish = self.download_info['is-dn-finish']
        if dn_first == 'null':
            img_wrap_div_list = self.browser.find_elements_by_css_selector('div#list div.col-md-4 div.item div.img-wrap')
            first = img_wrap_div_list[0].get_attribute('data-src')
            last = img_wrap_div_list[-1].get_attribute('data-src')
            self.download_info['dn-first'] = first
            Utils.UpdateUserInfo(self.md5, self.download_info)
            # 弹出modal
            img_wrap_div_list[0].click()
            img = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper img')
            # 等待视频加载出来后才有video标签
            video = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper video source')
            # 点击时需将display设为block
            group_next = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper div.slides-controler a.next')
            gallery_next = self.browser.find_element_by_css_selector('div#gallery-modal div.controler div.next-prev button.glyphicon-chevron-right')
            # 检查是否是多项，
            # 如果是多项，则挨个下载
    
    '''下载上半部分'''
    def DownloadUP(self):
        pass

    def ParseFlow(self, start):
        # 点击start项，弹出modal

        # 检查modal


    def RequestData(self, url):
        headers = {
            'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN',
            'Connection': 'Keep-Alive',
            'Host': 'inbmi.com',
            'Upgrade-Insecure-Requests': 1,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'
        }
        req = urllib.request.Request(url=url, headers=headers)
        data = urllib.request.urlopen(req).read()
        return data








if __name__ == '__main__':
    headers = {
        'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN',
        'Connection': 'Keep-Alive',
        'Host': 'inbmi.com',
        'Upgrade-Insecure-Requests': 1,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'
    }
    test = InsStar('pei716')
    test.BrowseUser()
    test.DownloadDN()
    '''
    dropload-noData
    '''