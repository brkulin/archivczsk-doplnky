# -*- coding: utf-8 -*-
#
# plugin.video.mall.tv
#
# (c) Michal Novotny
#
# original at https://www.github.com/misanov/
#
# Free for non-commercial use under author's permissions
# Credits must be used

import urllib2,urllib,re,sys,os,string,time,base64,datetime,json,aes,requests
import email.utils as eut
from urlparse import urlparse, urlunparse, parse_qs
from Components.config import config
try:
    import hashlib
except ImportError:
    import md5

from parseutils import *
from util import addDir, addLink, addSearch, getSearch
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.engine.tools.util import unescapeHTML

_UserAgent_ = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
addon =  ArchivCZSK.get_xbmc_addon('plugin.video.mall.tv')
profile = addon.getAddonInfo('profile')
__settings__ = addon
home = __settings__.getAddonInfo('path')
icon =  os.path.join( home, 'icon.png' )
lang = 'sk' if addon.getSetting('country') is '1' else 'cz'
__baseurl__ = 'https://sk.mall.tv' if lang is 'sk' else 'https://www.mall.tv'

class loguj(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'malltv.log')

    @staticmethod
    def logDebug(msg):
        if loguj.logDebugEnabled:
            loguj.writeLog(msg, 'DEBUG')

    @staticmethod
    def logInfo(msg):
        loguj.writeLog(msg, 'INFO')

    @staticmethod
    def logError(msg):
        loguj.writeLog(msg, 'ERROR')

    @staticmethod
    def writeLog(msg, type):
        try:
            if not loguj.logEnabled:
                return
            f = open(loguj.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3] + " [" + type + "] %s\n" % msg)
            f.close()
        except:
            pass

