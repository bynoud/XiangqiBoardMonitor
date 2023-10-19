import webview
from bs4 import BeautifulSoup

from threading import Thread
import inspect
import logging
import json

import sys
import os

if not sys.platform.startswith('linux'):
    import keyboard

from . import elements
from . import ihpy


# Start HTTP server in the background
def start_server():
    from . import HTTP_server


server = Thread(target=start_server, daemon=True).start()

html = """
<!DOCTYPE html>
<html>
<head lang="en">
<meta charset="UTF-8">
</head>
<body>
</body>
</html>
"""

global api_functions
api_functions = {}


# PYTHON - JAVASCRIPT BRIDGE #

class Api:
    def __init__(self):
        pass

    def bridge(self, func, calldata=None):
        if api_functions[func]:
            if calldata:
                return api_functions[func](calldata)
            else: 
                return api_functions[func]()

"""NOTE! It is not reccomended to use to use the event function or HTMLelement.addEventListener() when linking python code, see the updated example on Github"""

global bridgejs
# bridgejs = "function bridge(func) {pywebview.api.bridge(func)};"
bridgejs = ""

def event(function):
    global bridgejs
    if callable(function):
        fname = function.__name__
        if not fname in api_functions:
            api_functions.update({fname: function})
            bridgejs = bridgejs + "function NP_" + fname +  "(calldata=null){return pywebview.api.bridge('" + fname + "', calldata)}; "
        return f"NP_{fname}"
    else:
        raise EventException("Event attribute is not a function!")

def events(*functions):
    for fn in functions:
        event(fn)

def fileread(*p):
    # Check if program is being run as an exe
    if getattr(sys, 'frozen', False):
        p = [sys._MEIPASS] + p
    print(f'reading {p} "{os.path.join(*p)}"')
    return open(os.path.join(*p), "r", encoding="utf8").read()

# EXCEPTIONS #

class EventException(Exception):
    pass


class WindowException(Exception):
    pass


