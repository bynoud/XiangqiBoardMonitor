from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
import re, logging, threading

GRID_WIDTH = 9
GRID_HEIGHT = 10
PIECE_NAME = 'King Advisor Elephant Rook Cannon Horse Pawn'.split()

# Black -> lowercase
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

logger = logging.getLogger()

class Side(Enum):
    Unknow = 0
    White = 1
    Black = 2

    @property
    def opponent(self) -> Side:
        if self == Side.Unknow:
            return Side.Unknow
        if self == Side.Black:
            return Side.White
        return Side.Black
    
    @property
    def fen(self) -> str:
        if self == Side.White:
            return 'w'
        if self == Side.Black:
            return 'b'
        return 'u'
        # raise Exception('should not be called')
    
    def isSameSide(self, other: Side) -> bool:
        return False if other==Side.Unknow else other==self


class MonitorMsgSeverity(Enum):
    INFO = 0
    ERROR = 1
    FATAL = 2


def gen_fen(r: MonitorResult):
    # Start for highest rank
    fens = []
    rotate = r.mySide==Side.Black
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
            p = r.positions[row][col]
            if p == '.':
                spacecnt += 1
            else:
                fen = addfen(fen, p)
                spacecnt = 0
        fen = addfen(fen, '')
    return f'{"/".join(fens)}'

def board_str(r: MonitorResult):
    r = f'lastMove={r.moveSide} {r.lastMovePosition} me={r.mySide}\n'
    for row in r.positions:
        r += '|' + ' '.join(row) + '|\n'
    return r

class MonitorResult:

    def __init__(self) -> None:
        self.mySide: Side = Side.Unknow
        self.moveSide: Side = Side.Unknow
        self.positions = [['.' for i in range(GRID_WIDTH)] for j in range(GRID_HEIGHT)] # [ Y/row, X/col ]
        self.lastMovePosition = [] # [X/column, Y/row]
        self.lastMoveFrom = [] # [X/column, Y/row]

    @property
    def fen(self):
        try:
            return self._fen
        except:
            self._fen = gen_fen(self)
            return self._fen
        
    @property
    def fenfull(self):
        return f'{self.fen} {self.moveSide.opponent.fen} - - 0 1'

    def isSame(self, other: MonitorResult):
        return self.fenfull == other.fenfull
    
    def isSameMove(self, other: MonitorResult):
        if not self.lastMoveFrom or not other.lastMoveFrom:
            return False
        return self.lastMoveFrom == other.lastMoveFrom
    
    def isMyturn(self):
        return self.mySide.isSameSide(self.moveSide.opponent)

    def asstring(self):
        return (f'my={self.mySide} ' + 
                f'lastmove={self.moveSide} {self.lastMoveFrom}->{self.lastMovePosition} {self.fen}')

class BoardMonitorListener(ABC):
    @abstractmethod
    def on_monitor_msg(self, level: MonitorMsgSeverity, msg: str):
        pass
    @abstractmethod
    def on_board_updated(self, mon: MonitorResult):
        pass


# class LogAggregate:
#     idleCnt = {}
#     aggCnt = 10

#     def send_msg(self, msg):
#         try:
#             self.idleCnt[msg] += 1
#         except KeyError:
#             self.idleCnt[msg] = 1
#         if (self.idleCnt[msg] == 1):
#             logger.info(msg)
#             for l in self.eventListeners:
#                 l.on_monitor_error(msg)
#         if (self.idleCnt[msg] > 10):
#             self.idleCnt[msg] = 0
            

#===============================================================
from typing import Dict, List




class BaseMonitor(ABC):

    @abstractmethod
    def do_init(self, params) -> None:
        pass

    # return 0 if success, other to terminate the monitor
    @abstractmethod
    def do_board_scan(self) -> MonitorResult | None:
        pass

    eventListeners: List[BoardMonitorListener] = []
    stopPolling = False
    pollingStopped = threading.Event()
    engine_thread = None

    # def __init__(self) -> None:
    #     self.do_init(params)

    def add_event_listener(self, listener: BoardMonitorListener):
        self.eventListeners.append(listener)

    def send_msg(self, msg):
        for l in self.eventListeners:
            l.on_monitor_msg(MonitorMsgSeverity.INFO, msg)

    def send_error(self, msg):
        for l in self.eventListeners:
            l.on_monitor_msg(MonitorMsgSeverity.ERROR, msg)

    def send_fatal(self, msg):
        for l in self.eventListeners:
            l.on_monitor_msg(MonitorMsgSeverity.FATAL, msg)

    def send_board_update_event(self, result: MonitorResult):
        for l in self.eventListeners:
            l.on_board_updated(result)

    
    def start(self, params=None): #delaySecond=0.1):
        params = {'delaySecond':0.1, **(params or {})}
        # params = {'delaySecond':3, **(params or {})}
        self.stop()
        self.do_init(params)
        def polling():
            import time
            logger.info('ScreenMonitor started')
            while not self.stopPolling:
                # res = self.do_board_scan()
                try:
                    res = self.do_board_scan()
                except Exception as e:
                    logger.error(f'Error during board scan: {e}')
                    self.send_fatal('Error during board scan. Stop the app now')
                    break
                if res is not None:
                    self.send_board_update_event(res)
                time.sleep(params['delaySecond'])
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
