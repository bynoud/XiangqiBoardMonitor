from web.bottle import route, run, template
from gui_builder import Builder

builder = Builder(True)

@route('/x')
def index():
    print('getting here')
    return builder.driver.page_source

run(host='localhost', port=8080)
