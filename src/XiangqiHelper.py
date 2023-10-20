
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium import webdriver

import threading, time, re, pathlib, sys, logging, argparse, subprocess
from enum import StrEnum

import gvars

from HelperEngine import HelperEngine, GUIActionCmd
from UI.ControlUI import ControlUI
from BoardMonitor.XqchessMonitor import XqchessMonitor, MonitorResult

# MYDEBUG = True

# # arguments & logging
# parser = argparse.ArgumentParser()
# parser.add_argument( '-log',
#                      '--loglevel',
#                      default='error',
#                      help='Provide logging level. Example --loglevel debug, default=warning' )

# args = parser.parse_args()
# loglevel = 'INFO' if MYDEBUG else args.loglevel.upper()


# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# logFormatter = logging.Formatter('%(module)-20s: %(message)s')

# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(loglevel)
# stream_handler.setFormatter(logFormatter)
# logger.addHandler(stream_handler)


# fileHandler = logging.FileHandler('helper.log', mode='w')
# fileHandler.setFormatter(logFormatter)
# logger.addHandler(fileHandler)
logger = logging.getLogger()

##################

APP_URL = 'https://zigavn.com/'
GAME_CANVAS_ID = 'gameCanvas' # inspect the page to get this

JSDIR = 'js'
try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    JSDIR = f'{sys._MEIPASS}/js'
except Exception:
    JSDIR = f'./js'
logger.info(f'JSDIR {JSDIR}')
# COOKIE_FILE = 'mycookie.pkl'

def get_game_size(driver):
    try:
        canvas = driver.find_element(By.ID, GAME_CANVAS_ID)
        # return (int(canvas.get_attribute('width')), int(canvas.get_attribute('height')))
        return (canvas.size['width'], canvas.size['height'])
    except:
        logging.error('no game canvas is found')
        return (1000,800)

###########
# Make sure match this value with web-GUI
ID_SIDE = 'xhSideContent'
ID_CONTROL_MOVETIME = 'xhCtrlMovetime'
ID_CONTROL_MULTIPV = 'xhCtrlMultipv'
ID_CONTROL_LOGTEXT = 'xhCtrlLogtext'
ID_CONTROL_MYMOVE = 'xhCtrlMymove'

def read_js(filename, startPtn=None, endPtn=None):
    try:
        with open(f'{JSDIR}/{filename}', encoding='utf-8') as f:
            data = f.read()
        if startPtn is not None:
            x = re.match(f'.*^\s*// {startPtn}\s*\n(.*)\n\s*// {endPtn}.*', data, re.MULTILINE|re.DOTALL)
            if x is None:
                logger.fatal(f'File {filename} dont have JS variable markdown')
            data = x.group(1)
        # data = re.sub(re.compile(r'//.*$', re.MULTILINE), '', data) # remove comment
        # data = data.replace('\n',' ')
        return data
    except Exception as e:
        logger.fatal(f'Error during loading script "{filename}": {e}')

class JsFunc(StrEnum):
    DRAW_BOARD = 'draw_board'
    SHOW_POPUP = 'show_popup'
    POSITION = 'update_position'


class TestME:
    def __init__(self) -> None:
        self.ctrlUI = ControlUI()



class Helper(HelperEngine):
    def __init__(self, url='https://xqchess.com/', headless=False) -> None:
        super().__init__(MonitorCls=XqchessMonitor)
        self.url = url
        self.logs = []
        self.logDepth = 500
        self.headless = headless
        self.lastPosition = None
        self.lastmove = []
        self.lastMovelist = []

        self.ctrlUI = ControlUI()
        self.ctrlUI.listener = self
        self.ctrlUI.on_movetime_changed(lambda x: self.set_option('movetime',x))
        self.ctrlUI.on_multipv_changed(lambda x: self.set_option('multipv',x))
        self.ctrlUI.on_mymove(self.forceMySideMoveNext)

    def start(self, restart=False, mon_params=None):
        if not restart:
            self.start_page()
        mon_params = {**(mon_params or {}), 'wdriver':self.driver}
        super().start(restart=restart, mon_params=mon_params)
        if not restart:
            self.ctrlUI.start()

    def start_page(self, reload=False):
        if not reload:
            logger.info(f'** Web starting headless={self.headless} url={self.url}...')
            try:
                self.driver.close()
                logger.info(f'Web closed for reload')
            except:
                pass
            try:
                # userdir = tempfile.mkdtemp()
                userdir = f'{pathlib.Path().absolute()}\\browser_cache'
                logger.info(f'browser dir {userdir}')
                options = webdriver.ChromeOptions()
                options.add_argument(f"user-data-dir={userdir}")
                if self.headless:
                    options.add_argument('--headless=new')
                    options.add_argument('--disable-gpu')
                else:
                    options.add_experimental_option('excludeSwitches', ['enable-logging']) #
                    options.add_argument(f"--app={self.url}")
                    options.add_argument('--enable-extensions')
                service = Service()
                service.creation_flags |= subprocess.CREATE_NO_WINDOW # This is needed when use pyinstaller --nowindowed build
                self.driver = webdriver.Chrome(options=options, service=service)
                if self.headless:
                    self.driver.get(self.url)
            except NoSuchWindowException:
                logger.fatal(f'cannot go to internet')
        else:
            logger.info('** Reloading')
            self.driver.get(self.url)

    def update_gui(self):
        r = self.lastMonitor
        self.ctrlUI.popup_msg('')
        self.ctrlUI.update_position(r.positions, r.lastMovePosition, self.lastMovelist)

    # def update_position(self, result: MonitorResult):
    #     self.lastPosition = positions
    #     self.lastmove = [] if lastmove is None else [lastmove[0],lastmove[1]]
    #     if newturn:
    #         self.lastMovelist = [] # clear movelist in new turn
    #     self.update_gui()

    # def update_movelist(self, movelist):
    #     self.lastMovelist = movelist
    #     self.update_gui()

    def add_log(self, msg):
        self.ctrlUI.add_log(msg)
    
    def set_fatal(self, msg):
        self.ctrlUI.popup_msg(msg)


    ### callback from control UI
    def on_refresh_clicked(self):
        self.start_page(reload=True)


if __name__ == "__main__":
    x = Helper()
    x.start()
    print('cleanup here')
    gvars.cleanup()
    sys.exit()
