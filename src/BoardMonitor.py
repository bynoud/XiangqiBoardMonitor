import numpy as np
import cv2, threading, re, sys, logging
from enum import Enum
from abc import ABC, abstractmethod
from PIL import ImageGrab
from imutils.object_detection import non_max_suppression
from timeit import default_timer as timer

from typing import Dict, List

logger = logging.getLogger()

PATTERN_SCALE = 1 # reduce image size for faster processing
BORDER_THRESH = 0.8 # if nor scaling, 0.8 is enough. must try to get this right
PIECE_THRESH = 0.8
LASTMOVE_THRESH = 0.7

# PATTERN_PATH = './patterns'
try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    PATTERN_PATH = f'{sys._MEIPASS}/patterns'
except Exception:
    PATTERN_PATH = './patterns'

GRID_WIDTH = 9
GRID_HEIGHT = 10
PIECE_NAME = 'King Advisor Elephant Rook Cannon Horse Pawn'.split()

PIECE_SYMBOL = {
    'King': 'K',
    'Advisor': 'A',
    'Elephant': 'B',
    'Rook': 'R',
    'Cannon': 'C',
    'Horse': 'N',
    'Pawn': 'P'
}

MOVE_PTN = re.compile(r'([a-z])(\d+)([a-z])(\d+)')

FILE2NUM = dict(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8,i=9)



def load_gray(fileName):
    img = cv2.imread(f'{PATTERN_PATH}/{fileName}.png', 0)
    return cv2.resize(img, (0,0), fx=PATTERN_SCALE, fy=PATTERN_SCALE)

def get_imgsize(fileName):
    # ptn = cv2.imread(f'{PATTERN_PATH}/{fileName}.png', 0)
    img = load_gray(fileName)
    return np.array(img.shape[::-1])

def showimg(img):
    cv2.imshow('img', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def load_img_mask(fileName):
    # gray = cv2.imread(f'{PATTERN_PATH}/{fileName}.png', 0)
    gray = load_gray(fileName)
    _, mask = cv2.threshold(gray,10,255,cv2.THRESH_BINARY)
    return gray, mask

def find_pattern_verbose(fileName, thresh=0.8):
    largeImg = cv2.imread(f'{PATTERN_PATH}/ex2.png')
    temp_gray = cv2.imread(f'{PATTERN_PATH}/{fileName}.png',0)

    # save the image dimensions
    W, H = temp_gray.shape[::-1]
    
    # Converting them to grayscale
    img_gray = cv2.cvtColor(largeImg, 
                            cv2.COLOR_BGR2GRAY)
    
    # Passing the image to matchTemplate method
    match = cv2.matchTemplate(img_gray, temp_gray,  cv2.TM_CCOEFF_NORMED)


    # return np.where(match >= thresh)
    
    # Select rectangles with
    # confidence greater than threshold
    (y_points, x_points) = np.where(match >= thresh)
    boxes = list()
    for (x, y) in zip(x_points, y_points):
        boxes.append((x, y, x + W, y + H))
    
    # apply non-maxima suppression to the rectangles
    # this will create a single bounding box
    boxes = non_max_suppression(np.array(boxes))
    
    # loop over the final bounding boxes
    for (x1, y1, x2, y2) in boxes:
        
        # draw the bounding box on the image
        cv2.rectangle(largeImg, (x1, y1), (x2, y2),
                    (255, 0, 0), 3)
    
    # Show the template and the final output
    cv2.imshow("After NMS", largeImg)
    cv2.waitKey(0)
    
    # destroy all the windows 
    # manually to be on the safe side
    cv2.destroyAllWindows()


def find_pattern(board_gray, piece_gray, thresh=0.5, center=1, display=0, mask=None):
    W, H = piece_gray.shape[::-1]
    # Passing the image to matchTemplate method
    match = cv2.matchTemplate(board_gray, piece_gray, cv2.TM_CCOEFF_NORMED, mask=mask)
    
    # reduce the matching overlap
    (y_points, x_points) = np.where(match >= thresh)
    boxes = list()
    for (x, y) in zip(x_points, y_points):
        boxes.append((x, y, x + W, y + H))
    boxes = non_max_suppression(np.array(boxes))
    if display==1:
        for (x1, y1, x2, y2) in boxes:
            # draw the bounding box on the image
            cv2.rectangle(board_gray, (x1, y1), (x2, y2),
                        (0, 0, 0), 2)
        showimg(board_gray)

    coords = np.array( [ (x[0], x[1]) for x in boxes ] )

    if center==1 and len(coords) > 0:
        coords = np.add(coords, np.divide((W,H), 2))

    return coords

# def screen_cap_pyautogui():
#     img = pyautogui.screenshot()
#     return cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)

def screen_cap_forscale(region=None):
    # screencap actually not take much time compare ti matching, so make it simple...
    img = ImageGrab.grab(bbox=region)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (0,0), fx=PATTERN_SCALE, fy=PATTERN_SCALE)
    if region is not None:
        img = img[ region[1]:region[3] , region[0]:region[2] ]
    return img

