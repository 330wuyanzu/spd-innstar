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


'''TODO:
    1.使用动态代理下载
    2.上一次全部下载完后，下载新增的帖子
'''

def LOG(what):
    tm = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print(F'[{tm}] -- {what}')


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
        if '?' in name:
            name = name.split('?')[0]
        path = F'{root}/{usermd5}/{name}'
        fl = open(path,'wb')
        fl.write(data)
        fl.close()
        LOG(F'{usermd5}/{name} saved')


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
            self.browser.maximize_window()
        except Exception as ex:
            print(ex.__str__())
            exit(0)

    '''一直点击加载更多，直到加载完毕'''
    def LoadMore(self):
        count = 0
        while True:
            try:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                btn_more = self.browser.find_element_by_css_selector('div#loadMore button.btn')
                btn_more.click()
                LOG('Loading More')
                time.sleep(4)
                continue
            except EX.NoSuchElementException:
                LOG('Still Loading || All Loading Over:')
                try:
                    self.browser.find_element_by_css_selector('div#loadMore div.dropload-load span.loading')
                    LOG('    Still Loading')
                    time.sleep(6)
                    count += 1
                    if count == 3:
                        count = 0
                        self.browser.find_element_by_css_selector('div#loadMore').click()
                    continue
                except EX.NoSuchElementException:
                    try:
                        self.browser.find_element_by_css_selector('div#loadMore div.dropload-down div.dropload-noData')
                        LOG('    All Loading Over')
                        break
                    except EX.NoSuchElementException:
                        LOG('    Maybe Loading Over')
                        time.sleep(2)
                        continue
    
    def LoadUntil(self):
        count = 0
        while True:
            try:
                is_loaded = False
                dn_first = self.download_info['dn-first']
                img_wraps = self.browser.find_elements_by_css_selector('div#list div.col-md-4 div.item div.img-wrap')
                for wrap in img_wraps:
                    src = wrap.get_attribute('data-src')
                    src = src.split('/')[-1].split('?')[0]
                    if dn_first == src:
                        LOG(F'Loaded Until BreakPoint: {dn_first}')
                        is_loaded=True
                        break
                if is_loaded:
                    break
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                btn_more = self.browser.find_element_by_css_selector('div#loadMore button.btn')
                btn_more.click()
                LOG('Loading More')
                time.sleep(4)
                continue
            except EX.NoSuchElementException:
                LOG('Still Loading || All Loading Over:')
                try:
                    self.browser.find_element_by_css_selector('div#loadMore div.dropload-load span.loading')
                    LOG('    Still Loading')
                    time.sleep(6)
                    count += 1
                    if count == 3:
                        count = 0
                        self.browser.find_element_by_css_selector('div#loadMore').click()
                    continue
                except EX.NoSuchElementException:
                    try:
                        self.browser.find_element_by_css_selector('div#loadMore div.dropload-down div.dropload-noData')
                        LOG('    All Loading Over')
                        break
                    except EX.NoSuchElementException:
                        LOG('    Maybe Loading Over')
                        time.sleep(2)
                        continue

    '''判断该项是否是视频'''
    def IsVideo(self, item):
        try:
            item.find_element_by_css_selector('img.videocam')
            LOG('found video')
            return True
        except EX.NoSuchElementException:
            return False

    '''等待视频加载，并返回source'''
    def WaitVideo(self):
        LOG('wait for video load..........')
        # 等待视频加载出来后才有video标签
        while True:
            try:
                video = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper video source')
                return video
            except EX.NoSuchElementException:
                time.sleep(2)
                continue

    '''判断是否是图片组'''
    def IsGroup(self, item):
        try:
            item.find_element_by_css_selector('img.sidecar')
            LOG('found group')
            return True
        except EX.NoSuchElementException:
            return False

    '''加载图片组的下一项'''
    def GroupNext(self):
        # 点击时需将display设为block
        scriptp = "document.querySelector('div#gallery-modal div.img-container div.article div.imgwrapper div.slides-controler a.pre').style.display='block';"
        scriptn = "document.querySelector('div#gallery-modal div.img-container div.article div.imgwrapper div.slides-controler a.next').style.display='block';"
        self.browser.execute_script(scriptp)
        self.browser.execute_script(scriptn)
        group_next = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper div.slides-controler a.next')
        group_next.click()
        LOG('load group next....')

    '''下载视频'''
    def DownloadVideo(self):
        video_url = self.WaitVideo().get_attribute('src')
        name = video_url.split('/')[-1]
        data = self.RequestData(video_url)
        LOG(F'Video Donwloaded: {name}')
        return (name, data)

    '''下载图片组'''
    def DownloadGroup(self):
        tmp = []
        while True:
            name, data = self.DownloadSingle()
            LOG(F'Group Downloaded: {name}')
            tmp.append((name, data))
            lis = self.browser.find_elements_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper ol.carousel-indicators li')
            if 'active' in lis[-1].get_attribute('class'):
                break
            self.GroupNext()
        return tmp

    '''下载单个图片'''
    def DownloadSingle(self):
        img_url = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper img').get_attribute('src')
        name = img_url.split('/')[-1]
        data = self.RequestData(img_url)
        return (name, data)

    '''启动下载'''
    def StartDownload(self):
        LOG('Start Download')
        dn_last = self.download_info['dn-last']
        if dn_last == 'null':# 第一次下载该用户
            LOG(F'First Download This User: <{self.user}>')
            self.LoadMore()  # 一次性将所有的项目加载完
            items = self.browser.find_elements_by_css_selector('div#list div.col-md-4 div.item')
            items.reverse()
            self.download_info['dn-last'] = items[0].find_element_by_css_selector('div.img-wrap').get_attribute('data-src').split('/')[-1].split('?')[0]
            Utils.UpdateUserInfo(self.md5, self.download_info)
            try:
                for item in items:
                    item.find_element_by_css_selector('div.img-wrap').find_element_by_css_selector('img.thumb').click() # 打开modal
                    if self.IsVideo(item):
                        name, data = self.DownloadVideo()
                        Utils.SaveMedia(self.md5, name, data)
                    elif self.IsGroup(item):
                        nd_list = self.DownloadGroup()
                        for name, data in nd_list:
                            Utils.SaveMedia(self.md5, name, data)
                    else:
                        name, data = self.DownloadSingle()
                        Utils.SaveMedia(self.md5, name, data)
                    # 关闭modal
                    self.browser.find_element_by_css_selector('div#gallery-modal button.btn-close').click()
                    LOG('Modal Closed')
                    self.download_info['dn-first'] = item.find_element_by_css_selector('div.img-wrap').get_attribute('data-src').split('/')[-1].split('?')[0]
                    time.sleep(1)
                self.download_info['is-dn-finish'] = 'yes'
                LOG('All Dwonload Finished')
                self.browser.quit()
            except Exception:
                LOG('Download Broken')
                LOG(traceback.format_exc())
            finally:
                Utils.UpdateUserInfo(self.md5, self.download_info)
        elif self.download_info['is-dn-finish'] == 'not': # 如果不是第一次下载，且上一次还没有下载完
            LOG(F"BreakPoint: {self.download_info['dn-first']}")
            self.LoadUntil() # 加载到上次的断点
            items = self.browser.find_elements_by_css_selector('div#list div.col-md-4 div.item')
            items.reverse()
            self.download_info['dn-last'] = self.download_info['dn-first']
            try:
                new_items = []
                for item in items:
                    name = item.find_element_by_css_selector('div.img-wrap').get_attribute('data-src').split('/')[-1].split('?')[0]
                    if self.download_info['dn-last'] != name:
                        new_items.append(item)
                for item in new_items:
                    item.find_element_by_css_selector('div.img-wrap').find_element_by_css_selector('img.thumb').click() # 打开modal
                    if self.IsVideo(item):
                        name, data = self.DownloadVideo()
                        Utils.SaveMedia(self.md5, name, data)
                    elif self.IsGroup(item):
                        nd_list = self.DownloadGroup()
                        for name, data in nd_list:
                            Utils.SaveMedia(self.md5, name, data)
                    else:
                        name, data = self.DownloadSingle()
                        Utils.SaveMedia(self.md5, name, data)
                    # 关闭modal
                    self.browser.find_element_by_css_selector('div#gallery-modal button.btn-close').click()
                    LOG('Modal Closed')
                    self.download_info['dn-first'] = item.find_element_by_css_selector('div.img-wrap').get_attribute('data-src').split('/')[-1].split('?')[0]
                    time.sleep(1)
                self.download_info['is-dn-finish'] = 'yes'
                LOG('All Dwonload Finished')
                self.browser.quit()
            except Exception:
                LOG('Download Broken')
                LOG(traceback.format_exc())
            finally:
                Utils.UpdateUserInfo(self.md5, self.download_info)

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
    uid = 'pei716'
    test = InsStar(uid)
    test.BrowseUser()
    test.StartDownload()