class Window:
    def __init__(self, title, css=None, scripts=[], min_size=(300, 300), size=(900, 600), 
                 childwindow=False, resizable=True, static='',
                 **kwargs):
        api = Api()
        self.webview = webview.create_window(title, html=html, js_api=api, min_size=min_size, resizable=resizable, width=size[0],
                                             height=size[1], **kwargs)
        self.static = static
        self.css = css
        self.scripts = scripts
        self.running = False
        self.onloaded = None
        self.childwindow = childwindow
        
        # Cover attributes
        self.usecover = False
        self.covertime = 3000
        self.covercolor = '#fff'
        self.covercontent = "<h1>Loading...</h1>"
        self.after_load = None

        self.resize = self.webview.resize
        self.toggle_fullscreen = self.webview.toggle_fullscreen

    def load_handler(self, win):
        if self.showafter:
            self.showafter()

    def loader(self, content="<h1 style='None'>Loading...</h1>", color='#fff', duration=3000, after=None):
        self.usecover = True
        self.webview.background_color = color
        self.covercolor = color
        self.covertime = duration

        self.covercontent = content

        if after:
            self.after_load = event(after)

    def display(self, html=None, file=None, pyfunctions=None, encoding="utf-8"):
        # global bridgejs

        frame = inspect.currentframe()
        locals = frame.f_back.f_locals

        if file:

            # Check if program is being run as an exe
            if getattr(sys, 'frozen', False):
                content = str(open(os.path.join(sys._MEIPASS, self.static, file), "r", encoding=encoding).read())
            else:
                content = str(open(self.static+file, "r", encoding=encoding).read())

            soup_src = content

        elif html:
            soup_src = html

        soup_src = ihpy.compile(str(soup_src), locals)

        soup = BeautifulSoup(soup_src, features="lxml")
        bodyContent = soup.body.find_all()

        for element in bodyContent:
            elements.createNeutronId(element)
            
        self.webview.html = str(soup) # Compile using ihpy, see ihpy.py

        if pyfunctions:
            for function in pyfunctions:
                # api_functions.update({str(function): function})
                # bridgejs = bridgejs + "function " + function.__name__ +  "(calldata=null){return pywebview.api.bridge('" + str(function) + "', calldata)}; "
                event(function)

                
    def setHtml(self, html):
        self.webview.html = str(html)

    def hide(self):
        self.webview.hide()

    def show(self, after=None):
        self.covertime = 3000
        self.showafter = after

        if self.running != True:
            if not sys.platform.startswith('linux'):
                keyboard.block_key("f5")

            soup = BeautifulSoup(self.webview.html, features="lxml")

            # HTTPS server bridge for files
            base = soup.new_tag('base')
            base['href'] = "http://localhost:5600/"
            soup.body.append(base)
            
            # Python-JavaScript bridge #
            bridge = soup.new_tag('script')
            bridge.string = bridgejs
            # if self.after_load:
            #     bridge.string = bridgejs + " setTimeout(function() {document.getElementById('cover').style.display = 'none';" + self.after_load + "}," + str(
            #         self.covertime) + ")" 
            # else:
            #     bridge.string = bridgejs + " setTimeout(function() {document.getElementById('cover').style.display = 'none'}," + str(
            #         self.covertime) + ")"
            if self.onloaded:
                fn = event(self.onloaded)
                bridge.string += """
                window.addEventListener("pywebviewready", function() {
                    console.log("pywebview ready"); """ + fn + "()})"
                
            for s in self.scripts:
                bridge.string += fileread(self.static, s)

            soup.body.append(bridge)

            # Loader #
            cover = soup.new_tag('div', id="cover", attrs={
                'style': 'position: fixed; height: 100%; width: 100%; top:0; left: 0; background: ' + self.covercolor + '; z-index:9999;'})

            if self.usecover == True:
                coverContent = BeautifulSoup(str(self.covercontent), features="lxml")
                cover.append(coverContent)
                soup.body.append(cover)

            # CSS stylesheet #
            style = soup.new_tag('style')
            if self.css:
                style.string = fileread(self.static, self.css)
            soup.body.append(style)

            self.webview.html = str(soup)
            # print("DTME", self.webview.html)
            self.running = True
            if self.childwindow:
                self.webview.evaluate_js(f"""document.open();document.write(`{str(soup)}`);document.close();""")
            else:
                webview.start(self.load_handler, self.webview, private_mode=False, storage_path=None,
                )#debug=True)
        else:
            self.webview.show()

    def appendChild(self, html):
        if self.running:
            self.webview.evaluate_js(f"""document.body.innerHTML += '{html}';""")
            return html
        else:
            raise WindowException(""""Window.append" can only be called while the window is running!""")

    def append(self, html):
        if self.running:
            self.webview.evaluate_js(f"""document.body.innerHTML += '{html}';""")
        else:
            raise WindowException(""""Window.append" can only be called while the window is running!""")

    def getElementById(self, id):
        if self.running:
            elementNeutronID = str(self.webview.evaluate_js(f""" '' + document.getElementById("{id}").className;"""))
            
            NeutronID = elementNeutronID.split(' ')[0]

            #Make sure that it is the actual Neutron id

            if "NeutronID_" in  NeutronID:
                pass
            else:
                for classname in elementNeutronID.split(' '):
                    if "NeutronID_" in classname:
                       NeutronID = classname 

            if NeutronID != "null":
                return elements.HTMLelement(self, NeutronID)
            else:
                logging.warning(f'HTMLelement with id "{id}" was not found!')
                return None

        else:
            soup = BeautifulSoup(self.webview.html, features="lxml")
            # check if element exists
            element = soup.select(f'#{id}')
            if element != []:
                NeutronID = element[0].get('class')[0]
                return elements.HTMLelement(self, NeutronID)
            else:
                logging.warning(f'HTMLelement with id "{id}" was not found!')
                return None

    def getElementsByTagName(self, name):
        if self.running:

            ElementsNeutronID = self.webview.evaluate_js("var elementsNeutronID = []; Array.from(document.getElementsByTagName('" + name + "')).forEach(function(item) { elementsNeutronID.push(item.className) }); '' + elementsNeutronID;")
            return [elements.HTMLelement(self, NeutronID.split(' ')[0]) for NeutronID in ElementsNeutronID.split(",")]
        else:
            pass

    def calljs(self, fname, data=None):
        # print(f"calljs {fname} {json.dumps(data)}")
        if data:
            self.webview.evaluate_js(f'{fname}({json.dumps(data)})')
        else:
            self.webview.evaluate_js(f'{fname}()')