# This only work for SCALE=1
def screen_cap(region=None):
    # if region is None:
    #     logger.info(f'Capture the whole screen')
    # img = ImageGrab.grab(bbox=region)
    # screencap actually not take much time compare ti matching, so make it simple...
    img = ImageGrab.grab(bbox=region)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    # img = cv2.resize(img, (0,0), fx=PATTERN_SCALE, fy=PATTERN_SCALE)
    # if region is not None:
    #     img = img[ region[1]:region[3] , region[0]:region[2] ]
    return img

def create_mask(img_rgb):
    return np.array(np.array([ [0 if y.sum() < 10 else 255 for y in x] for x in img_rgb ])).astype(np.uint8)

class Side(Enum):
    Unknow = 0
    White = 1
    Black = 2

    @property
    def opponent(self):
        if self == Side.Unknow:
            return Side.Unknow
        if self == Side.Black:
            return Side.White
        return Side.Black
    
    @property
    def fen(self):
        if self == Side.White:
            return 'w'
        if self == Side.Black:
            return 'b'
        raise Exception('should not be called')

class MonitorFatal(Enum):
    NoBoardFound = 1

class BoardMonitorListener(ABC):
    @abstractmethod
    def on_monitor_fatal(self, type: MonitorFatal):
        pass
    @abstractmethod
    def on_monitor_error(self, msg: str):
        pass
    @abstractmethod
    def on_board_updated(self, fen: str, moveSide: Side, lastmovePosition):
        pass

class PiecePattern:
    def __init__(self, side: Side, name: str) -> None:
        self.side = side
        self.name = name
        self.fullName = f'{side.name}{name}'
        self.symbol = PIECE_SYMBOL[name]
        if side==Side.Black:
            self.symbol = self.symbol.lower()
        self.gray = load_gray(self.fullName)

