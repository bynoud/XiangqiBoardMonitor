from typing import List
from abc import ABC, abstractmethod
import tkinter as tk
import tkinter.scrolledtext as tkst
import queue
from enum import Enum

DEFAULT_SIZE = 40
GRID_HEIGHT = 10
GRID_WIDTH = 9
GRID_LINE_SIZE = 2
GRID_BORDER_OFFSET = 10

GRID_HALFSIZE = DEFAULT_SIZE / 2
GRID_COLOR = 'LightSteelBlue4'

PIECE_COLOR = {
    'White': 'orange red',
    'Black': 'dark green'
}

MOVE_COLOR = [
    'dark green', 'Red4',
    'SeaGreen1', 'IndianRed3',
    'PaleGreen3', 'IndianRed2',
    'PaleGreen2', 'IndianRed1',
    'PaleGreen1', 'salmon2',
]

NUM2FILE = list('abcdefghi')

CROSS_POSITION = [
    (1,2), (7,2),
    (0,3), (2,3), (4,3), (6,3), (8,3),
    (1,7), (7,7),
    (0,6), (2,6), (4,6), (6,6), (8,6),
]

PIECE_GUITAG = 'PieceGUI'
LASTMOVE_GUITAG = 'LastMoveGUI'
MOVE_GUITAG = 'MoveGUI'

def sideColor(s):
    return PIECE_COLOR['Black' if s.islower() else 'White']


class GUIActionCmd(Enum):
    Empty = 0
    Position = 1
    Moves = 2
    MESSAGE = 3

class GUIAction:
    def __init__(self, action: GUIActionCmd, params=None) -> None:
        self.action = action
        self.params = params

class GUIEventType(Enum):
    ForceMySideNextMove = 0
    SetMoveTime = 1

class HelperGUIListener:
    @abstractmethod
    def on_gui_event(self, action: GUIEventType, params = None):
        pass

