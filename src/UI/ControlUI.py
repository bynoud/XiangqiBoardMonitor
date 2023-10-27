import Neutron
import ctypes
import logging

import cv2
import numpy as np

import gvars

logger = logging.getLogger()

GRID_WIDTH = 9
GRID_HEIGHT = 10
positions = [['.' for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]

ctypes.windll.shcore.SetProcessDpiAwareness(2)

def find_circles(gray,
                 param1=1, # 500
                 param2=40, #smaller value-> more false circles
                 minRadius=20, maxRadius=100):
    minDist = minRadius*2
    gray_blurred = cv2.blur(gray, (3, 3))
    circles = cv2.HoughCircles(gray_blurred, cv2.HOUGH_GRADIENT, 1, minDist,
                                       param1=param1, param2=param2, 
                                       minRadius=minRadius, maxRadius=maxRadius)
    if circles is None:
        circles = []
    else:
        circles = np.uint16(np.around(circles[0,:]))

    # output = gray.copy()
    # for i in circles:
    #     cv2.circle(output, (i[0], i[1]), i[2], (0, 255, 0), 2)
    # cv2.imwrite(outPath,output)
    # print('XXX', len(circles))
    # ==
    # print(circles)
    return circles.tolist()

class ControlUI:
    def __init__(self, static='UI/') -> None:
        self.win = Neutron.Window("XiangqiHelper", 
                                  size=(450,700), 
                                  static=static,
                                  css="def.css",
                                  scripts=['board.js'])
        self.win.display(file="helper_control.html")

        self._cb_movetime = []
        self._cb_multipv = []
        self._cb_mymove = []

        self.listener = None

        self.setupConfig = dict(
            setupParam1 = 80,
            setupParam2 = 40,
            minRadius = 20,
            maxRadius = 50
        )

        self.lastpopup = ''
        self.positions = None
        self.lastmove = None
        self.movelist = None
        self.logs = []

        self.loaded = False
        self.win.onloaded = self.onloaded
        
        # register the function
        Neutron.events(
            self.py_hi,
            self.set_movetime,
            self.set_multipv,
            self.set_mymove,
            self.onloaded,
            self.setup_value_changed,
            self.reload_page
        )

    def onloaded(self):
        logger.info("ControlUI loaded")
        self.loaded = True
        self.setup_init()
        self.refresh()

    def calljs(self, fn, params):
        try:
            self.win.calljs(fn, params)
        except Exception as e:
            logger.error(f'calljs failed: {e}')


    def setup_init(self):
        # self.setupImgPath = ''
        self.setupImg = cv2.imread(f'UI/b.png', 0)
        self.calljs('setupInit', self.setupConfig)
        self.calljs('setupImage', dict(
            path='UI/b.png',
            circles=self.setup_value_changed()))
        # self.win.calljs('drawSetupImage', self.setup_value_changed())

    def setup_value_changed(self, val=None):
        print(f'value changed "{val}"')
        if val is not None:
            self.setupConfig[val['name']] = int(val['value'])
        # oldfile = self.setupImgPath
        # self.setupImgPath = f'b_{time.time()}.png'
        circles = find_circles(self.setupImg,
                     param1 = self.setupConfig['setupParam1'],
                     param2 = self.setupConfig['setupParam2'],
                     minRadius=self.setupConfig['minRadius'],
                     maxRadius=self.setupConfig['maxRadius'])
        return circles
        # self.win.calljs('setupImage', self.setupImgPath)
        # if oldfile != '':
        #     os.remove(oldfile)

    def set_movetime(self, val):
        print(f'movetime = {val}')
        for cb in self._cb_movetime:
            cb(val)

    def on_movetime_changed(self, cb):
        self._cb_movetime.append(cb)

    def set_multipv(self, val):
        print(f'multipv = {val}')
        for cb in self._cb_multipv:
            cb(val)

    def on_multipv_changed(self, cb):
        self._cb_multipv.append(cb)

    def set_mymove(self):
        print(f'mymove')
        for cb in self._cb_mymove:
            cb()

    def on_mymove(self, cb):
        self._cb_mymove.append(cb)

    def reload_page(self):
        self.listener.on_refresh_clicked()

    def start(self):
        if self.win.running:
            return
        self.win.show()

    def refresh(self):
        if not self.win.running:
            return
        self.calljs('show_popup', dict(message=self.lastpopup))
        self.calljs('update_position', dict(positions=self.positions, 
                                lastmove=self.lastmove, 
                                movelist=self.movelist))
        self.calljs('set_log', self.logs)

    def popup_msg(self, msg):
        self.lastpopup = msg
        if not self.win.running:
            return
        self.calljs('show_popup', dict(message=msg))

    def update_position(self, positions, lastmove, movelist):
        self.positions = positions
        self.lastmove = lastmove
        self.movelist = movelist
        if not self.win.running:
            return
        self.calljs('update_position', dict(positions=positions, 
                                lastmove=lastmove, 
                                movelist=movelist))

    def set_log(self, logs):
        self.logs = logs
        if not self.win.running:
            return
        self.calljs('set_log', self.logs)

    def py_hi(self, msg):
        print(f'py_hi {msg}')
        # win.webview.evaluate_js('callme("frompy")')
        # win.calljs('callme', 'frompy')
        self.calljs('update_position', dict(positions=positions, 
                                lastmove=[], 
                                movelist=[]))
        
if __name__ == "__main__":
    ui = ControlUI('UI/')
    ui.start()