def get_url(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    req.add_header('Set-Cookie', '_selectedLanguage='+lang)
    response = urllib2.urlopen(req)
    data=response.read()
    response.close()
    return data

def OBSAH():
    addDir('SlowTV - Nonstop živě',"#",7,icon,4)
    addDir('Odvysílaná živá vysílání',"#",7,icon,3)
    addDir('Připravovaná živá vysílání',"#",7,icon,1)
    addDir('Nejnovější',"#",5,icon,10001)
    addDir('Populární',"#",5,icon,10002)
    addDir('Kategorie',"#",2,icon,1)
    addDir('Pořady',"#",3,icon,1)

def ZIVE(sid):
    strana = 0
    pocet = 0
    celkem = 0
    while True:
        html = get_url(__baseurl__+'/Live/LiveSectionVideos?sectionId='+str(sid)+'&page='+str(strana))
        if not html:
            break
        data = re.findall('<div.*?video-card.*?<a.*?href=(.*?) .*?title="(.*?)".*?data-img=(.*?) .*?_info', html, re.S)
        if data:
            for item in data:
                addDir(unescapeHTML(item[1]),item[0],9,item[2],1)
                pocet+=1
        temp = re.search('slider-total=(.*?) ', html, re.S)
        if temp:
            celkem = int(temp.group(1))
        if pocet >= celkem:
            break
        strana+=1

def KATEGORIE():
    html = get_url(__baseurl__+'/kategorie')

    hlavni = re.findall('<div.*?video-card.*?<a.*?href=(.*?) .*?data-src=(.*?)>.*?<h2.*?>(.*?)</h2>', html, re.S)
    if hlavni:
        hlavni.pop()
        for item in hlavni:
            addDir(unescapeHTML(item[2]),__baseurl__+item[0],6,item[1],1)
    vedlejsi = re.findall('col-sm-auto.*?href=(.*?) class="badge.*?>(.*?)</a>', html, re.S)
    if vedlejsi:
        for item in vedlejsi:
            addDir(unescapeHTML(item[1]),__baseurl__+item[0],6,icon,1)

def PODKATEGORIE(url):
    if __baseurl__ not in url:
        url = __baseurl__+url
    html = get_url(url)

    data = re.search('<section.*?isSerie(.*?)</section>', html, re.S)
    if data:
        hlavni = re.findall('<div.*?video-card.*?<a.*?href=(.*?) .*?data-src=(.*?)>.*?<h4.*?>(.*?)</h4>', data.group(1), re.S)
        if hlavni:
            for item in hlavni:
                addDir(unescapeHTML(item[2]),__baseurl__+item[0],4,item[1],1)

def PORADY():
    strana = 0
    pocet = 0
    celkem = 0
    while True:
        html = get_url(__baseurl__+'/Serie/CategorySortedSeries?categoryId=0&sortType=1&page='+str(strana))
        if not html:
            break
        data = re.findall('data-src=(.*?)>.*?href=(.*?) .*?<h4.*?>(.*?)</h4>', html, re.S)
        if data:
            for item in data:
                addDir(unescapeHTML(item[2]),item[1],4,item[0],1)
                pocet+=1
        temp = re.search('slider-total=(.*?) ', html, re.S)
        if temp:
            celkem = int(temp.group(1))
        if pocet >= celkem:
            break
        strana+=1

def VYBERY(url):
    if __baseurl__ not in url:
        url = __baseurl__+url
    html = get_url(url)

    # zalozky TODO
    section = re.search('<ul class="mall_categories-list(.*?)</ul>', html, re.S)
    if section:
        lis = re.findall('<li data-id=(.*?) .*?>([^<]+)', section.group(1), re.S)
        if lis != None:
            for li in lis:
                if int(li[0]) > 0:
                    addDir(unescapeHTML(li[1]),'#',5,None,li[0])

def VIDEA(sid):
    strana = 0
    celkem = 10 # max stran pro jistotu, aby se nezacyklil a u nejnovejsich a popularnich jsou to tisice!
    while True:
        url = '/Serie/Season?seasonId='+str(sid)+'&sortType=3&' # sekce dle data id
        if sid==10001: # nejnovejsi
            url = '/sekce/nejnovejsi?' if lang is 'cz' else '/sekcia/najnovsie?'
        if sid==10002: # popularni
            url = '/sekce/trending?' if lang is 'cz' else '/sekcia/trending?'
        html = get_url(__baseurl__+url+'page='+str(strana))
        if not html:
            break
        data = re.findall('video-card .*?href=(.*?) .*?title="(.*?)".*?data-img=(.*?) ', html, re.S)
        if data:
            for item in data:
                addDir(unescapeHTML(item[1]),item[0],9,item[2],1)
        if strana >= celkem:
            break
        strana+=1

def VIDEOLINK(url):
    if __baseurl__ not in url:
        url = __baseurl__+url
    html = get_url(url)

    try:
        title = re.search('<meta property=og:title content="(.*?)"', html, re.S).group(1)
    except:
        title = ""
    try:
        image = re.search('<meta property=og:image content="(.*?)"', html, re.S).group(1)
    except:
        image = None
    try:
        descr = re.search('<meta property=og:description content="(.*?)"', html, re.S).group(1)
    except:
        descr = ""
    try:
        src = re.search('source src=(.*?) ', html, re.S).group(1)+'.m3u8'
        addLink(title,src,image,descr)
    except:
        addLink("[COLOR red]Video nelze načíst[/COLOR]","#",None,None)


name=None
url=None
mode=None
thumb=None
page=None
desc=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        page=int(params["page"])
except:
        pass
try:
        thumb=urllib.unquote_plus(params["thumb"])
except:
        pass

#loguj.logInfo('URL: '+str(url))
#loguj.logInfo('NAME: '+str(name))
#loguj.logInfo('MODE: '+str(mode))
#loguj.logInfo('PAGE: '+str(page))
#loguj.logInfo('IMG: '+str(thumb))

if mode==None or url==None or len(url)<1:
        OBSAH()
elif mode==2:
        KATEGORIE()
elif mode==3:
        PORADY()
elif mode==4:
        VYBERY(url)
elif mode==5:
        VIDEA(page)
elif mode==6:
        PODKATEGORIE(url)
elif mode==7:
        ZIVE(page)
elif mode==9:
        VIDEOLINK(url)