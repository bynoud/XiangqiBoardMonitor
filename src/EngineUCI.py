from queue import Queue, Empty
from collections.abc import Iterable
from abc import ABC, abstractmethod
from enum import Enum
from typing import List
import time, sys, logging
import subprocess
import threading

from pprint import PrettyPrinter

logger = logging.getLogger()

DEFAULT_OPT = {'UCI_Variant':'xiangqi', 'UCI_Elo': 2850}
ENGINE_EXE_NAME = 'fairy-stockfish_x86-64-bmi2.exe'
# DEFAULT_ENGPATH = 'engine_exe/fairy-stockfish_x86-64-bmi2.exe'

DEBUG_INFO= dict(id=0)
def get_debid():
    DEBUG_INFO['id'] = DEBUG_INFO['id']+1
    return DEBUG_INFO['id']

try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    DEFAULT_ENGPATH = f'{sys._MEIPASS}/engine_exe/{ENGINE_EXE_NAME}'
except Exception:
    DEFAULT_ENGPATH = f'./engine_exe/{ENGINE_EXE_NAME}'

INFO_KEYWORDS = {'depth': int, 'seldepth': int, 'multipv': int, 'nodes': int, 'nps': int, 'time': int, 'score': list, 'pv': list}
class Move:
    def __init__(self, info) -> None:
        self.info = info
        self.pv: List[str] = info.get('pv', ['NoMove'])
        score = info.get('score', ('NoMove',-100000000))
        self.scoreUnit = score[0]
        self.score = int(score[1])
    
    # @property
    # def firstmove(self):
    #     return self.pv[0]
    # @property
    # def ponder(self):
    #     return None if len(self.pv) < 2 else self.pv[1]
    # @property.setter
    # def ponder(self, val):
    #     if ()
    #     self.pv[1] = val

    def __str__(self) -> str:
        return f'{self.scoreUnit} {self.score} {self.pv}'

    @property
    def depth(self):
        return len(self.pv)
    @property
    def bestmove(self):
        return f'[{self.scoreUnit} {self.score}] {self.pv[:2]}'
    
    def iter_moves(self, num=-1):
        num = num if num>0 else len(self.pv)
        for m in self.pv[:num]:
            yield m

    def match(self, bestmove) -> bool:
        if len(self.pv) < 2:
            self.pv.append(bestmove[1])
        m1 = self.pv[0] == bestmove[0]
        m2 = True if bestmove[1] is None else bestmove[1]==self.pv[1]
        return (m1 and m2)

    @classmethod
    def parse(cls, items):
        if len(items) > 1 and items[0] == 'info' and items[1] != 'string':
            key = None
            values = []
            info = {}
            for i in items[1:] + ['']:
                if not i or i in INFO_KEYWORDS:
                    if key:
                        if values and not issubclass(INFO_KEYWORDS[key], Iterable):
                            values = values[0]
                        info[key] = INFO_KEYWORDS[key](values)
                    key = i
                    values = []
                else:
                    values.append(i)
            if 'score' in info:
                return Move(info)
            else:
                return None
        return None

def parse_movelist(infos: List[Move], bestmove):
    selinfo = None
    # lastScore = ('NoMove', -10000000000)
    # explen = 1 if bestmove[1] is None else 2
    for info in infos:
        # pv = info.get('pv', [])
        # if len(pv) < explen:
        #     continue
        # if pv[:explen] != list(bestmove[:explen]):
        #     continue
        if not info.match(bestmove):
            continue
        # score = info.get('score',('NoMove',-100000000))
        # score[1] = int(score[1])
        if ((selinfo is None) or
            (info.depth > selinfo.depth and (info.score > 0 or info.score >= selinfo.score))):
            selinfo = info

    if selinfo is None:
        logger.warning(f'Info none {bestmove} {infos}')
    return selinfo


# def parse_info(items):
#     if len(items) > 1 and items[0] == 'info' and items[1] != 'string':
#         key = None
#         values = []
#         info = {}
#         for i in items[1:] + ['']:
#             if not i or i in INFO_KEYWORDS:
#                 if key:
#                     if values and not issubclass(INFO_KEYWORDS[key], Iterable):
#                         values = values[0]
#                     info[key] = INFO_KEYWORDS[key](values)
#                 key = i
#                 values = []
#             else:
#                 values.append(i)
#         return info
#     return None

