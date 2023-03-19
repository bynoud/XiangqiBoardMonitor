
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from selenium import webdriver

import threading, time, re, pickle, pathlib
from enum import StrEnum

from HelperEngine import HelperEngine, MonitorFatal

APP_URL = 'https://zigavn.com/'
GAME_CANVAS_ID = 'gameCanvas' # inspect the page to get this
COOKIE_FILE = 'mycookie.pkl'

def get_game_size(driver):
    try:
        canvas = driver.find_element(By.ID, GAME_CANVAS_ID)
        return (int(canvas.get_attribute('width')), int(canvas.get_attribute('height')))
    except:
        print('** Error: no game canvas is found')
        return (1000,800)

###########
# Make sure match this value with web-GUI
ID_SIDE = 'xhSideContent'
ID_CONTROL_MOVETIME = 'xhCtrlMovetime'
ID_CONTROL_MULTIPV = 'xhCtrlMultipv'
ID_CONTROL_LOGTEXT = 'xhCtrlLogtext'

def fatal(msg):
    print(f'** Fatal: {msg}')

def read_js(filename, startPtn=None, endPtn=None):
    try:
        with open(filename) as f:
            data = f.read()
        if startPtn is not None:
            x = re.match(f'.*^\s*// {startPtn}\s*\n(.*)\n\s*// {endPtn}.*', data, re.MULTILINE|re.DOTALL)
            if x is None:
                fatal(f'File {filename} dont have JS variable markdown')
            data = x.group(1)
        # data = re.sub(re.compile(r'//.*$', re.MULTILINE), '', data) # remove comment
        # data = data.replace('\n',' ')
        return data
    except Exception as e:
        fatal(f'Error during loading script "{filename}": {e}')

class JsFunc(StrEnum):
    DRAW_BOARD = 'draw_board'
    SHOW_POPUP = 'show_popup'
    POSITION = 'update_position'

