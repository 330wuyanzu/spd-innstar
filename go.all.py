#encode: utf-8
#coding: utf-8

'''TODO:
    1.使用动态代理下载
    2.上一次全部下载完后，下载新增的帖子
'''

from selenium import webdriver
import selenium.common.exceptions as EX
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib
import time
#from requests_html import HTML
import re
import pathlib
import os
import hashlib as hashlib
import traceback
import copy
import json

import utils

Utils = utils.Utils
LOG = utils.LOG
INFO = utils.INFO
WARN = utils.WARN
NULL = 'null'

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
        self.browser.get(url)
        try:
            _x = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div#loadMore button.btn')))
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        except EX.TimeoutException:
            self.browser.quit()
        else:
            self.browser.maximize_window()

    '''所有已下载的文件名'''
    @property
    def Downloaded(self):
        tmp = []
        path = pathlib.Path(F'../downloaded/{self.md5}')
        tmp.extend(list(path.glob('*.mp4')))
        tmp.extend(list(path.glob('*.jpg')))
        tmp.extend(list(path.glob('*.jpeg')))
        tmp.extend(list(path.glob('*.png')))
        x = []
        for item in tmp:
            x.append(item.as_posix().split('./')[-1])
        return x
    
    '''是否可以加载'''
    @property
    def _is_loadable(self):
        try:
            _btn_more = self.browser.find_element_by_css_selector('div#loadMore button.btn')
        except EX.NoSuchElementException:
            return False
        else:
            return True
    
    '''是否正在加载'''
    @property
    def _is_loading(self):
        try:
            _loading = self.browser.find_element_by_css_selector('div#loadMore div.dropload-load span.loading')
        except EX.NoSuchElementException:
            return False
        else:
            return True
    
    '''是否全部加载完毕'''
    @property
    def _is_loadfinish(self):
        try:
            _finish = self.browser.find_element_by_css_selector('div#loadMore div.dropload-down div.dropload-noData')
        except EX.NoSuchElementException:
            return False
        else:
            True

    '''加载一次'''
    def Load(self):
        while True:
            if self._is_loadable:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                btn_more = self.browser.find_element_by_css_selector('div#loadMore button.btn')
                INFO('loadable')
                try:
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    btn_more.click()
                    INFO('clicked load')
                    time.sleep(1)
                    return 1
                except EX.ElementNotVisibleException:
                    WARN(traceback.format_exc())
                    time.sleep(2)
                except EX.ElementClickInterceptedException:
                    WARN(traceback.format_exc())
                    time.sleep(2)
            elif self._is_loading:
                INFO('loading')
                try:
                    _loading = self.browser.find_element_by_css_selector('div#loadMore div.dropload-load span.loading')
                except EX.NoSuchElementException:
                    return 1
                else:
                    try:
                        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                        _loading.click()
                    except EX.ElementClickInterceptedException:
                        pass
                    except EX.ElementNotVisibleException:
                        pass
                time.sleep(5)

    '''一次性加载完'''
    def LoadAll(self):
        while not self._is_loadfinish:
            self.Load()
    
    '''加载直到某个item的data-src出现'''
    def LoadUntil(self):
        downloaded = self.Downloaded
        last_found = ''
        while not self._is_loadfinish:
            self.Load()
            img_wraps = self.browser.find_elements_by_css_selector('div#list div.col-md-4 div.item div.img-wrap')
            img_wraps.reverse() # 反转列表，从下往上开始遍历
            for wrap in img_wraps:# 遍历已经加载出来的项目，看断点是否已经加载出来
                target = wrap.get_attribute('data-src').split('/')[-1].split('?')[0]
                if target in downloaded:
                    last_found = target
                elif last_found != '':
                    self.download_info['dn-first'] = last_found
                    return 1
            
    '''判断该项是否是视频'''
    def IsVideo(self, img_wrap):
        try:
            img_wrap.find_element_by_css_selector('img.videocam')
            INFO('Found Video')
            return True
        except EX.NoSuchElementException:
            return False

    '''等待视频加载，并返回source'''
    def WaitVideo(self):
        INFO('Wait For Video Load..........')
        # 等待视频加载出来后才有video标签
        while True:
            try:
                video = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article video source')
                INFO('Video Loaded')
                return video
            except EX.NoSuchElementException:
                time.sleep(2)
                continue

    '''判断是否是图片组'''
    def IsGroup(self, img_wrap):
        try:
            img_wrap.find_element_by_css_selector('img.sidecar')
            INFO('Found Group')
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
        INFO("Loading Group's Next One.......")

    '''下载视频'''
    def DownloadVideo(self):
        video_url = self.WaitVideo().get_attribute('src')
        name = video_url.split('/')[-1].split('?')[0]
        data = self.RequestData(video_url)
        Utils.SaveMedia(self.md5, name, data)
        INFO(F'Video Donwloaded: {name}')

    '''下载图片组'''
    def DownloadGroup(self):
        while True:
            name, data = self.DownloadSingle()
            Utils.SaveMedia(self.md5, name, data)
            INFO(F'One of Group Downloaded: {name}')
            lis = self.browser.find_elements_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper ol.carousel-indicators li')
            if 'active' in lis[-1].get_attribute('class'):
                INFO('Group Download Finish')
                break
            self.GroupNext()

    '''下载单个图片'''
    def DownloadSingle(self):
        img_url = self.browser.find_element_by_css_selector('div#gallery-modal div.img-container div.article div.imgwrapper img').get_attribute('src')
        name = img_url.split('/')[-1].split('?')[0]
        data = self.RequestData(img_url)
        return (name, data)

    def _download(self, items):
        for item in items:
            self._open_modal(item) # 打开modal
            if self.IsVideo(item):
                self.DownloadVideo()
            elif self.IsGroup(item):
                self.DownloadGroup()
            else:
                name, data = self.DownloadSingle()
                Utils.SaveMedia(self.md5, name, data)
                INFO('Pic Downloaded')
            self._close_modal() # 关闭modal
            self.download_info['dn-first'] = item.find_element_by_css_selector('div.img-wrap').get_attribute('data-src').split('/')[-1].split('?')[0]
            time.sleep(1)
        self.download_info['is-dn-finish'] = 'yes'
        INFO('All Dwonload Finished')
        self.browser.quit()

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

    def _open_modal(self, item):
        try:
            img_wrap = item.find_element_by_css_selector('div.img-wrap')
            thumb = img_wrap.find_element_by_css_selector('img.thumb')
            thumb.click()
            time.sleep(1)
            INFO('Modal Opened')
        except EX.NoSuchElementException:
            WARN('Modal Open Failed')
            exit(0)
        except EX.ElementClickInterceptedException:
            WARN('Thumb Unclickable')
            exit(0)
        except EX.ElementNotVisibleException:
            WARN('Element Not Visible')
            exit(0)

    def _close_modal(self):
        try:
            btn_close = self.browser.find_element_by_css_selector('div#gallery-modal button.btn-close')
            btn_close.click()
            INFO('Modal Closed')
        except EX.NoSuchElementException:
            WARN("Can't find modal's close button")
        except EX.ElementClickInterceptedException:
            WARN('Close button Unclickable')
            exit(0)
        except EX.ElementNotVisibleException:
            WARN('CLose button not visible')
            exit(0)

    '''启动下载'''
    def StartDownload(self):
        INFO('Start Download')
        dn_last = self.download_info['dn-last']
        if dn_last == 'null':# 第一次下载该用户
            INFO(F'First Download This User: <{self.user}>')
            self.LoadAll() # 一次性将所有的项目加载完
            items = self.browser.find_elements_by_css_selector('div#list div.col-md-4 div.item')
            items.reverse()
            self.download_info['dn-last'] = items[0].find_element_by_css_selector('div.img-wrap').get_attribute('data-src').split('/')[-1].split('?')[0]
            Utils.UpdateUserInfo(self.md5, self.download_info)
            try:
                self._download(items)
            except Exception:
                WARN('Download Broken')
                WARN(traceback.format_exc())
            finally:
                Utils.UpdateUserInfo(self.md5, self.download_info)
        elif self.download_info['is-dn-finish'] == 'not': # 如果不是第一次下载，且上一次还没有下载完
            INFO(F"BreakPoint: {self.download_info['dn-first']}")
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
                self._download(new_items)
            except Exception:
                WARN('Download Broken')
                WARN(traceback.format_exc())
            finally:
                Utils.UpdateUserInfo(self.md5, self.download_info)


if __name__ == '__main__':
    uid = 'pei716'
    test = InsStar(uid)
    test.BrowseUser()
    test.StartDownload()