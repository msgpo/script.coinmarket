# -*- coding: utf-8 -*-

import xbmc, xbmcaddon, xbmcgui
import os, requests, urllib2, json, collections, threading
from time import sleep
import time
from collections import OrderedDict

from sqlite3 import dbapi2 as database

ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
KEY_NAV_BACK = 92
ACTION_ESC = 182
ACTION_MOUSE_RIGHT_CLICK = 101

ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2

ADDON_ID='script.coinmarket'
addon=xbmcaddon.Addon(id=ADDON_ID)
home=xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))

profileDir = addon.getAddonInfo('profile')
profileDir = xbmc.translatePath(profileDir).decode("utf-8")

if not os.path.exists(profileDir):
    os.makedirs(profileDir)

dbFile = os.path.join(profileDir, 'watching.db')  
dbcon=database.connect(dbFile)
dbcur=dbcon.cursor()

try:
    dbcur.execute("CREATE TABLE IF NOT EXISTS currency (id INT);")
except:
    pass

dbcon.close()

cur_type = ["USD","AUD","BRL","CAD","CHF","CLP","CNY","CZK","DKK","EUR","GBP","HKD","HUF","IDR","ILS","INR","JPY","KRW","MXN","MYR","NOK","NZD","PHP","PKR","PLN","RUB","SEK","SGD","THB","TRY","TWD","ZAR","BTC","ETH","XRP","LTC","BCH"]
currency= {
    "USD": { "symbol": "$", "before": True},
    "AUD": { "symbol": "$", "before": True},
    "BRL": { "symbol": "R$", "before": True}, 
    "CAD": { "symbol": "$", "before": True}, 
    "CHF": { "symbol": "Fr.", "before": True},
    "CLP": { "symbol": "$", "before": True},
    "CNY": { "symbol": "¥", "before": True},
    "CZK": { "symbol": "Kč", "before": True},
    "DKK": { "symbol": "kr.", "before": True},
    "EUR": { "symbol": "€", "before": True},
    "GBP": { "symbol": "£", "before": True},
    "HKD": { "symbol": "$", "before": True},
    "HUF": { "symbol": "Ft. ", "before": True},
    "IDR": { "symbol": "Rp ", "before": True},
    "ILS": { "symbol": "₪", "before": True},
    "INR": { "symbol": "₹", "before": True},
    "JPY": { "symbol": "¥", "before": True},
    "KRW": { "symbol": "₩", "before": True},
    "MXN": { "symbol": "$", "before": True},
    "MYR": { "symbol": "RM", "before": True},
    "NOK": { "symbol": "kr ", "before": True},
    "NZD": { "symbol": "$", "before": True},
    "PHP": { "symbol": "₱", "before": True},
    "PKR": { "symbol": "Rs ", "before": True},
    "PLN": { "symbol": "zl", "before": True},
    "RUB": { "symbol": "₽", "before": True},
    "SEK": { "symbol": "kr ", "before": True},
    "SGD": { "symbol": "S$", "before": True},
    "THB": { "symbol": "฿", "before": True},
    "TRY": { "symbol": "₺", "before": True},
    "TWD": { "symbol": "NT$", "before": True},
    "ZAR": { "symbol": "R", "before": True},
    "BTC": { "symbol": " BTC", "before": False},
    "ETH": { "symbol": " ETH", "before": False},
    "XRP": { "symbol": " XRP", "before": False},
    "LTC": { "symbol": " LTC", "before": False},
    "BCH": { "symbol": "BCH", "before": False}
}

view_type = ["rank", "volume_24h", "percent_change_24h", "favourites"]

try:
    default_currency = cur_type[int(xbmcaddon.Addon().getSetting('default_currency'))]
    default_view = view_type[int(xbmcaddon.Addon().getSetting('default_view'))]
except:
    default_currency = cur_type[0]
    default_view = view_type[0]

