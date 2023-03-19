import tkinter as tk
import tkinter.scrolledtext as tkst
import queue
from enum import Enum

from FairyfishUCIAdapter import Engine, EngineEventListener, Move
from BoardMonitor import BoardMonitor, BoardMonitorListener, Side, MonitorFatal

GRID_HEIGHT = 10
GRID_WIDTH = 9

class GUIActionCmd(Enum):
    Empty = 0
    Position = 1
    Moves = 2
    Message = 3

class GUIAction:
    def __init__(self, action: GUIActionCmd, params=None) -> None:
        self.action = action
        self.params = params

class HelperEngine(EngineEventListener, BoardMonitorListener):

    def __init__(self) -> None:
        self.help = True
        self.debugDepth = 8
        self.guiOptions = dict(movetime=2, multipv=1)
        self.guiUpdateAction = queue.Queue()

    def send_msg(self, msg):
        self.send_guicmd(GUIActionCmd.Message, msg)

    def set_option(self, name, value):
        if name not in self.guiOptions:
            print(f'** [Helper] Error: Unknow option {name}')
            return
        if value != self.guiOptions[name]:
            self.guiOptions[name] = value
            match name:
                case 'movetime':
                    self.engine.set_movetime(value)
                case 'multipv':
                    self.engine.set_multipv(value)
                case _:
                    print(f'** [Helper] Unknow option {name}')


    def stop(self):
        try:
            self.engine.quit()
            print('Engine stopped')
        except:
            pass
        try:
            self.monitor.stop()
            print('Monitor stopped')
        except:
            pass

    def restart(self, retry=5):
        try:
            self.stop()
            self.lastFen = ''
            self.lastFenFull = ''
            self.engine = Engine()
            self.engine.add_event_listener(self)
            self.monitor = BoardMonitor()
            self.monitor.add_event_listener(self)
            self.engine.start()
            self.monitor.start()
            self.send_msg('Engine started')
            self.restartCount = 5
        except Exception as e:
            retry -= 1
            if retry <= 0:
                raise Exception('The engine cannot restart:', e)
            self.restart(retry)


    def send_guicmd(self, action: GUIActionCmd, params):
        self.guiUpdateAction.put(GUIAction(action, params))

    def execute_gui_cmd(self):
        while True:
            try:
                act: GUIAction = self.guiUpdateAction.get_nowait()
            except queue.Empty:
                break

            try:
                match act.action:
                    case GUIActionCmd.Position:
                        self.update_position(act.params[0], act.params[1])
                    case GUIActionCmd.Moves:
                        self.update_movelist(act.params)
                    case GUIActionCmd.Message:
                        self.add_log(act.params)
                    case _:
                        pass
            except:
                print(f'** Failed to updating GUI. {act}')


    # Monitor callback
    def on_board_updated(self, fen: str, moveSide: Side, lastmovePosition):
        if moveSide == Side.Unknow:
            if self.lastFen == fen:
                print(f'** Warning: Unkown move side with same fen. Ignored')
                return
            else:
                print(f'** Error: Unkown move side. Assume not is me')
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
        self.send_msg(msg)

    def on_monitor_fatal(self, type: MonitorFatal):
        self.send_msg(type.name)

    # Engine callback
    def on_move_calculated(self, fen, info: Move):
        if self.lastFenFull != fen:
            print(f'** Warn: Late arrival on move. Ignored. cur {self.lastFenFull} --- {fen}')
            # self.send_msg('** Warn: Late arrival on move. Ignored')
            return
        if info is None:
            print('** Error: info is None')
            self.send_msg('** Error: NO Bestmove')
            return
        print(info)
        moves = []
        for mv in info.iter_moves(self.debugDepth):
            try:
                moves.append( self.monitor.move_parse(mv) )
            except Exception as e:
                print(f'** Error: Failed to parse move "{mv}"')
                self.send_msg(f'** Error: Failed to parse move "{mv}"')
                print(e)
                break
        self.send_guicmd(GUIActionCmd.Moves, moves)
        self.send_msg(f'Bestmove: {info.bestmove}')

    def update_position(self, positions, lastmove):
        pass
        # self.clear_pieces()
        # for x in range(GRID_WIDTH):
        #     for y in range(GRID_HEIGHT):
        #         p = positions[y][x]
        #         if p == '.':
        #             continue
        #         self.draw_piece(positions[y][x], x, y)

    def update_movelist(self, movelist):
        pass
        # self.clear_movelist()
        # for index, (start, end) in enumerate(movelist):
        #     if index > self.debugDepth:
        #         return
        #     self.draw_move(index, start, end)

    # add a log
    def add_log(self, msg):
        pass
