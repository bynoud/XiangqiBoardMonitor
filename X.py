
from FairyfishUCIAdapter import Engine
from BoardMonitor import BoardMonitor, GRID_HEIGHT
from HelperGUI import HelperGUI, GUIActionCmd
import re

START_POS = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"
MOVE_PTN = re.compile(r'([a-z])(\d+)([a-z])(\d+)')

FILE2NUM = dict(a=0,b=1,c=2,d=3,e=4,f=5,g=6,h=7,i=8)
    
def move_parse(mv):
    m = MOVE_PTN.match(mv)
    return ( ( FILE2NUM[m.group(1)], GRID_HEIGHT-int(m.group(2)) ),
             ( FILE2NUM[m.group(3)], GRID_HEIGHT-int(m.group(4)) ) )

class Helper:

    def __init__(self) -> None:
        self.engine = Engine()

        self.monitor = BoardMonitor()
        self.monitor.add_event_listener(self)

        self.gui = HelperGUI()

        self.help = True
        self.debugDepth = 8
        self.lastFen = ''
        self.nextMoveSide = 'White'


    def start(self):
        try:
            self.engine.start()
        except:
            self.engine = Engine()
            self.engine.start()
        self.monitor.start()

        self.gui.loop()
        print('GUI exited')
        self.stop()

    def on_board_updated(self, fen, nextMoveSide):
        # Stockfish is stateless, so no need for newgame?
        # if fen==START_POS:
        #     self.engine.newgame()
        fen = f'{fen} {nextMoveSide[0].lower()} - - 0 1'
        # print(fen)
        self.nextMoveSide = nextMoveSide

        # update gui
        self.gui.send_guicmd(GUIActionCmd.Position, self.monitor.positions)

        myturn = self.help and nextMoveSide == self.monitor.mySide
        # no point to set position if we don't neef the move generate
        if myturn:
            self.lastFen = fen
            self.engine.set_fen(fen, self)

    def on_monitor_error(self, msg):
        self.gui.send_guicmd(GUIActionCmd.MESSAGE, msg)

    def on_move_caculated(self, fen, score, info):
        if self.lastFen != fen:
            print('** Warn: Late arrival on move. Ignored')
            self.gui.send_guicmd(GUIActionCmd.MESSAGE, '** Warn: Late arrival on move. Ignored')
            return
        if info is None:
            print('** Error: info is None')
            self.gui.send_guicmd(GUIActionCmd.MESSAGE, '** Error: info is None')
            return
        print(f'[{score}] {info["pv"][:self.debugDepth]}')
        moves = []
        for mv in info["pv"][:self.debugDepth]:
            try:
                moves.append( move_parse(mv) )
            except Exception as e:
                print(f'** Error: Failed to parse move "{mv}"')
                self.gui.send_guicmd(GUIActionCmd.MESSAGE, f'** Error: Failed to parse move "{mv}"')
                print(e)
        self.gui.send_guicmd(GUIActionCmd.Moves, moves)
        self.gui.send_guicmd(GUIActionCmd.MESSAGE, f'Bestmove: {info["pv"][:2]}')


    def clear(self):
        self.monitor.clear_board()

    def stop(self):
        try:
            self.engine.quit()
        except:
            pass
        self.monitor.stop()
        

def start():
    h = Helper()
    h.start()
    return h