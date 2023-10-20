# import tkinter as tk
# import tkinter.scrolledtext as tkst
import queue, logging
from enum import Enum
from abc import ABC, abstractmethod

from EngineUCI import Engine, EngineEventListener, Move
from BoardMonitor.BaseMonitor import *

logger = logging.getLogger()

class GUIActionCmd(Enum):
    Empty = 0
    Position = 1
    Moves = 2
    Message = 3
    Fatal = 4

class GUIAction:
    def __init__(self, action: GUIActionCmd, params=None) -> None:
        self.action = action
        self.params = params

class LogAggregate:
    idleCnt = {}
    aggCnt = 40

    # True if message should print out
    def send_msg(self, msg):
        try:
            self.idleCnt[msg] += 1
        except KeyError:
            self.idleCnt[msg] = 1
        if (self.idleCnt[msg] == 1):
            return True
        if (self.idleCnt[msg] > self.aggCnt):
            self.idleCnt[msg] = 0
        return False
            

def move_parse(side: Side, mv):
    m = MOVE_PTN.match(mv)
    sx, sy = FILE2NUM[m.group(1)], int(m.group(2))
    ex, ey = FILE2NUM[m.group(3)], int(m.group(4))
    if side==Side.Black:
        return [ [GRID_WIDTH-sx, sy-1], [GRID_WIDTH-ex, ey-1] ]
    else:
        return [ [sx-1, GRID_HEIGHT-sy], [ex-1, GRID_HEIGHT-ey] ]