class MainClass(xbmcgui.WindowDialog):
    def heartbeat(self):
        while self.running:
            time.sleep(300)
            if self.active:
            
                watching = self.getAllWatching()    

                if self.order == "favourites":
                
                    toReturn = {}
                    toReturn['data'] = {}
                    for ids in watching:
                        cmc = json.loads(self.get("https://api.coinmarketcap.com/v2/ticker/"+str(ids)+"?convert="+default_currency).decode('utf-8'), parse_float=str)
                        toReturn['data'][int(ids)] = cmc["data"]
                    toReturn['data'] = OrderedDict(sorted(toReturn['data'].items(), key=lambda (x, y): y['rank']))
                

                    cmc = toReturn
                else:
                    cmc = json.loads(self.get("https://api.coinmarketcap.com/v2/ticker/?start="+str(self.start)+"&limit=10&sort="+str(self.order)+"&convert="+default_currency).decode('utf-8'), object_pairs_hook=OrderedDict, parse_float=str)

                    
                    
                    count = 0
                    for word in cmc['data']:
                        try:
                            val = cmc['data'][word]['quotes'][default_currency]['market_cap'].split(".")
                            val = str('{:,}'.format(int(val[0])))

                            self.label[str(count)+"3"].setLabel(self.printCurrency(val))
                        except:
                            pass

                        try:
                            val = cmc['data'][word]['quotes'][default_currency]['price']
                            self.label[str(count)+"4"].setLabel(self.printCurrency(val))
                        except:
                            pass

                        try:
                            val = cmc['data'][word]['quotes'][default_currency]['volume_24h'].split(".")
                            val = str('{:,}'.format(int(val[0])))

                            self.label[str(count)+"5"].setLabel(self.printCurrency(val))
                        except:
                            pass

                        try:
                            val = cmc['data'][word]['circulating_supply'].split(".")
                            val = str('{:,}'.format(int(val[0])))

                            self.label[str(count)+"6"].setLabel(val+" "+cmc['data'][word]['symbol'])
                        except:
                            pass

                        try:
                            val = "{:.2f}".format(float(cmc['data'][word]['quotes'][default_currency]['percent_change_24h']))

                            self.label[str(count)+"7"].setLabel(val+"%")
                        except:
                            pass
                        count = count + 1


    def __init__(self, rank=default_view, page=1, parent=None):
        self.active = True
        self.running = True

        self.t = threading.Thread(target = self.heartbeat)
        self.t.start()

        self.skip = False
        if parent is not None:
            self.parent = parent
            self.is_loading = False
            self.ignore = []
            self.start = page
            self.order = rank
            self.skip = True
            parent.active = False
        else:
            self.is_loading = False
            dialog = xbmcgui.DialogBusy()
            dialog.create()
            self.start = 1
            self.order = default_view
            self.ignore = []

        watching = self.getAllWatching()

        if self.order == "favourites":
            if not watching:
                dialog = xbmcgui.Dialog()
                ret = dialog.ok("Coin Market - View Error", "You currently have no favourites setup.", "To use this view you must have at least one favourited currency. Please change your default view and add some currencies to your favourites.")
                exit()
            #https://api.coinmarketcap.com/v2/ticker/1/?convert=btc
            toReturn = {}
            toReturn['data'] = {}
            for ids in watching:
                cmc = json.loads(self.get("https://api.coinmarketcap.com/v2/ticker/"+str(ids)+"?convert="+default_currency).decode('utf-8'), parse_float=str)
                toReturn['data'][int(ids)] = cmc["data"]
            toReturn['data'] = OrderedDict(sorted(toReturn['data'].items(), key=lambda (x, y): y['rank']))
            

            cmc = toReturn
        else:
            cmc = json.loads(self.get("https://api.coinmarketcap.com/v2/ticker/?start="+str(self.start)+"&limit=10&sort="+str(self.order)+"&convert="+default_currency).decode('utf-8'), object_pairs_hook=OrderedDict, parse_float=str)
        #xbmc.log(str(cmc), xbmc.LOGERROR)
        self.setCoordinateResolution(0)

        
        
        self.background = xbmcgui.ControlImage(0,0,1920,1080, os.path.join(home, 'resources/images', 'fanart.jpg'))
        self.addControl(self.background)
        if not self.skip:
            self.background.setAnimations([('WindowOpen', 'effect=slide start=0,-1080 end=0,0 time=1500 condition=true tween=bounce', )])
        
        self.footer = xbmcgui.ControlImage(0,1000,1920,80, os.path.join(home, 'resources/images', 'main_footer.png'))
        self.addControl(self.footer)
        if not self.skip:
            self.footer.setAnimations([('WindowOpen', 'effect=slide start=0,80 end=0,0 delay=1500 time=1000 condition=true tween=bounce', )])

        self.prev = xbmcgui.ControlButton (1740, 1020, 45, 43, '', font='font10', noFocusTexture=os.path.join(home, 'resources/images', 'prev_page_normal.png'), focusTexture=os.path.join(home, 'resources/images', 'prev_page_hover.png'))
        self.addControl(self.prev)
        if not self.skip:
            self.prev.setAnimations([('WindowOpen', 'effect=slide start=0,80 end=0,0 delay=1500 time=1000 condition=true tween=bounce', )])

        self.next = xbmcgui.ControlButton (1840, 1020, 45, 43, '', font='font10', noFocusTexture=os.path.join(home, 'resources/images', 'next_page_normal.png'), focusTexture=os.path.join(home, 'resources/images', 'next_page_hover.png'))
        self.addControl(self.next)
        if not self.skip:
            self.next.setAnimations([('WindowOpen', 'effect=slide start=0,80 end=0,0 delay=1500 time=1000 condition=true tween=bounce', )])

        self.fave = xbmcgui.ControlButton (1640, 1020, 45, 45, '', font='font10', noFocusTexture=os.path.join(home, 'resources/images', 'fave_page_normal.png'), focusTexture=os.path.join(home, 'resources/images', 'fave_page_hover.png'))
        self.addControl(self.fave)
        if not self.skip:
            self.fave.setAnimations([('WindowOpen', 'effect=slide start=0,80 end=0,0 delay=1500 time=1000 condition=true tween=bounce', )])
    
        self.header = xbmcgui.ControlImage(0,0,1920,100, os.path.join(home, 'resources/images', 'main_header.png'))
        self.addControl(self.header)
        if not self.skip:
            self.header.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=200 condition=true delay=1500', )])
        self.info = {}
        self.like = {}
        
        
        
        for count in range(0, len(cmc['data'])):
            self.info[str(count)] = xbmcgui.ControlButton (0, 100+((count)*90), 1920, 90, '', font='font10', focusTexture=os.path.join(home, 'resources/images', 'main_hover.png'), noFocusTexture=os.path.join(home, 'resources/images', 'line'+str(count+1)+'.png'))
            self.addControl(self.info[str(count)])
            if not self.skip:
                self.info[str(count)].setAnimations([('WindowOpen', 'effect=slide start=1920 end=0 time=300 condition=true delay='+str(1500+(count*100)), ),
                                            ])

                                        
            

        for count in range(0,10):
            try:
                self.info[str(count)].controlDown(self.info[str(count+1)])
            except:
                pass
            try:
                self.info[str(count)].controlUp(self.info[str(count-1)])
            except:
                pass
        
        if rank is not "favourites":
            self.b1 = xbmcgui.ControlButton (1680, 0, 240, 100, '', font='font10', noFocusTexture=os.path.join(home, 'resources/images', 'clear_button.png'), focusTexture=os.path.join(home, 'resources/images', 'button_hover1.png'))
            self.addControl(self.b1)
            if not self.skip:
                self.b1.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=300 condition=true delay=1500', ),
                                                ])
            self.b2 = xbmcgui.ControlButton (1100, 0, 274, 100, '', font='font10', noFocusTexture=os.path.join(home, 'resources/images', 'clear_button.png'), focusTexture=os.path.join(home, 'resources/images', 'button_hover2.png'))
            self.addControl(self.b2)
            if not self.skip:
                self.b2.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=300 condition=true delay=1500', ),
                                                ])

            self.b3 = xbmcgui.ControlButton (0, 0, 100, 100, '', font='font10', noFocusTexture=os.path.join(home, 'resources/images', 'clear_button.png'), focusTexture=os.path.join(home, 'resources/images', 'button_hover3.png'))
            self.addControl(self.b3)
            if not self.skip:
                self.b3.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=300 condition=true delay=1500', ),
                                                ])

            self.info[str(0)].controlUp(self.b3)

            self.b3.controlDown(self.info[str(0)])
            self.b3.controlRight(self.b2)
            self.b3.controlLeft(self.b1)

            self.b2.controlDown(self.info[str(0)])
            self.b2.controlRight(self.b1)
            self.b2.controlLeft(self.b3)

            self.b1.controlDown(self.info[str(0)])
            self.b1.controlRight(self.b3)
            self.b1.controlLeft(self.b2)

        self.info[str(len(cmc['data'])-1)].controlDown(self.fave)
        self.prev.controlRight(self.next)
        self.prev.controlLeft(self.fave)
        self.next.controlRight(self.fave)
        self.next.controlLeft(self.prev)
        self.prev.controlUp(self.info[str(len(cmc['data'])-1)])
        self.next.controlUp(self.info[str(len(cmc['data'])-1)])

        self.fave.controlRight(self.prev)
        self.fave.controlLeft(self.next)
        self.fave.controlUp(self.info[str(len(cmc['data'])-1)])

        if rank is not "favourites":
            self.ignore.append(self.b1.getId())
            self.ignore.append(self.b2.getId())
            self.ignore.append(self.b3.getId())
            self.ignore.append(self.prev.getId())
            self.ignore.append(self.next.getId())
            self.ignore.append(self.fave.getId())
        

        self.label = {}
        self.logo = {}
        self.realID = []
        #for i in range (1, 11):
        count = 0
        sleep(1.5)
        for word in cmc['data']:
            try:
                self.realID.append(cmc['data'][word]['id'])

                self.like[str(count)] = xbmcgui.ControlImage(1840, 110+(count*90), 70, 70, os.path.join(home, 'resources/images', 'fave2.png'))
                self.addControl(self.like[str(count)])
                if not self.skip:
                    self.like[str(count)].setAnimations([('WindowOpen', 'effect=slide start=1920 end=0 time=300 condition=true delay='+str(1500+(count*100))),])

                if cmc['data'][word]['id'] not in watching:
                    self.like[str(count)].setVisible(False)

                self.logo[str(count)] = xbmcgui.ControlImage(125, 113+((count)*90), 64, 64, "https://s2.coinmarketcap.com/static/img/coins/64x64/"+str(cmc['data'][word]['id'])+".png")
                
                
                self.label[str(count)+"1"] = xbmcgui.ControlLabel(50,129+(count*90), 800, 20, str(cmc['data'][word]['rank']), font="font10", textColor="0xFF141414")

                self.label[str(count)+"2"] = xbmcgui.ControlLabel(220,129+(count*90), 800, 20, str(cmc['data'][word]['name']), font="font10", textColor="0xFF141414")

                try:
                    val = cmc['data'][word]['quotes'][default_currency]['market_cap'].split(".")
                    val = str('{:,}'.format(int(val[0])))

                    self.label[str(count)+"3"] = xbmcgui.ControlLabel(573,129+(count*90), 274, 20, self.printCurrency(val), font="font10", textColor="0xFF141414")
                except:
                    pass

                try:
                    val = cmc['data'][word]['quotes'][default_currency]['price']
                    self.label[str(count)+"4"] = xbmcgui.ControlLabel(847,129+(count*90), 274, 20, self.printCurrency(val), font="font10", textColor="0xFF141414")
                except:
                    pass

                try:
                    val = cmc['data'][word]['quotes'][default_currency]['volume_24h'].split(".")
                    val = str('{:,}'.format(int(val[0])))

                    self.label[str(count)+"5"] = xbmcgui.ControlLabel(1121,129+(count*90), 274, 20, self.printCurrency(val), font="font10", textColor="0xFF141414")
                except:
                    pass

                try:
                    val = cmc['data'][word]['circulating_supply'].split(".")
                    val = str('{:,}'.format(int(val[0])))

                    self.label[str(count)+"6"] = xbmcgui.ControlLabel(1395,129+(count*90), 274, 20, val+" "+cmc['data'][word]['symbol'], font="font10", textColor="0xFF141414")
                except:
                    pass

                try:
                    val = "{:.2f}".format(float(cmc['data'][word]['quotes'][default_currency]['percent_change_24h']))

                    if float(val) > 0:
                        self.label[str(count)+"7"] = xbmcgui.ControlLabel(1703,129+(count*90), 274, 20, val+"%", font="font10", textColor="0xff104000")
                    else:
                        self.label[str(count)+"7"] = xbmcgui.ControlLabel(1703,129+(count*90), 274, 20, val+"%", font="font10", textColor="0xFFD90000")
                except:
                    pass
                count = count + 1
            except:
                break

        for count in range (0, 10):
            try:
                self.addControl(self.logo[str(count)])
                if not self.skip:
                    self.logo[str(count)].setAnimations([('WindowOpen', 'effect=slide start=1920 end=0 time=300 condition=true delay='+str(1500+(count*100))),
                    ('VisibleChange', 'effect=slide start=0 end=100 time=300 condition=true')])
                for i in range (1, 8):
                    try:
                        self.addControl(self.label[str(count)+str(i)])
                        if not self.skip:
                            self.label[str(count)+str(i)].setAnimations([('WindowOpen', 'effect=slide start=1920 end=0 time=300 condition=true delay='+str(1500+(count*100))), 
                            ('VisibleChange', 'effect=slide start=0 end=100 time=300 condition=true'),
                            ])
                    except:
                        pass    
            except:
                pass
        self.loading = xbmcgui.ControlImage(14,1008,64,64, os.path.join(home, 'resources/images', 'loading.gif'))
        
        self.addControl(self.loading)
        self.loading.setVisible(False)
        self.setFocus(self.info['0'])
        try:
            dialog.close()
        except:
            self.loading.setVisible(False)
            self.setFocus(self.next)
            self.parent.loading.setVisible(False)
    
    def sort_by_rank(self, d):
        return d[1]['rank']
        
    def onAction(self, action):
        if action in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU, ACTION_MOUSE_RIGHT_CLICK, ACTION_ESC]:
            try:
                self.parent.is_loading = False
                self.parent.setFocus(self.parent.prev)
            except:
                pass

            self.active = False
            self.running = False

            try:
                self.parent.active = True
            except:
                pass

            self.close()
        if self.getFocusId() not in self.ignore:
            pass

    def onControl(self, control):    
        try:
            if not self.is_loading:
                if self.order is not "percent_change_24h" and control == self.b1:
                    self.is_loading = True
                    self.loading.setVisible(True)
                    mydisplay = MainClass("percent_change_24h", self.start, self)
                    mydisplay .doModal()
                elif self.order is not "volume_24h" and control == self.b2:
                    self.is_loading = True
                    self.loading.setVisible(True)
                    mydisplay = MainClass("volume_24h", self.start, self)
                    mydisplay .doModal()
                elif self.order is not "rank" and control == self.b3:
                    self.is_loading = True
                    self.loading.setVisible(True)
                    mydisplay = MainClass("rank", self.start, self)
                    mydisplay .doModal()
                elif control == self.next:
                    self.is_loading = True
                    self.loading.setVisible(True)
                    mydisplay = MainClass(self.order, self.start+10, self)
                    mydisplay .doModal()
        except:
            pass
        if not self.is_loading:
            if control == self.fave:
                if self.order == "favourites":
                    self.is_loading = True
                    self.loading.setVisible(True)
                    mydisplay = MainClass("rank", 1, self)
                    mydisplay .doModal()
                else:
                    watch = self.getAllWatching()
                    if len(watch) > 0:
                        self.is_loading = True
                        self.loading.setVisible(True)
                        mydisplay = MainClass("favourites", 1, self)
                        mydisplay .doModal()
                    else:
                        dialog = xbmcgui.Dialog()
                        ret = dialog.ok("Coin Market - View Error", "You currently have no favourites setup.", "To use this view you must have at least one favourited currency. Please change your default view and add some currencies to your favourites.")
                
            elif control == self.prev and self.start is not 1:
                self.parent.is_loading = False
                self.parent.setFocus(self.parent.prev)
                
                self.active = False
                self.running = False

                try:
                    self.parent.active = True
                except:
                    pass

                self.close()
            else:
                for i in range (0,10):
                    if control == self.info[str(i)]:
                        self.updateWatching(i)
            
        
                    
    
    def get(self, path, args={}):
        r = requests.get(path, data=args, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}, verify=False)
        return r.text

    def printCurrency(self, val):
        if currency[default_currency]['before']:
            return currency[default_currency]['symbol']+val
        else:
            return val+currency[default_currency]['symbol']

    def updateWatching(self, ids):
        watch = self.getAllWatching()
        dbcon=database.connect(dbFile)
        dbcur=dbcon.cursor()
        if self.realID[ids] not in watch:
            if len(watch) < 10:
                dbcur.execute("INSERT INTO currency (id) VALUES ('"+str(self.realID[ids])+"')")
                self.like[str(ids)].setVisible(True)
        else:
            dbcur.execute("DELETE FROM currency WHERE id = '"+str(self.realID[ids])+"'")
            self.like[str(ids)].setVisible(False)
        dbcon.commit()

        dbcon.close()

    def getAllWatching(self):
        dbcon=database.connect(dbFile)
        dbcur=dbcon.cursor()

        dbcur.execute("SELECT id FROM currency ORDER BY id ASC")
        faves=dbcur.fetchall()

        toReturn = []
        for i in faves:
            toReturn.append(i[0])
        dbcon.close()
        return map(int, toReturn)
        



mydisplay = MainClass()
mydisplay .doModal()
del mydisplay