class Builder(HelperEngine):
    def __init__(self, headless=False) -> None:
        super().__init__()
        self.logs = []
        self.logDepth = 500
        self.headless = headless
        self.init_js_script()
        self.lastPosition = None
        self.lastmove = []
        self.lastMovelist = []
        # try:
        #     options = webdriver.ChromeOptions()
        #     if headless:
        #         options.add_argument('--headless=new')
        #         options.add_argument('--disable-gpu')
        #     else:
        #         options.add_experimental_option('excludeSwitches', ['enable-logging'])
        #         options.add_argument(f"--app={APP_URL}"); 
        #     self.driver = webdriver.Chrome(options=options)
        #     if headless:
        #         self.driver.get(APP_URL)
        # except NoSuchWindowException:
        #     fatal(f'cannot get to internet')

        # self.build_gui()
        # if not headless:
        #     # self.start_reload_monitor()
        #     self.start_gui_polling()

    def init_js_script(self):
        self.js_vars = read_js('gui_inject.js', 'JS_VAR_START', 'JS_VAR_END')
        self.js_vars += read_js('draw_board.js')

    def exe_script(self, src, *param):
        try:
            self.driver.execute_script(src, *param)
        except Exception as e:
            fatal(f'Error during execute script: {src[:80]}...\n{e}')

    def exe_js_func(self, jsfunc: JsFunc, param={}):
        try:
            self.driver.execute_script(f'{self.js_vars}\n{jsfunc.value}({param})')
        except Exception as e:
            fatal(f'Error during execute func: {jsfunc} {param}...\n{e}')

    def test(self):
        options = webdriver.ChromeOptions()
        # options.add_experimental_option('excludeSwitches', ['enable-logging']) #
        options.add_argument('--enable-extensions')
        self.driver = webdriver.Chrome(options=options)
        self.driver.get('https://google.com')
        self.build_gui()

    def start(self, reload=False):
        if not reload:
            print('** Web starting...')
            try:
                self.driver.close()
                print(f'Web closed for reload')
            except:
                pass
            try:
                userdir = f'{pathlib.Path().absolute()}\\browser_cache'
                options = webdriver.ChromeOptions()
                options.add_argument(f"user-data-dir={userdir}")
                if self.headless:
                    options.add_argument('--headless=new')
                    options.add_argument('--disable-gpu')
                else:
                    options.add_experimental_option('excludeSwitches', ['enable-logging']) #
                    options.add_argument(f"--app={APP_URL}")
                    options.add_argument('--enable-extensions')
                self.driver = webdriver.Chrome(options=options)
                if self.headless:
                    self.driver.get(APP_URL)
            except NoSuchWindowException:
                fatal(f'cannot go to internet')
        else:
            print('** Reloading')
            self.driver.get(APP_URL)
        self.restart()
        self.build_gui()
        if not self.headless:
            self.start_gui_polling()

    def stop(self):
        print('GUI Exitting')
        # pickle.dump(self.driver.get_cookies(), open(COOKIE_FILE, "wb"))
        super().stop()


    @property
    def is_stopped(self):
        try:
            if len(self.driver.window_handles) == 0:
                return True
            else:
                return False
        except WebDriverException:
            return True

    # def load_js(self, filename, *params):
    #     try:
    #         with open(filename) as f:
    #             data = f.read()
    #         self.driver.execute_script(data, *params)
    #     except Exception as e:
    #         fatal(f'Error during loading script "{filename}" {params}: {e}')

    # def inject_js(self, filename, startPtn=None, endPtn=None):
    #     try:
    #         with open(filename) as f:
    #             data = f.read()
    #         if startPtn is not None:
    #             x = re.match(f'.*^\s*// {startPtn}\s*\n(.*)\n\s*// {endPtn}.*', data, re.MULTILINE|re.DOTALL)
    #             if x is None:
    #                 fatal(f'File {filename} dont have JS variable markdown')
    #             data = x.group(1)
    #         data = re.sub(re.compile(r'//.*$', re.MULTILINE), '', data) # remove comment
    #         data = data.replace('\n',' ')
    #         self.driver.execute_script(f'''
    #             var scr = document.createElement('script')
    #             scr.textContent = "{data}"
    #             document.body.appendChild(scr);''')
    #     except Exception as e:
    #         fatal(f'Error during loading script "{filename}": {e}')

    # def load_js_var(self, filename):
    #     self.inject_js(filename, 'JS_VAR_START', 'JS_VAR_END')

    # def reload(self):
    #     print(f'** Warning: Page reloading')
    #     self.driver.get(APP_URL)
    #     self.build_gui()
    #     self.start_gui_polling()

    def build_gui(self):
        print(f'[Builder] building the GUI')
        W, H = get_game_size(self.driver)
        self.exe_script(read_js('gui_inject.js'), dict(originalWidth=W, **self.guiOptions))
        self.exe_js_func(JsFunc.DRAW_BOARD)

        # WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.ID, ID_SIDE)))
        self.movetimeEle = self.driver.find_element(By.ID, ID_CONTROL_MOVETIME)
        self.multipvEle = self.driver.find_element(By.ID, ID_CONTROL_MULTIPV) #.get_attribute('value')
        self.logareaEle = self.driver.find_element(By.ID, ID_CONTROL_LOGTEXT)

        sideEle = self.driver.find_element(By.ID, ID_SIDE)
        self.driver.set_window_size(W + 100 + int(sideEle.value_of_css_property('width')[:-2]), H+150)


    def start_gui_polling(self):
        def poll():
            print(f'GUI polling start {self.guiOptions}')
            while not self.is_stopped:
                # print('check here')
                try:
                    self.execute_gui_cmd()
                    self.set_option('movetime', self.movetimeEle.get_attribute('value'))
                    self.set_option('multipv', self.multipvEle.get_attribute('value'))
                except (NoSuchElementException, StaleElementReferenceException):
                    self.start(reload=True)
                    return
                except WebDriverException:
                    if not self.is_stopped:
                        self.start(reload=False)
                    return
                time.sleep(0.5)
            self.stop()
        threading.Thread(target=poll).start()

    def on_monitor_fatal(self, type: MonitorFatal):
        match type:
            case MonitorFatal.NoBoardFound:
                self.exe_js_func(JsFunc.SHOW_POPUP, dict(message='No Board detected'))
            case _:
                print(f'** Error: Unknown fatal {type}')

    def update_gui(self):
        self.exe_js_func(JsFunc.POSITION,
                         dict(positions=self.lastPosition, 
                              lastmove=self.lastmove, 
                              movelist=self.lastMovelist))

    def update_position(self, positions, lastmove):
        self.lastPosition = positions
        self.lastmove = [] if lastmove is None else [lastmove[0],lastmove[1]]
        self.update_gui()

    def update_movelist(self, movelist):
        self.lastMovelist = movelist
        self.update_gui()
        # self.clear_movelist()
        # for index, (start, end) in enumerate(movelist):
        #     if index > self.debugDepth:
        #         return
        #     self.draw_move(index, start, end)


    # add a log
    def add_log(self, msg):
        self.logs.append(msg)
        self.logs = self.logs[-self.logDepth:]
        self.driver.execute_script('''
            arguments[0].value = arguments[1];
            arguments[0].scrollTop = arguments[0].scrollHeight
        ''', self.logareaEle, '\n'.join(self.logs))

# import base64
# import io
# from PIL import Image
# canvas = b.driver.find_element(By.ID, 'gameCanvas')
# canvas_base64 = b.driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
# canvas_png = base64.b64decode(canvas_base64)
# img = Image.open(io.BytesIO(canvas_png))
# nparr = np.asarray(img)

# data = b.driver.get_screenshot_as_png()
# img = Image.open(io.BytesIO(data))
# nparr = np.asarray(img)

# png_url = b.driver.execute_script(
#             'return document.getElementById("gameCanvas").toDataURL("image/png");')
# str_base64 = re.search(r'base64,(.*)', png_url).group(1)
# # Convert it to binary
# str_decoded = base64.b64decode(str_base64)
# image = Image.open(io.BytesIO(str_decoded))
# image = remove_transparency(image)

# def remove_transparency(im, bg_colour=(255, 255, 255)):
#     # Only process if image has transparency (https://stackoverflow.com/a/1963146)
#     if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
#         # Need to convert to RGBA if LA format due to a bug in PIL (https://stackoverflow.com/a/1963146)
#         alpha = im.convert('RGBA').split()[-1]
#         # Create a new background image of our matt color.
#         # Must be RGBA because paste requires both images have the same format
#         # (https://stackoverflow.com/a/8720632  and  https://stackoverflow.com/a/9459208)
#         bg = Image.new("RGBA", im.size, bg_colour + (255,))
#         bg.paste(im, mask=alpha)
#         return bg
#     else:
#         return im