class HelperEngine(EngineEventListener, BoardMonitorListener, ABC):

    def __init__(self, MonitorCls = BaseMonitor) -> None:
        self.MonitorCls = MonitorCls

        self.help = True
        self.debugDepth = 8

        self.lastFenFull = ''
        self.mySideMoveNext = False
        self.lastMonitor = MonitorResult()
        self.lastMovelist = []

        self.engine: Engine = None
        self.monitor: BaseMonitor = None

        self.guiOptions = dict(movetime=2, multipv=1)
        # self.guiUpdateAction = queue.Queue()
        self.logagg = LogAggregate()

    def set_option(self, name, value):
        if name not in self.guiOptions:
            logging.warning(f'Unknow option {name}')
            return
        if value != self.guiOptions[name]:
            self.guiOptions[name] = value
            match name:
                case 'movetime':
                    self.engine.set_movetime(value)
                case 'multipv':
                    self.engine.set_multipv(value)
                case _:
                    logging.warning(f'Unknow option {name}')

    def stop(self):
        try:
            self.engine.quit()
            logger.info('Engine stopped')
        except:
            pass
        try:
            self.monitor.stop()
            logger.info('Monitor stopped')
        except:
            pass

    def start(self, restart=False, mon_params=None):
        self.stop()
        print('staring...')

        self.engine = Engine()
        self.engine.add_event_listener(self)
        self.engine.start()
        self.add_log('Engine started')

        self.monitor = self.MonitorCls()
        self.monitor.add_event_listener(self)
        self.monitor.start(mon_params)
        self.add_log('Monitor started')

    def forceMySideMoveNext(self):
        self.lastFenFull = ''
        self.mySideMoveNext = True
        self.lastMonitor = MonitorResult()
        self.add_log('Forced my side move next')

    # def send_guicmd(self, action: GUIActionCmd, params):
    #     # if not self.handle_guicmd(action, params):
    #     #     self.guiUpdateAction.put(GUIAction(action, params))
    #     try:
    #         match action:
    #             case GUIActionCmd.Position:
    #                 self.update_position(params[0], params[1], params[2])
    #             case GUIActionCmd.Moves:
    #                 self.update_movelist(params)
    #             case GUIActionCmd.Message:
    #                 self.add_log(params)
    #             case GUIActionCmd.Message:
    #                 self.set_fatal(params)
    #             case _:
    #                 logger.error(f'** Unknown CMD {action}')
    #     except:
    #         logger.error(f'** Failed to updating GUI. {action} {params}')

    # @abstractmethod
    # def handle_guicmd(self, action: GUIActionCmd, params):
    #     return False

    # def execute_gui_cmd(self):
    #     while True:
    #         try:
    #             act: GUIAction = self.guiUpdateAction.get_nowait()
    #         except queue.Empty:
    #             break

    #         try:
    #             match act.action:
    #                 case GUIActionCmd.Position:
    #                     self.update_position(act.params[0], act.params[1], act.params[2])
    #                 case GUIActionCmd.Moves:
    #                     self.update_movelist(act.params)
    #                 case GUIActionCmd.Message:
    #                     self.add_log(act.params)
    #                 case _:
    #                     logger.error(f'** Unknown CMD {act}')
    #         except:
    #             logger.warning(f'** Failed to updating GUI. {act}')


    # Monitor callback

    def on_monitor_msg(self, level: MonitorMsgSeverity, msg: str):
        agg = self.logagg.send_msg(f'{level} {msg}')
        match level:
            case MonitorMsgSeverity.INFO:
                if agg:
                    self.add_log(msg)
            case MonitorMsgSeverity.ERROR:
                if agg:
                    logger.error(msg)
            case MonitorMsgSeverity.FATAL:
                self.set_fatal(msg)
            case _:
                logger.error(f'Unknow error level {level} {msg}')

    def on_board_updated(self, result: MonitorResult):
        # logger.info(f'updateboard {fen} {moveSide} {lastmovePosition} {lastMoveFrom} {forceMove}')
        if self.mySideMoveNext:
            result.moveSide = result.mySide
            self.lastMonitor = MonitorResult()

        if self.lastMonitor.isSame(result):
            return
        
        logger.info(f'updateboard {result.asstring()}')
        
        if self.lastMonitor.isSameMove(result):
            logger.warning(f'Seem wrong detect on lastmove -> ignored')
            return

        self.lastMonitor = result
        # self.send_guicmd(GUIActionCmd.Position, result)
        # self.update_position(result)
        if result.isMyturn() and self.help:
            self.lastMovelist = [] # clear current movelist
            self.lastFenFull = result.fenfull
            self.engine.start_next_move(self.lastFenFull)
        self.update_gui()

    # Engine callback
    def on_move_calculated(self, fen, info: Move):
        if self.lastFenFull != fen:
            logger.info(f'Late arrival on move. Ignored. cur {self.lastFenFull} --- {fen}')
            # self.send_msg('** Warn: Late arrival on move. Ignored')
            return
        if info is None:
            logger.warning('info is None')
            self.add_log('** Error: NO Bestmove')
            return
        logger.info(info)
        moves = []
        for mv in info.iter_moves(self.debugDepth):
            try:
                moves.append( move_parse(self.lastMonitor.mySide, mv) )
            except Exception as e:
                logger.error(f'Failed to parse move "{mv}": {e}')
                # self.send_msg(f'** Error: Failed to parse move "{mv}"')
                break
        # self.send_guicmd(GUIActionCmd.Moves, moves)
        # self.update_movelist(moves)
        self.lastMovelist = moves
        self.add_log(f'Bestmove: {info.bestmove}')
        self.update_gui()

    # def update_position(self, result: MonitorResult):
    #     self.lastPosition = positions
    #     self.lastmove = [] if lastmove is None else [lastmove[0],lastmove[1]]
    #     if newturn:
    #         self.lastMovelist = [] # clear movelist in new turn
    #     self.update_gui()

    # def update_movelist(self, movelist):
    #     self.lastMovelist = movelist
    #     self.update_gui()

    def on_engine_fatal(self, msg):
        logger.error(f'Engine fatal: {msg}. Restarting')
        self.add_log(f'Engine fatal, restarting...')
        self.start(restart=True)

    # @abstractmethod
    # def update_position(self, result: MonitorResult):
    #     pass

    # @abstractmethod
    # def update_movelist(self, movelist):
    #     pass

    @abstractmethod
    def update_gui(self):
        pass

    @abstractmethod
    def add_log(self, msg):
        pass

    @abstractmethod
    def set_fatal(self, msg):
        pass
