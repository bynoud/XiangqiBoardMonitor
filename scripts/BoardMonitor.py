import numpy as np
import cv2
import pyautogui
from PIL import ImageGrab
from imutils.object_detection import non_max_suppression
from timeit import default_timer as timer

from typing import Dict

PATTERN_SCALE = 1 # reduce image size for faster processing
BORDER_THRESH = 0.8 # if nor scaling, 0.8 is enough. must try to get this right
PIECE_THRESH = 0.8

PATTERN_PATH = '../patterns'
GRID_WIDTH = 9
GRID_HEIGHT = 10
PIECE_NAME = 'King Advisor Elephant Rook Cannon Horse Pawn'.split()
PIECE_SIDE = 'Black White'.split()

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
    # print(f'found {len(boxes)} {boxes}')
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
    # print(boxes)
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

def screen_cap_pyautogui():
    img = pyautogui.screenshot()
    return cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)

def screen_cap_forscale(region=None):
    # if region is None:
    #     print(f'Capture the whole screen')
    # img = ImageGrab.grab()
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
    #     print(f'Capture the whole screen')
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


class PiecePattern:
    def __init__(self, side, name) -> None:
        self.side = side
        self.name = name
        self.fullName = f'{side}{name}'
        self.symbol = name[0] if side=='Black' else name[0].lower()
        self.gray = load_gray(self.fullName)

class BoardMonitor:
    # upleftSize = get_imgsize('upleft_fullsize')
    playSize = get_imgsize('play_area')
    pieceSize = get_imgsize('BlackKing')
    playStart = get_imgsize('corrner2playfield')
    gridSize = np.divide(playSize, (GRID_WIDTH-1, GRID_HEIGHT-1))
    
    borderPatternGray, borderPatternMask = load_img_mask('border')
    borderSize = get_imgsize('border')
    lastMovePatternGray, lastMovePatternMsk = load_img_mask('lastMove')

    positions = None
    piecePatterns: Dict[str, PiecePattern] = {}

    idleCnt = {}
    lastBoardStr = ''
    lastScanRegion = None

    lastMoveSide = None
    lastMovePosition = None

    def __init__(self) -> None:
        self.clear_board()
        for side in PIECE_SIDE:
            for name in PIECE_NAME:
                p = PiecePattern(side,name)
                self.piecePatterns[p.fullName] = p
        # ptn_rgb = cv2.imread(f'{PATTERN_PATH}/lastMove.png')
        # self.lastMovePatternMsk = create_mask(ptn_rgb)
        # self.lastMovePatternGray = cv2.cvtColor(np.array(ptn_rgb), cv2.COLOR_BGR2GRAY)

    def clear_board(self):
        self.positions = [['.' for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # It's [Y,X] in this array

    def crop_image(self, board_gray):
        # board_gray = cv2.cvtColor(board_color, cv2.COLOR_BGR2GRAY)
        # upleft_ptn = cv2.imread(f'{PATTERN_PATH}/upleft.png', 0)
        borderPos = find_pattern(board_gray, self.borderPatternGray, mask=self.borderPatternMask, thresh=BORDER_THRESH, center=0)
        if len(borderPos) != 1:
            # print("** Error : Cannot find upleft pattern. Check the input")
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
        coord = find_pattern(board_gray, self.lastMovePatternGray, thresh=PIECE_THRESH,
                            mask=self.lastMovePatternMsk, center=1, display=display)
        if len(coord)==0:
            return None
        coord = coord[0]
        return np.round((coord - self.playStart) / self.gridSize).astype(int)

    def send_msg(self, msg, end=None):
        try:
            self.idleCnt[msg] += 1
        except KeyError:
            self.idleCnt[msg] = 1
        if (self.idleCnt[msg] == 1):
            print(msg, end=end)
        if (self.idleCnt[msg] > 10):
            self.idleCnt[msg] = 0

    def scan_image(self, board_gray):
        board = self.crop_image(board_gray)
        if board is None:
            self.send_msg("** Error : Cannot find the board. Check the screen")
            return
        self.clear_board()

        self.lastMovePosition = self.scan_lastmove(board)
        # print(f'lastmove {lastMove}')

        for _, piece in self.piecePatterns.items():
            for pos in self.scan_piece(board, piece.gray):
                # print(pos, pieceSym)
                if np.array_equal(pos, self.lastMovePosition):
                    self.lastMoveSide = piece.side
                curp = self.positions[pos[1]][pos[0]]
                if (curp != '.'):
                    print(f'** Error: Duplicated piece found at {pos} {curp} -> {piece.symbol}')
                self.positions[pos[1]][pos[0]] = piece.symbol

        # for side in PIECE_SIDE:
        #     for name in PIECE_NAME:
        #         pieceName, pieceSym = pieceside2sym(side, name)
        #         # print(f'finding {pieceName}')
        #         for pos in self.scan_piece(board, pieceName):
        #             # print(pos, pieceSym)
        #             if np.array_equal(pos, self.lastMovePosition):
        #                 self.lastMoveSide = side
        #             curp = self.positions[pos[1]][pos[0]]
        #             if (curp != '.'):
        #                 print(f'** Error: Duplicated piece found at {pos} {curp} -> {pieceSym}')
        #             self.positions[pos[1]][pos[0]] = pieceSym

        newBoard = self.board_str()
        if newBoard != self.lastBoardStr:
            print(newBoard)
        self.lastBoardStr = newBoard


    def board_str(self):
        r = f'lastMove={self.lastMoveSide} {self.lastMovePosition}\n'
        for row in self.positions:
            r += '|' + ' '.join(row) + '|\n'
        return r

    def screen_check(self):
        # start = timer()
        img = screen_cap(self.lastScanRegion)
        self.scan_image(img)
        # end = timer()
        # print(end-start)

    def start(self, delaySecond=0.3):
        import time
        while True:
            self.screen_check()
            time.sleep(delaySecond)

    # def timeit():
    #     board_gray = cv2.imread(f'{PATTERN_PATH}/ex2.png',0)
    #     start = timer()
    #     pos = find_pieces(board_gray)
    #     end = timer()
    #     print_board(pos)
    #     print(end-start)
