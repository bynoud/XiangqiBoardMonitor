>>> import selenium
>>> from selenium import webdriver

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.get('file://C:/MYDATA/MyApps/XiangqiBoardMonitor/src/UI/xqchess.html')
nodes = driver.find_elements(By.CLASS_NAME, 'xq-node')

nodes = driver.find_elements(By.CLASS_NAME, 'xq-node')
positions = [['.' for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]

ptn = re.compile(r'^p(\d)(\d)$')
# for node in nodes:
#     attr = node.get_attribute('class').split()
#     if 'occupied' in attr:
#         print(f'check here {attr}')
#         for cn in attr:
#             print(f'  {cn}')
#             if attr[0] == 'p':
#                 positions[int(attr[1])][int(attr[2])] = node.find_element(By.CSS_SELECTOR, ':first-child').get_attribute('class')
#                 break


import xml.etree.ElementTree as ET

NameMap = {
    'chariot': 'R',
    'cannon': 'C',
    'horse': 'N',
    'king': 'K',
    'adviser': 'A',
    'elephant': 'B',
    'pawn': 'P',
}

tree = ET.fromstring(driver.find_element(By.CLASS_NAME, 'xq-board-wrap').get_attribute('innerHTML'))
positions = [['.' for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)]
lastmove = None
for node in tree:
    attr = node.attrib['class'].split()
    if 'occupied' in attr:
        # print(f'check here {attr}')
        mypos = [0,0]
        for cn in attr:
            # print(f'  {cn}')
            if cn[0] == 'p':
                mypos = [int(cn[1]), int(cn[2])]
                break
        if 'last-move' in attr:
            lastmove = mypos
        a = node[0].attrib['class'].split()
        piece = ''
        for name in NameMap:
            if name in a:
                piece = NameMap[name]
                break
        if 'black' in a:
            piece = piece.lower()
        positions[mypos[0]][mypos[1]] = piece