class BoardMonitor:
    playSize = get_imgsize('play_area')             # The captured image of playing field only. This is used to calculate the grid size
    pieceSize = get_imgsize('BlackKing')            # Any image that have the size of piece to search
    playStart = get_imgsize('corrner2playfield')    # To get the offset from where Border is detected, to the actual playing field
    gridSize = np.divide(playSize, (GRID_WIDTH-1, GRID_HEIGHT-1))
    
    borderPatternGray, borderPatternMask = load_img_mask('border')  # The border pattern. Make sure that the tool can recognize this given any active possition
                                                                    # NOTE: when the lastmove is in the conner, the lastmove indicator may "peek" into border pattern
                                                                    #       make sure to mask it properly
    borderSize = get_imgsize('border')
    lastMovePatternGray, lastMovePatternMsk = load_img_mask('lastMove')

    positions = None
    piecePatterns: Dict[str, PiecePattern] = {}

    idleCnt = {}
    lastBoardStr = ''
    lastScanRegion = None

    mySide = Side.White
    lastMoveSide = Side.Unknow
    lastMovePosition = None
    forceMyMoveNext = False

    eventListeners: List[BoardMonitorListener] = []
    stopPolling = False
    pollingStopped = threading.Event()
    engine_thread = None

    

    def __init__(self) -> None:
        self.clear_board()
        for side in [Side.Black, Side.White]:
            for name in PIECE_NAME:
                p = PiecePattern(side,name)
                self.piecePatterns[p.fullName] = p
        
        # maybe this help speedup pattern matching
        self.patternOffset = [[np.multiply(self.gridSize, (i,j)) + self.playStart - np.divide(self.gridSize,2)
                               for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # [Y,X]

    def is_myside(self, side:Side):
        return False if side==Side.Unknow else side==self.mySide

    def add_event_listener(self, listener: BoardMonitorListener):
        self.eventListeners.append(listener)

    def clear_board(self):
        self.positions = [['.' for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # It's [Y,X] in this array

    def crop_image(self, board_gray):
        # board_gray = cv2.cvtColor(board_color, cv2.COLOR_BGR2GRAY)
        # upleft_ptn = cv2.imread(f'{PATTERN_PATH}/upleft.png', 0)
        borderPos = find_pattern(board_gray, self.borderPatternGray, mask=self.borderPatternMask, thresh=BORDER_THRESH, center=0)
        if len(borderPos) != 1:
            self.lastScanRegion = None
            return None

        upleftPos = borderPos[0]
        boardStart = upleftPos # + self.upleftSize - self.pieceSize
        boardEnd =  upleftPos + self.borderSize #+ self.upleftSize + self.playSize + self.pieceSize

        board_crop = board_gray[ boardStart[1]:boardEnd[1] , boardStart[0]:boardEnd[0] ]
        if self.lastScanRegion is None:
            self.lastScanRegion = (upleftPos[0], upleftPos[1], boardEnd[0], boardEnd[1])
        elif upleftPos[0] != 0 or upleftPos[1] != 0: # Not all zero
            self.lastScanRegion = None

        return board_crop

    # def scan_piece_name(self, board_gray, pieceName, display=0):
    #     piece_gray = cv2.imread(f'{PATTERN_PATH}/{pieceName}.png',0)
    #     coord = find_pattern(board_gray, piece_gray, center=1, display=display)
    #     if len(coord)==0:
    #         return coord
    #     return np.round((coord - self.playStart) / self.gridSize).astype(int)

    def scan_piece(self, board_gray, piece_gray, display=0):
        coord = find_pattern(board_gray, piece_gray, thresh=PIECE_THRESH, center=1, display=display)
        if len(coord)==0:
            return coord
        return np.round((coord - self.playStart) / self.gridSize).astype(int)

    def scan_lastmove(self, board_gray, display=0):
        coord = find_pattern(board_gray, self.lastMovePatternGray, thresh=LASTMOVE_THRESH,
                            mask=self.lastMovePatternMsk, center=1, display=display)
        if len(coord)==0:
            # self.send_msg('** Error: Last move position not found')
            return None
        coord = coord[0]
        return np.round((coord - self.playStart) / self.gridSize).astype(int)

    def send_msg(self, msg):
        try:
            self.idleCnt[msg] += 1
        except KeyError:
            self.idleCnt[msg] = 1
        if (self.idleCnt[msg] == 1):
            logger.info(msg)
            for l in self.eventListeners:
                l.on_monitor_error(msg)
        if (self.idleCnt[msg] > 10):
            self.idleCnt[msg] = 0

    def send_board_update_event(self, fen: str, moveSide: Side):
        if moveSide == Side.Unknow and self.forceMyMoveNext:
            moveSide = self.mySide.opponent
            logger.warning(f'Force moveside {moveSide}')
        self.forceMyMoveNext = False
        if fen != self.lastBoardStr or moveSide != self.lastMoveSide:
            for l in self.eventListeners:
                l.on_board_updated(fen, moveSide, self.lastMovePosition)
        self.lastBoardStr = fen
        self.lastMoveSide = moveSide

    def send_board_fatal(self, type: MonitorFatal):
        for l in self.eventListeners:
            l.on_monitor_fatal(type)

    # a little bit faster, but still slow thouigh...
    def scan_image(self, board_gray):
        board = self.crop_image(board_gray)
        self.clear_board()

        if board is None:
            # self.send_msg("** Error : No Board found.")
            self.send_board_fatal(MonitorFatal.NoBoardFound)
            self.lastBoardStr = ''
            return

        self.lastMovePosition = self.scan_lastmove(board)
        moveSide = Side.Unknow
        kingPos = {Side.Black: None, Side.White: None}

        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                ptnOffs = self.patternOffset[row][col]
                s = ptnOffs.astype(int)
                e = (ptnOffs + self.gridSize).astype(int)
                boardLoc = board[ s[1]:e[1], s[0]:e[0] ]
                for _, piece in self.piecePatterns.items():
                    res = find_pattern(boardLoc, piece.gray, thresh=PIECE_THRESH)
                    if len(res) > 0:
                        # found here
                        if np.array_equal(self.lastMovePosition, (col,row)):
                            moveSide = piece.side
                        curp = self.positions[row][col]
                        if (curp != '.'):
                            logger.warning(f'Duplicated piece found at {row}:{col} {curp} -> {piece.symbol}')
                        self.positions[row][col] = piece.symbol
                        if piece.name == 'King':
                            kingPos[piece.side] = (col,row)
                        break

        if kingPos[Side.Black] is None or kingPos[Side.White] is None:
            logger.warning(f'KING is not found in both sides')
            return
        
        self.mySide = Side.White if kingPos[Side.White][1] > kingPos[Side.Black][1] else Side.Black
        # if self.lastMoveSide == 'Unknown':
        #     self.send_msg(f'** Error: move side unkown, assum my side move')
        #     self.lastMoveSide = self.mySide

        self.send_board_update_event(self.get_fen(), moveSide)


    # def scan_image_full(self, board_gray):
    #     board = self.crop_image(board_gray)
    #     self.clear_board()

    #     if board is None:
    #         self.send_msg("** Error : No Board found.")
    #         self.lastBoardStr = ''
    #         return

    #     self.lastMovePosition = self.scan_lastmove(board)
    #     self.lastMoveSide = 'Unknown'
    #     kingPos = {'Black': None, 'White': None}

    #     for _, piece in self.piecePatterns.items():
    #         for pos in self.scan_piece(board, piece.gray):
    #             if np.array_equal(pos, self.lastMovePosition):
    #                 self.lastMoveSide = piece.side
    #             curp = self.positions[pos[1]][pos[0]]
    #             if (curp != '.'):
    #                 logger.warning(f'** Error: Duplicated piece found at {pos} {curp} -> {piece.symbol}')
    #             self.positions[pos[1]][pos[0]] = piece.symbol
    #             if piece.name == 'King':
    #                 kingPos[piece.side] = pos

    #     if kingPos['Black'] is None or kingPos['White'] is None:
    #         logger.warning(f'** Error: KING is not found in both sides')
    #         return
        
    #     self.mySide = 'White' if kingPos['White'][1] > kingPos['Black'][1] else 'Black'

    #     self.send_board_update_event()


    def board_str(self):
        r = f'lastMove={self.lastMoveSide} {self.lastMovePosition} me={self.mySide}\n'
        for row in self.positions:
            r += '|' + ' '.join(row) + '|\n'
        return r
    
    def get_fen(self):
        # Start for highest rank
        fens = []
        rotate = self.mySide==Side.Black
        def addfen(fen, sym):
            spaceSym = f'{"" if spacecnt==0 else spacecnt}'
            if rotate:
                fen = sym + spaceSym + fen
                if sym=='':
                    fens.insert(0,fen)
            else:
                fen = fen + spaceSym + sym
                if sym=='':
                    fens.append(fen)
            return fen
        for row in range(GRID_HEIGHT): # we save highest rank at 0
            fen = ''
            spacecnt = 0
            for col in range(GRID_WIDTH):
                p = self.positions[row][col]
                if p == '.':
                    spacecnt += 1
                else:
                    fen = addfen(fen, p)
                    spacecnt = 0
            fen = addfen(fen, '')
        return f'{"/".join(fens)}'

    def move_parse(self, mv):
        m = MOVE_PTN.match(mv)
        sx, sy = FILE2NUM[m.group(1)], int(m.group(2))
        ex, ey = FILE2NUM[m.group(3)], int(m.group(4))
        if self.mySide==Side.Black:
            return [ [GRID_WIDTH-sx, sy-1], [GRID_WIDTH-ex, ey-1] ]
        else:
            return [ [sx-1, GRID_HEIGHT-sy], [ex-1, GRID_HEIGHT-ey] ]

    def screen_check(self):
        # start = timer()
        img = screen_cap(self.lastScanRegion)
        self.scan_image(img)
        # end = timer()
        # logger.info(end-start)

    def start(self, delaySecond=0.1):
        self.stop()

        def polling():
            import time
            logger.info('ScreenMonitor started')
            while not self.stopPolling:
                try:
                    self.screen_check()
                except Exception as e:
                    logger.warning('screen check failed', e)
                    break
                time.sleep(delaySecond)
            self.pollingStopped.set()
            self.engine_thread = None
            logger.warning('ScreenMonitor stopped')
        self.engine_thread = threading.Thread(target=polling, daemon=True)
        self.engine_thread.start()

    def stop(self):
        if self.engine_thread and self.engine_thread.is_alive():
            logger.info('Stopping monitor thread...')
            self.stopPolling = True
            self.pollingStopped.wait()
            self.pollingStopped.clear()
            self.stopPolling = False
        self.clear_board()

    # def timeit():
    #     board_gray = cv2.imread(f'{PATTERN_PATH}/ex2.png',0)
    #     start = timer()
    #     pos = find_pieces(board_gray)
    #     end = timer()
    #     print_board(pos)
    #     logger.info(end-start)