class HelperGUI:

    def __init__(self, gridsize=DEFAULT_SIZE) -> None:
        self.gridsize = gridsize
        self.halfsize = int(self.gridsize/2)
        self.root = tk.Tk()
        self.gridCenter = [[None for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # [Y,X] = [row,col]
        self.guiUpdateAction = queue.Queue()
        self.guiUpdaterId = None

        self.playCanvas = self.draw_play_area()
        self.controlFrame = self.draw_controls()
        self.logview = self.draw_logview()

        self.eventListeners: List[HelperGUIListener] = []

    def add_event_listener(self, listener: HelperGUIListener):
        self.eventListeners.append(listener)

    def draw_play_area(self) -> tk.Canvas:
        hs = self.halfsize
        fs = self.gridsize

        W = GRID_WIDTH*fs + GRID_BORDER_OFFSET*2
        H = GRID_HEIGHT*fs + GRID_BORDER_OFFSET*2
        canvas = tk.Canvas(self.root, width=W, height=H)
        canvas.pack()

        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                xoffs, yoffs = x*fs + GRID_BORDER_OFFSET, y*fs + GRID_BORDER_OFFSET
                self.gridCenter[y][x] = (xoffs+hs, yoffs+hs)

                isleft, isright = x==0, x==GRID_WIDTH-1
                istop, isbot = y==0, y==GRID_HEIGHT-1
                # left horizontal
                if not isleft:
                    line = canvas.create_line(0, hs, hs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                    canvas.move(line, xoffs, yoffs)
                # right horizontal
                if not isright:
                    line = canvas.create_line(hs, hs, fs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                    canvas.move(line, xoffs, yoffs)
                # top vertical
                if not istop and not (y==5 and not (isleft or isright)):
                    line = canvas.create_line(hs, 0, hs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                    canvas.move(line, xoffs, yoffs)
                # bottom vertical
                if not isbot and not (y==4 and not (isleft or isright)):
                    line = canvas.create_line(hs, hs, hs, fs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                    canvas.move(line, xoffs, yoffs)

                if isleft:
                    canvas.create_text(xoffs, yoffs+hs, text=GRID_HEIGHT-y, font=('calibri',12) , fill='black')
                if isbot:
                    canvas.create_text(xoffs+hs, yoffs+fs, text=NUM2FILE[x], font=('calibri',12) , fill='black')

                if (x,y) in CROSS_POSITION:
                    hs2 = int(hs*0.7)
                    fs2 = fs - hs2
                    if not isleft:
                        line = canvas.create_line(hs2, hs2, hs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                        canvas.move(line, xoffs, yoffs)
                        line = canvas.create_line(hs2, fs2, hs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                        canvas.move(line, xoffs, yoffs)
                    if not isright:
                        line = canvas.create_line(fs2, hs2, hs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                        canvas.move(line, xoffs, yoffs)
                        line = canvas.create_line(fs2, fs2, hs, hs, fill=GRID_COLOR, width=GRID_LINE_SIZE)
                        canvas.move(line, xoffs, yoffs)

        # palace
        fs2 = fs*2
        for x,y in ((3,0), (3,7)):
            xoffs, yoffs = self.gridCenter[y][x]
            line = canvas.create_line(0, 0, fs2, fs2, fill=GRID_COLOR, width=GRID_LINE_SIZE)
            canvas.move(line, xoffs, yoffs)
            line = canvas.create_line(fs2, 0, 0, fs2, fill=GRID_COLOR, width=GRID_LINE_SIZE)
            canvas.move(line, xoffs, yoffs)

        return canvas
    
    def send_event(self, action: GUIEventType, params=None):
        # print(f'Sending GUI event {action} {params}')
        for l in self.eventListeners:
            l.on_gui_event(action, params)
    
    def draw_controls(self):
        fr = tk.Frame(self.root)
        fr.grid_rowconfigure(0, weight=1)
        fr.grid_columnconfigure(1, weight=1)

        getmoveBtn = tk.Button(fr, text='Myside', padx=10, pady=5,
                               command= lambda: self.send_event(GUIEventType.ForceMySideNextMove))
        getmoveBtn.grid(row=0, column=0, sticky='ns')

        mtVal = tk.IntVar(value=2)
        def mtUpdate(inc):
            cur = mtVal.get()
            if inc:
                cur += 1
            else:
                cur -= 1
            if cur < 6 and cur > 0:
                mtVal.set(cur)
                self.send_event(GUIEventType.SetMoveTime, cur)

        fr2 = tk.Frame(fr, padx=10, pady=5)
        mtEntry = tk.Entry(fr2, textvariable=mtVal, justify='center')
        mtButtonframe = tk.Frame(mtEntry)
        mtButtonframe.pack(side=tk.RIGHT)
        mtBtnUp = tk.Button(mtButtonframe, text="▲", font="none 5",
                            command=lambda: mtUpdate(True))
        mtBtnUp.pack(side=tk.TOP)
        mtBtnDown = tk.Button(mtButtonframe, text="▼", font="none 5",
                              command=lambda: mtUpdate(False))
        mtBtnDown.pack(side=tk.BOTTOM)
        # mtEntry.grid(row=0, column=1, sticky='ns')
        mtEntry.pack(side=tk.LEFT, ipadx=15)
        fr2.grid(row=0,column=1, sticky='ns')
        
        fr.pack()
        return fr
    
    def draw_logview(self):
        frame1 = tk.Frame(
            master = self.root,
            bg = '#808000'
        )
        frame1.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.YES)
        editArea = tkst.ScrolledText(
            master = frame1,
            wrap   = tk.WORD,
            width  = 20,
            height = 10
        )
        # Don't use widget.place(), use pack or grid instead, since
        # They behave better on scaling the window -- and you don't
        # have to calculate it manually!
        editArea.pack(padx=10, pady=10, fill=tk.BOTH, expand=tk.YES)
        return editArea

    def draw_position(self, positions):
        pieceHalfSize = int(self.gridsize * 0.4)
        self.playCanvas.delete(PIECE_GUITAG)
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                p = positions[y][x]
                if p == '.':
                    continue
                center = self.gridCenter[y][x]
                self.draw_piece(positions[y][x], pieceHalfSize, center[0], center[1])

    def draw_piece(self, symbol, halfsize, xoffs, yoffs):
        startX, startY = xoffs - halfsize, yoffs - halfsize
        endX, endY = xoffs + halfsize, yoffs + halfsize
        self.playCanvas.create_oval(startX, startY, endX, endY, fill='AntiqueWhite1', width=2, tag=PIECE_GUITAG)
        self.playCanvas.create_text(xoffs, yoffs, text=symbol, font=('calibri',halfsize) , fill=sideColor(symbol), tag=PIECE_GUITAG)

    def draw_lastmove(self, pos):
        canvas = self.playCanvas
        canvas.delete(LASTMOVE_GUITAG)
        if pos is None:
            return
        hs = int(self.gridsize/2)
        ct = self.gridCenter[pos[1]][pos[0]]
        for offs in ( (-1,-1), (1,-1), (-1,1), (1,1)):
            sx, sy = ct[0] + offs[0]*hs, ct[1] + offs[1]*hs
            canvas.create_line(sx, sy, sx - offs[0]*8, sy, fill='black', width=4, tags=LASTMOVE_GUITAG)
            canvas.create_line(sx, sy, sx, sy - offs[1]*8, fill='black', width=4, tags=LASTMOVE_GUITAG)

    def draw_movelist(self, movelist):
        self.playCanvas.delete(MOVE_GUITAG)
        obj = []
        for index, (start, end) in enumerate(movelist):
            if index > len(MOVE_COLOR):
                return
            obj.append(self.draw_move(start, end, MOVE_COLOR[index]))
        # loop in revered, the first index has highest raise
        while len(obj)>0:
            o = obj.pop()
            self.playCanvas.tag_raise(o)

    def draw_move(self, start, end, color):
        # print(f'drawmove {start} - {end} - {color}')
        startX, startY = self.gridCenter[start[1]][start[0]]
        endX, endY = self.gridCenter[end[1]][end[0]]
        return self.playCanvas.create_line(startX, startY, endX, endY,
                                    arrow=tk.LAST, width=3, 
                                    fill=color, tags=MOVE_GUITAG)

    def add_log(self, msg):
        self.logview.insert(tk.END, msg+'\n')
        pos = self.logview.vbar.get()
        if pos[1] > 0.95:
            self.logview.see(tk.END)

    def send_guicmd(self, action: GUIActionCmd, params):
        self.guiUpdateAction.put(GUIAction(action, params))

    def gui_handler(self):
        while True:
            try:
                act: GUIAction = self.guiUpdateAction.get_nowait()
            except queue.Empty:
                break

            try:
                match act.action:
                    case GUIActionCmd.Position:
                        self.draw_position(act.params[0])
                        self.draw_lastmove(act.params[1])
                    case GUIActionCmd.Moves:
                        self.draw_movelist(act.params)
                    case GUIActionCmd.MESSAGE:
                        self.add_log(act.params)
                    case _:
                        pass
            except:
                print(f'** Failed to updating GUI. {act}')
        self.guiUpdaterId = self.root.after(200, self.gui_handler)

    def quit_cleanup(self):
        print(f'quiting {self.guiUpdaterId}')
        self.root.after_cancel(self.guiUpdaterId)
        self.root.destroy()

    def loop(self):
        self.gui_handler()
        self.root.protocol('WM_DELETE_WINDOW', self.quit_cleanup)
        self.root.mainloop()
