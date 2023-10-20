
import xml.etree.ElementTree as ET
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .BaseMonitor import *

NameMap = {
    'chariot': 'R',
    'cannon': 'C',
    'horse': 'N',
    'king': 'K',
    'adviser': 'A',
    'elephant': 'B',
    'pawn': 'P',
}

class XqchessMonitor(BaseMonitor):
    driver = None

    def do_init(self, params):
        print(f'start here {params}')
        self.driver = params['wdriver']

    def do_board_scan(self):
        # return self.html_scrapping()
        try:
            return self.html_scrapping()
        except Exception as e:
            self.send_fatal('Board Not Found')
            return None

    def html_scrapping(self):
        kingPos = {Side.Black: None, Side.White: None}
        tree = ET.fromstring(
            self.driver.find_element(By.CLASS_NAME, 'xq-board-wrap').get_attribute('innerHTML'))

        def get_position(attr):
            for cn in attr:
                if cn[0] == 'p':
                    return [int(cn[1]), int(cn[2])]
            return [0,0]
        def get_piece(cls):
            a = cls.split()
            piece = ''
            for name in NameMap:
                if name in a:
                    piece = NameMap[name]
                    break
            if 'black' in a:
                return (Side.Black, piece.lower())
            else:
                return (Side.White, piece)

        result = MonitorResult()

        for node in tree:
            attr = node.attrib['class'].split()
            if 'occupied' in attr:
                # print(f'check here {attr}')
                mypos = get_position(attr)
                side, piece = get_piece(node[0].attrib['class'])

                if piece in ('K','k'):
                    kingPos[side] = mypos

                if 'last-move' in attr:
                    result.lastMovePosition = [mypos[1], mypos[0]]
                    result.moveSide = side
                result.positions[mypos[0]][mypos[1]] = piece
            
            elif 'last-move' in attr:
                result.lastMoveFrom = get_position(attr)

        if kingPos[Side.Black] is None or kingPos[Side.White] is None:
            self.send_error(f'KING is not found in both sides')
        else:
            result.mySide = Side.White if kingPos[Side.White][0] > kingPos[Side.Black][0] else Side.Black
        return result
