import numpy as np
import cv2, threading, sys
from PIL import ImageGrab
from imutils.object_detection import non_max_suppression
from timeit import default_timer as timer

from typing import Dict, List

from BaseMonitor import *

PATTERN_SCALE = 1 # reduce image size for faster processing
BORDER_THRESH = 0.8 # if nor scaling, 0.8 is enough. must try to get this right
PIECE_THRESH = 0.8
LASTMOVE_THRESH = 0.7

# PATTERN_PATH = './patterns'
try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    PATTERN_PATH = f'{sys._MEIPASS}/patterns/Ziga'
except Exception:
    PATTERN_PATH = './patterns/Ziga'


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
    # debug only
    print(f'found {len(circles)}')
    output = gray.copy()
    for i in circles:
        cv2.circle(output, (i[0], i[1]), i[2], (0, 255, 0), 2)
    showimg(output)
    # ==
    return circles

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


class PiecePattern:
    def __init__(self, side: Side, name: str) -> None:
        self.side = side
        self.name = name
        self.fullName = f'{side.name}{name}'
        self.symbol = PIECE_SYMBOL[name]
        if side==Side.Black:
            self.symbol = self.symbol.lower()
        self.gray = load_gray(self.fullName)

class ZigaMonitor(BaseMonitor):
    piecePatterns: Dict[str, PiecePattern] = {}
    lastScanRegion = None

    # Abstract override
    def do_init(self, params=None):
        self.playSize = get_imgsize('play_area')             # The captured image of playing field only. This is used to calculate the grid size
        self.pieceSize = get_imgsize('BlackKing')            # Any image that have the size of piece to search
        self.playStart = get_imgsize('corrner2playfield')    # To get the offset from where Border is detected, to the actual playing field
        self.gridSize = np.divide(self.playSize, (GRID_WIDTH-1, GRID_HEIGHT-1))
        
        self.borderPatternGray, self.borderPatternMask = load_img_mask('border')  # The border pattern. Make sure that the tool can recognize this given any active possition
                                                                        # NOTE: when the lastmove is in the conner, the lastmove indicator may "peek" into border pattern
                                                                        #       make sure to mask it properly
        self.borderSize = get_imgsize('border')
        self.lastMovePatternGray, self.lastMovePatternMsk = load_img_mask('lastMove')

        for side in [Side.Black, Side.White]:
            for name in PIECE_NAME:
                p = PiecePattern(side,name)
                self.piecePatterns[p.fullName] = p
        
        # maybe this help speedup pattern matching
        self.patternOffset = [[np.multiply(self.gridSize, (i,j)) + self.playStart - np.divide(self.gridSize,2)
                               for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # [Y,X]

    def do_board_scan(self):
        # start = timer()
        img = screen_cap(self.lastScanRegion)
        return self.scan_image(img)
        # end = timer()
        # logger.info(end-start)


    # Specified task

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

    # a little bit faster, but still slow thouigh...
    def scan_image(self, board_gray):
        board = self.crop_image(board_gray)
        if board is None:
            # self.send_msg("** Error : No Board found.")
            self.send_fatal('Board Not Found')
            return None
        
        result = MonitorResult()

        result.lastMovePosition = self.scan_lastmove(board)
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
                        if np.array_equal(result.lastMovePosition, (col,row)):
                            result.moveSide = piece.side
                        curp = result.positions[row][col]
                        if (curp != '.'):
                            logger.warning(f'Duplicated piece found at {row}:{col} {curp} -> {piece.symbol}')
                        result.positions[row][col] = piece.symbol
                        if piece.name == 'King':
                            kingPos[piece.side] = (col,row)
                        break

        if kingPos[Side.Black] is None or kingPos[Side.White] is None:
            self.send_error(f'KING is not found in both sides')
        else:
            result.mySide = Side.White if kingPos[Side.White][1] > kingPos[Side.Black][1] else Side.Black

        return result



    # def timeit():
    #     board_gray = cv2.imread(f'{PATTERN_PATH}/ex2.png',0)
    #     start = timer()
    #     pos = find_pieces(board_gray)
    #     end = timer()
    #     print_board(pos)
    #     logger.info(end-start)
