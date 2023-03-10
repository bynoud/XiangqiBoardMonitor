
from FairyfishUCIAdapter import Engine, EngineEventListener
from BoardMonitor import BoardMonitor, BoardMonitorListener, Side
from HelperGUI import HelperGUI, GUIActionCmd, HelperGUIListener, GUIEventType
import re

START_POS = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"


class Helper(EngineEventListener, BoardMonitorListener, HelperGUIListener):

    def __init__(self) -> None:
        self.engine = Engine()
        self.engine.add_event_listener(self)
        self.monitor = BoardMonitor()
        self.monitor.add_event_listener(self)
        self.gui = HelperGUI()
        self.gui.add_event_listener(self)

        self.help = True
        self.debugDepth = 8
        self.lastFen = ''
        self.lastFenFull = ''


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
        self.gui.send_guicmd(GUIActionCmd.Position, [self.monitor.positions, lastmovePosition])

        myturn = self.help and nextSide == self.monitor.mySide
        # no point to set position if we don't neef the move generate
        if myturn:
            self.lastFenFull = f'{fen} {nextSide.fen} - - 0 1'
            self.engine.start_next_move(self.lastFenFull)

    def on_monitor_error(self, msg):
        self.gui.send_guicmd(GUIActionCmd.MESSAGE, msg)

    def on_move_calculated(self, fen, score, info):
        if self.lastFenFull != fen:
            print(f'** Warn: Late arrival on move. Ignored. cur {self.lastFenFull} --- {fen}')
            self.gui.send_guicmd(GUIActionCmd.MESSAGE, '** Warn: Late arrival on move. Ignored')
            return
        if info is None:
            print('** Error: info is None')
            self.gui.send_guicmd(GUIActionCmd.MESSAGE, '** Error: NO Bestmove')
            return
        print(f'[{score}] {info["pv"][:self.debugDepth]}')
        moves = []
        for mv in info["pv"][:self.debugDepth]:
            try:
                moves.append( self.monitor.move_parse(mv) )
            except Exception as e:
                print(f'** Error: Failed to parse move "{mv}"')
                self.gui.send_guicmd(GUIActionCmd.MESSAGE, f'** Error: Failed to parse move "{mv}"')
                print(e)
                return
        self.gui.send_guicmd(GUIActionCmd.Moves, moves)
        self.gui.send_guicmd(GUIActionCmd.MESSAGE, f'Bestmove: {score} {info["pv"][:2]}')

    def on_gui_event(self, action: GUIEventType, params=None):
        match action:
            case GUIEventType.ForceMySideNextMove:
                self.monitor.forceNextSide = self.monitor.mySide
                print(f'Force move side {self.monitor.forceNextSide}')
            case GUIEventType.SetMoveTime:
                self.engine.movetime = params * 1000
                print(f'Set Engine movetime = {params} second')
            case _: print(f'** Error: unknown GUI action {action}')

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