import json
import pathlib
import hashlib
import time
from colorama import init, Fore
init(autoreset=True)

def LOG(what):
    tm = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print(F'[{tm}] -- {what}')

def INFO(what):
    LOG(F'INFO: {what}')

def WARN(what):
    LOG(F'{Fore.RED}WARN: {what}')

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
        INFO(F'Media {usermd5}/{name} saved')