class EngineEventListener(ABC):
    @abstractmethod
    def on_move_calculated(self, fen, info):
        pass
    @abstractmethod
    def on_engine_fatal(self, msg):
        pass

class EngineCmdType(Enum):
    Quit = 0
    SetFen = 1
    SetMovetime = 2
    SetMultipv = 3
class EngineCmd:
    def __init__(self, action: EngineCmdType, params=None) -> None:
        self.action = action
        self.params = params
    def __str__(self) -> str:
        return f'{self.action} params={self.params}'

class Engine():

    def __init__(self, enginePath=DEFAULT_ENGPATH, options=None):
        self.debid = get_debid()
        self.enginePath = enginePath
        self.options = DEFAULT_OPT if options is None else {**DEFAULT_OPT, **options}
        self.uci_movetime = 2000
        self.uci_multipv = 1
        self.eventListeners: List[EngineEventListener] = []

        self.commandQueue = Queue()
        self.activefen = Queue(1)
        self.timeoutqueue = Queue()

        try:
            self.process = subprocess.Popen([self.enginePath],
                                            stdin=subprocess.PIPE, 
                                            stdout=subprocess.PIPE, 
                                            universal_newlines=True)
        except:
            logger.fatal(f'Engine cannot start from paht {self.enginePath}')
            exit()
        self.pprinter = PrettyPrinter()
        self.lock = threading.Lock()
        self.paused = False
        self.stopping = False

    def add_event_listener(self, listener: EngineEventListener):
        self.eventListeners.append(listener)

    def write(self, message):
        with self.lock:
            self.process.stdin.write(message)
            self.process.stdin.flush()

    def write_nolock(self, *messages):
        for msg in messages:
            self.process.stdin.write(msg)
            self.process.stdin.flush()

    def setoption(self, name, value):
        self.write('setoption name {} value {}\n'.format(name, value))

    def initialize(self):
        logger.info('Engine init')
        message = 'uci\n'
        for option, value in self.options.items():
            message += 'setoption name {} value {}\n'.format(option, value)
        self.write(message)

    def newgame(self):
        self.write('ucinewgame\n')

    def position(self, fen=None, moves=None, newgame=False):
        if newgame:
            self.write('ucinewgame\n')
        fen = 'fen {}'.format(fen) if fen else 'startpos'
        moves = 'moves {}'.format(' '.join(moves)) if moves else ''
        self.write('position {} {}\n'.format(fen, moves))

    def analyze(self):
        self.write('go infinite\n')
        self.paused = False

    def stop_seach(self):
        self.write('stop\n')
        self.paused = True

    def toggle(self):
        if self.paused:
            self.analyze()
        else:
            self.stop_seach()


    def read(self):
        while self.process.poll() is None:
            yield self.process.stdout.readline()


    def start(self):
        self.stopping = False
        self.start_output_handler()
        self.start_cmd_handler()
        self.start_timeout_check()

    def quit(self):
        self.stopping = True
        self.send_cmd(EngineCmdType.Quit)
        # self.write('quit\n')

    def send_event_fatal(self, msg):
        if self.stopping:
            return
        for l in self.eventListeners:
            l.on_engine_fatal(msg)

    def start_timeout_check(self):
        def check():
            while True:
                x = self.timeoutqueue.get()
                logger.info(f'Timeout check start {self.debid} {x}')
                try:
                    x2 = self.timeoutqueue.get(timeout=20)
                    if x2 != x:
                         logger.fatal(f'Timeout mismtach "{x}" "{x2}"')
                         exit()
                    else:
                        logger.info(f'Timeout check done {self.debid} {x}')
                except Empty:
                    # logger.error(f'Timeout for "{x}"')
                    # raise Exception(f'** Error: Timeout for "{x}"')
                    self.send_event_fatal(f'Timeout for "{x}"')
                    break
                    # break
        threading.Thread(target=check, daemon=True).start()

    def send_cmd(self, action: EngineCmdType, params=None):
        self.commandQueue.put(EngineCmd(action, params))

    def wait_next_cmd(self):
        while True:
            cmd: EngineCmd = self.commandQueue.get()

            if cmd.action == EngineCmdType.Quit:
                logger.info('Adapter execute finished')
                self.write_nolock('stop\n', 'quit\n')
                return
            
            precmd = None
            while cmd.action == EngineCmdType.SetFen:
                if precmd is not None:
                    logger.warning(f'** Warning : CMD ignored {cmd}')
                precmd = cmd
                try:
                    cmd = self.commandQueue.get_nowait()
                except Empty:
                    cmd = None
                    break

            if precmd is not None:
                yield precmd
            if cmd is not None:
                yield cmd


    def start_cmd_handler(self):
        def fen_execute():
            for cmd in self.wait_next_cmd():
                match cmd.action:
                    case EngineCmdType.SetFen:
                        self.set_fen(cmd.params)
                    case EngineCmdType.SetMovetime:
                        self.uci_movetime = int(cmd.params)*1000
                        logger.info(f'[Engine] set movetime = {self.uci_movetime}')
                    case EngineCmdType.SetMultipv:
                        self.uci_multipv = cmd.params
                        self.write_nolock(f'setoption name MultiPV value {self.uci_multipv}\n')
                        logger.info(f'[Engine] set multipv = {self.uci_multipv}')
                    case _:
                        logger.warning(f'unknow cmd {cmd.action}')

        threading.Thread(target=fen_execute, daemon=True).start()

    def set_fen(self, fen):
        # dont need the lock, we only handle the UCI in one thread
        self.write_nolock('stop\n')
        # this will be blocked until the last active fen got the bestmove
        logger.info(f'Start process move {self.debid} "{fen}"')
        self.timeoutqueue.put(fen) # start timeout
        self.activefen.put(fen)
        self.timeoutqueue.put(fen) # stop timeout
        logger.info(f'Get move for {self.debid} {self.uci_movetime} "{fen}" ...')
        self.write_nolock('ucinewgame\n',
                          f'position fen {fen}\n',
                          f'go movetime {self.uci_movetime}\n')
        time.sleep(0.1) # we need to make sure the UCI receive the 'go' command, not sure what is the best way...

    def start_output_handler(self):
        def read_output():
            infos = []
            logfile = open('debug.log', 'w')
            try:
                # for line in self.read():
                repeatcnt = 0
                while not self.stopping:
                    line = self.process.stdout.readline()
                    logfile.write(line)
                    if line=='':
                        repeatcnt += 1
                        if repeatcnt > 100:
                            # logger.warn(f'Failed here')
                            self.send_event_fatal('UCI output empty')
                            break
                    else:
                        repeatcnt = 0
                    items = line.split()
                    if len(items) == 0:
                        continue
                    if items[0] == 'info':
                        info = Move.parse(items)
                        if info:
                            infos.append(info)
                    elif items[0] == 'bestmove':
                        bestmove, ponder = items[1], None if len(items)<4 else items[3]
                        try:
                            fen = self.activefen.get_nowait()
                            logger.info(f'Found bestmove for "{fen}" {bestmove} {ponder}')
                            info = parse_movelist(infos, (bestmove, ponder)) 
                            self.send_move_calculated_event(fen, info)
                            infos = []
                        except Empty:
                            logger.warning(f'Receiving bestmove log where not expected {bestmove} {ponder}')
                        
            except RuntimeError:
                pass

            logger.warning('Adapter thread closed')
            logfile.close()

        # def read_error():
        #     while self.process.poll() is None:
        #         err = self.process.stderr.readline()
        #         logger.info(f'UCI error: {err}')

        threading.Thread(target=read_output, daemon=True).start()
        # threading.Thread(target=read_error, daemon=True).start()
        self.initialize()

    def send_move_calculated_event(self, fen, info):
        for l in self.eventListeners:
            l.on_move_calculated(fen, info)

    def start_next_move(self, fen):
        self.send_cmd(EngineCmdType.SetFen, fen)
    def set_movetime(self, val):
        self.send_cmd(EngineCmdType.SetMovetime, val)
    def set_multipv(self, val):
        self.send_cmd(EngineCmdType.SetMultipv, val)

    def pp(self, x):
        self.pprinter(x)
