# -*- coding: utf-8 -*-
#author:purplewolf
import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time,platform
import os.path
import termcolor
try:
    from PIL import Image
except:
    pass
import urllib2
import os
import json
from bs4 import BeautifulSoup
from ConfigParser import ConfigParser
from getpass import getpass
import sys



class Logging:
    flag = True

    @staticmethod
    def error(msg):
        if Logging.flag == True:
            print "".join("ERROR: ")

    @staticmethod
    def warn(msg):
        if Logging.flag == True:
            print "".join("WARN: ")

    @staticmethod
    def info(msg):
        # attrs=['reverse', 'blink']
        if Logging.flag == True:
            print "".join("INFO: ")

    @staticmethod
    def debug(msg):
        if Logging.flag == True:
            print "".join("DEBUG: ")

    @staticmethod
    def success(msg):
        if Logging.flag == True:
            print "".join("SUCCES: ")



class LoginPasswordError(Exception):
    def __init__(self, message):
        if type(message) != type("") or message == "": self.message = u"帐号密码错误"
        else: self.message = message
        Logging.error(self.message)

class NetworkError(Exception):
    def __init__(self, message):
        if type(message) != type("") or message == "": self.message = u"网络异常"
        else: self.message = message
        Logging.error(self.message)

class AccountError(Exception):
    def __init__(self, message):
        if type(message) != type("") or message == "": self.message = u"帐号类型错误"
        else: self.message = message
        Logging.error(self.message)

class zhihuLogin(object):
    def __init__(self):
        Logging.flag = True
        self.headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36"
    }

        #实例会话对象
        self.session = requests.session()
        #实例LWPCookie对象
        self.session.cookies = cookielib.LWPCookieJar(filename='cookiefile')
        try:
            #从文件中加载Cookie
            session.cookies.load(ignore_discard=True)
        except:
            print("Cookie 未能加载")

        
    def get_captcha(self):
        t = str(int(time.time()*1000))
        captcha_url = 'http://zhihu.com/captcha.gif?r='+t+"&type=login"
        r = self.session.get(captcha_url,headers=self.headers)
        image_name=u'captcha.jpg'
        with open(image_name,'wb') as f:
            f.write(r.content)
            f.close()

        Logging.info(u"正在调用外部程序渲染验证码 ... ")
        if platform.system() == "Linux":
            Logging.info(u"Command: xdg-open %s &" % image_name )
            os.system("xdg-open %s &" % image_name )
        elif platform.system() == "Darwin":
            Logging.info(u"Command: open %s &" % image_name )
            os.system("open %s &" % image_name )
        elif platform.system() in ("SunOS", "FreeBSD", "Unix", "OpenBSD", "NetBSD"):
            os.system("open %s &" % image_name )
        elif platform.system() == "Windows":
            os.system("%s" % image_name )
        else:
            Logging.info(u"我们无法探测你的作业系统，请自行打开验证码 %s 文件，并输入验证码。" % os.path.join(os.getcwd(), image_name) )
    
        try:
            im =Image.open('captcha.jpg')
            #im.show()
            #im.close()
        except:
            print os.path.abspath('captcha.jpg')

        sys.stdout.write(termcolor.colored(u"请输入验证码: ", "cyan") )
        captcha = raw_input( )
        return captcha

    def get_xrsf(self):
        index_url = 'http://www.zhihu.com'
        index_page = self.session.get(index_url,headers=self.headers)
        if int(index_page.status_code) != 200:
            raise NetworkError(u"验证码请求失败")
        pattern = r'name="_xsrf" value="(.*?)"'
        self._xrsf = re.findall(pattern,index_page.text)
        if len(self._xrsf) < 1:
            Logging.info(u"提取XSRF 代码失败" )
            return None
        return self._xrsf[0]
    
    def isLogin(self):
        url = "https://www.zhihu.com/settings/profile"
        login_page = self.session.get(url,headers=self.headers,allow_redirects=False)
        status_code = int(login_page.status_code)
        if status_code == 200:
            print login_page.text
            return True
        elif status_code == 301 or status_code == 302:
            return False
        else:
            Logging.warn(u"网络故障")
            return None

    def read_account_from_config_file(self,config_file="config.ini"):
    
        cf = ConfigParser()
        if os.path.exists(config_file) and os.path.isfile(config_file):
            Logging.info(u"正在加载配置文件 ...")
            cf.read(config_file)

            email = cf.get("info", "email")
            password = cf.get("info", "password")
            if email == "" or password == "":
                Logging.warn(u"帐号信息无效")
                return (None, None)
            else: return (email, password)
        else:
            Logging.error(u"配置文件加载失败！")
            return (None, None)

    def upload_form(self,account,secret):
        if re.match(r"^1\d{10}$",account):
            print("手机号登录\n")
            post_url = 'http://www.zhihu.com/login/phone_num'
            postdata={
                '_xrsf':self.get_xrsf(),
                'password':secret,
                'phone_num':account,
                }

        elif re.match(r"^\S+\@\S+\.\S+$", account):
            print("邮箱登录\n")
            post_url = 'https://www.zhihu.com/login/email'
            postdata={
                '_xrsf':self.get_xrsf(),
                'password':secret,
                'email':account,
                }
        else:
            raise AccountError(u"帐号类型错误")

        print postdata
    
        try:
            login_page = self.session.post(post_url,data=parse.urlencode(postdata),headers=self.headers)
            if(login_page.status_code != 200):
                raise NetworkError(u"表单上传失败!")
        except:
            postdata["captcha"] = self.get_captcha()
            print postdata
            login_page = self.session.post(post_url,data=postdata,headers=self.headers)
        
        print login_page
        if(login_page.headers['content-type'].lower() == "application/json"):
           try:
               result = json.loads(login_page.content)
           except Exception as e:
               Logging.error(u"JSON解析失败！")
               Logging.debug(e)
               Logging.debug(login_page.content)
               result= {}
           if result["r"] == 0:
               Logging.success(u"登录成功！" )
               return {"result": True}
           elif result["r"] == 1:
               Logging.success(u"登录失败！" )
               return {"error": {"code": int(result['errcode']), "message": result['msg'], "data": result['data'] } }
           else:
               Logging.warn(u"表单上传出现未知错误: \n \t %s )" % ( str(result) ) )
               return {"error": {"code": -1, "message": u"unknown error"} }
        else:
           Logging.warn(u"无法解析服务器的响应内容: \n \t %s " % r.text )
           return {"error": {"code": -2, "message": u"parse error"} }

        session.cookies.save()

    def login(self,account=None,password=None):
        if self.isLogin() == True:
            Logging.success(u"你已经登录过咯")
            return True

        if account == None:
           (account,password) = self.read_account_from_config_file()
        if account == None:
           sys.stdout.write(u"请输入登录账号: ")
           account = raw_input()
           password = getpass("请输入登录密码: ")

        result = self.upload_form(account,password)
        if "error" in result:
           if result["error"]['code'] == 1991829:
               Logging.error(u"验证码输入错误，请准备重新输入。" )
               return self.login()
           elif result["error"]['code'] == 100005:
                # 密码错误
                Logging.error(u"密码输入错误，请准备重新输入。" )
                return self.login()
           else:
                Logging.warn(u"unknown error." )
                return False
        elif "result" in result and result['result'] == True:
            # 登录成功
            Logging.success(u"登录成功！" )
            #保存Cookie
            self.session.cookies.save()
            return True

       
if __name__ == '__main__':
       zhihu = zhihuLogin()
       zhihu.login()
       zhihu.isLogin()


    

