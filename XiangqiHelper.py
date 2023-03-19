import tkinter as tk
import tkinter.scrolledtext as tkst
import queue
from enum import Enum

from FairyfishUCIAdapter import Engine, EngineEventListener, Move
from BoardMonitor import BoardMonitor, BoardMonitorListener, Side

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

class XiangqiHelper(EngineEventListener, BoardMonitorListener):

    def __init__(self, gridsize=DEFAULT_SIZE) -> None:
        self.gridsize = gridsize
        self.help = True
        self.debugDepth = 8
        self.guiUpdateAction = queue.Queue()
        self.guiUpdaterId = None
        self.restartCount = 5

        self.build_gui()

    def start(self):
        self.restart_engine()
        self.loop()
        print('GUI exited')
        self.stop_engine()

    def stop_engine(self):
        try:
            self.engine.quit()
        except:
            pass
        try:
            self.monitor.stop()
        except:
            pass

    def restart_engine(self):
        try:
            self.stop_engine()
            self.lastFen = ''
            self.lastFenFull = ''
            self.engine = Engine()
            self.engine.add_event_listener(self)
            self.monitor = BoardMonitor()
            self.monitor.add_event_listener(self)
            self.engine.start()
            self.monitor.start()
            self.send_guicmd(GUIActionCmd.MESSAGE, 'Engine started')
            self.restartCount = 5
        except Exception as e:
            self.restartCount -= 1
            if self.restartCount <= 0:
                raise Exception('The engine cannot restart:', e)
            self.restart_engine()

        

    def build_gui(self):
        self.halfsize = int(self.gridsize/2)
        self.root = tk.Tk()
        self.gridCenter = [[None for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # [Y,X] = [row,col]
        self.playCanvas = self.draw_play_area()
        self.controlFrame = self.draw_controls()
        self.logview = self.draw_logview()


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
    
    def draw_controls(self):
        fr = tk.Frame(self.root)
        fr.grid_rowconfigure(0, weight=1)
        fr.grid_columnconfigure(1, weight=1)

        restartBtn = tk.Button(fr, text="RESTART", padx=20, pady=5, command=self.restart_engine)
        restartBtn.grid(row=0, column=0, sticky='ns')

        def forceMySideMoveNext():
            self.monitor.forceNextSide = self.monitor.mySide
            print(f'Force move side {self.monitor.forceNextSide}')
        getmoveBtn = tk.Button(fr, text='Myside', padx=10, pady=5, command=forceMySideMoveNext)
        getmoveBtn.grid(row=0, column=2, sticky='ns')

        mtVal = tk.IntVar(value=2)
        def mtUpdate(inc):
            cur = mtVal.get()
            if inc:
                cur += 1
            else:
                cur -= 1
            if cur < 15 and cur > 0:
                mtVal.set(cur)
                self.engine.set_movetime(cur * 1000)
                # print(f'Set Engine movetime = {cur} second')

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
        mtEntry.pack(side=tk.LEFT, ipadx=15)
        fr2.grid(row=0,column=3, sticky='ns')
        
        pvVal = tk.IntVar(value=1)
        def pvUpdate(inc):
            cur = pvVal.get()
            if inc:
                cur += 1
            else:
                cur -= 1
            if cur < 30 and cur > 0:
                pvVal.set(cur)
                self.engine.set_multipv(cur)

        pvFrame = tk.Frame(fr, padx=10, pady=5)
        pvEntry = tk.Entry(pvFrame, textvariable=pvVal, justify='center')
        pvButtonframe = tk.Frame(pvEntry)
        pvButtonframe.pack(side=tk.RIGHT)
        pvBtnUp = tk.Button(pvButtonframe, text="▲", font="none 5",
                            command=lambda: pvUpdate(True))
        pvBtnUp.pack(side=tk.TOP)
        pvBtnDown = tk.Button(pvButtonframe, text="▼", font="none 5",
                              command=lambda: pvUpdate(False))
        pvBtnDown.pack(side=tk.BOTTOM)
        pvEntry.pack(side=tk.LEFT, ipadx=15)
        pvFrame.grid(row=0,column=4, sticky='ns')
        

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


    # Monitor callback
    def on_board_updated(self, fen: str, moveSide: Side, lastmovePosition):
        if moveSide == Side.Unknow:
            if self.lastFen == fen:
                print(f'** Warning: Unkown move side with same fen. Ignored')
                return
            else:
                print(f'** Error: Unkown move side. Assume not is me')
                # self.gui.send_guicmd(GUIActionCmd.MESSAGE, '** Error: Unknown move side')
                moveSide = self.monitor.mySide

        self.lastFen = fen
        nextSide = moveSide.opponent

        # update gui
        self.send_guicmd(GUIActionCmd.Position, [self.monitor.positions, lastmovePosition])

        myturn = self.help and nextSide == self.monitor.mySide
        # no point to set position if we don't neef the move generate
        if myturn:
            self.lastFenFull = f'{fen} {nextSide.fen} - - 0 1'
            self.engine.start_next_move(self.lastFenFull)

    def on_monitor_error(self, msg):
        self.send_guicmd(GUIActionCmd.MESSAGE, msg)

    # Engine callback
    def on_move_calculated(self, fen, info: Move):
        if self.lastFenFull != fen:
            print(f'** Warn: Late arrival on move. Ignored. cur {self.lastFenFull} --- {fen}')
            # self.send_guicmd(GUIActionCmd.MESSAGE, '** Warn: Late arrival on move. Ignored')
            return
        if info is None:
            print('** Error: info is None')
            self.send_guicmd(GUIActionCmd.MESSAGE, '** Error: NO Bestmove')
            return
        print(info)
        moves = []
        for mv in info.iter_moves(self.debugDepth):
            try:
                moves.append( self.monitor.move_parse(mv) )
            except Exception as e:
                print(f'** Error: Failed to parse move "{mv}"')
                self.send_guicmd(GUIActionCmd.MESSAGE, f'** Error: Failed to parse move "{mv}"')
                print(e)
                break
        self.send_guicmd(GUIActionCmd.Moves, moves)
        self.send_guicmd(GUIActionCmd.MESSAGE, f'Bestmove: {info.bestmove}')
