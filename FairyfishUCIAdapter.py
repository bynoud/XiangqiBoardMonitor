from queue import Queue, Empty
from collections.abc import Iterable
from abc import ABC, abstractmethod
from typing import List
import time
import subprocess
import threading

from pprint import PrettyPrinter

DEFAULT_OPT = {'UCI_Variant':'xiangqi', 'UCI_Elo': 2850}
DEFAULT_ENGPATH = 'fairy-stockfish-largeboard_x86-64-bmi2.exe'

def parse_movelist(infos, bestmove):    
    selinfo = None
    lastScore = ('NoMove', -10000000000)
    explen = 1 if bestmove[1] is None else 2
    for info in infos:
        pv = info.get('pv', [])
        if len(pv) < explen:
            continue
        if pv[:explen] != list(bestmove[:explen]):
            continue
        score = info.get('score',('NoMove',-100000000))
        score[1] = int(score[1])
        if (selinfo is None) or \
            (len(pv) > len(selinfo.get('pv',[])) and (score[1] > 0 or score[1] >= lastScore[1])):
            selinfo = info
            lastScore = score

    if selinfo is None:
        print(f'** Error: Info none {bestmove} {infos}')
    return lastScore, selinfo


INFO_KEYWORDS = {'depth': int, 'seldepth': int, 'multipv': int, 'nodes': int, 'nps': int, 'time': int, 'score': list, 'pv': list}
def parse_info(items):
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
        return info
    return None

class EngineEventListener(ABC):
    @abstractmethod
    def on_move_calculated(seld, fen, score, info):
        pass

class Engine():

    def __init__(self, enginePath=DEFAULT_ENGPATH, options=None):
        self.enginePath = enginePath
        self.options = DEFAULT_OPT if options is None else {**DEFAULT_OPT, **options}
        self.movetime = 2000
        self.eventListeners: List[EngineEventListener] = []

        self.fenlist = Queue()
        self.activefen = Queue(1)
        self.timeoutqueue = Queue()

        self.process = subprocess.Popen([self.enginePath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        self.multipv = Queue()
        self.pprinter = PrettyPrinter()
        self.lock = threading.Lock()
        self.paused = False
        self.stopping = False

    def add_event_listener(self, listener: EngineEventListener):
        self.eventListeners.append(listener)

    def write(self, message):
        with self.lock:
            # print(f'UCI: {message}', end='')
            self.process.stdin.write(message)
            self.process.stdin.flush()

    def write_nolock(self, *messages):
        for msg in messages:
            # print(f'UCI: {msg}', end='')
            self.process.stdin.write(msg)
            self.process.stdin.flush()
        # try:
        #     with self.lock:
        #         self.process.stdin.write(message)
        #         self.process.stdin.flush()
        # except Exception as e:
        #     if retry:
        #         self.reset()
        #         self.start()
        #         self.write(message, retry=False)
        #     else:
        #         raise(e)

    def setoption(self, name, value):
        self.write('setoption name {} value {}\n'.format(name, value))

    def initialize(self):
        print('Engine init')
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
        self.start_fenlist_handler()
        self.start_timeout_check()

    def quit(self):
        self.stopping = True
        self.fenlist.put(None)
        # self.write('quit\n')


    def start_timeout_check(self):
        def check():
            while True:
                x = self.timeoutqueue.get()
                time.sleep(10)
                try:
                    self.timeoutqueue.get_nowait()
                except Empty:
                    print(f'** Error: Timeout for "{x}"')
                    break
        threading.Thread(target=check, daemon=True).start()


    def start_fenlist_handler(self):
        def fen_execute():
            while True:
                fen = self.fenlist.get()
                if fen is None:
                    print('Fen execute finished')
                    self.write_nolock('stop\n', 'quit\n')
                    break

                try:
                    nxtfen = self.fenlist.get_nowait()
                    print(f'** Warning: Ignore fen "{fen}"')
                    fen = nxtfen
                except Empty:
                    pass

                # dont need the lock, we only handle the UCI in this thread
                self.write_nolock('stop\n')

                # this will be blocked until the last active fen got the bestmove
                self.timeoutqueue.put(fen) # start timeout
                self.activefen.put(fen)
                self.timeoutqueue.put(fen) # stop timeout
                print(f'Get move for {self.movetime} "{fen}" ...')
                self.write_nolock('ucinewgame\n',   # should we need this?
                                f'position fen {fen}\n',
                                f'go movetime {self.movetime}\n')
                time.sleep(0.2) # we need to make sure the UCI receive the 'go' command, not sure what is the best way...

        threading.Thread(target=fen_execute, daemon=True).start()

    def start_output_handler(self):
        def read_output():
            infos = []
            logfile = open('debug.log', 'w')
            try:
                # for line in self.read():
                lastline = ''
                repeatcnt = 0
                while not self.stopping:
                    line = self.process.stdout.readline()
                    logfile.write(line)
                    # print("OUT: ", line, end='')
                    if line==lastline:
                        repeatcnt += 1
                        if repeatcnt > 100:
                            print(f'Failed here')
                            break
                    items = line.split()
                    if len(items) == 0:
                        continue
                    if items[0] == 'info':
                        info = parse_info(items)
                        if info and 'score' in info:
                            infos.append(info)
                    elif items[0] == 'bestmove':
                        bestmove, ponder = items[1], None if len(items)<4 else items[3]
                        try:
                            fen = self.activefen.get_nowait()
                            print(f'Found bestmove for "{fen}" {bestmove} {ponder}')
                            score, info = parse_movelist(infos, (bestmove, ponder)) 
                            self.send_move_calculated_event(fen, score, info)
                            infos = []
                        except Empty:
                            print(f'** Error: receiving bestmove log where not expected {bestmove} {ponder}')
                        
            except RuntimeError:
                pass

            print('** Warn: Adapter thread closed')
            logfile.close()

        # def read_error():
        #     while self.process.poll() is None:
        #         err = self.process.stderr.readline()
        #         print(f'UCI error: {err}')

        threading.Thread(target=read_output, daemon=True).start()
        # threading.Thread(target=read_error, daemon=True).start()
        self.initialize()

    def send_move_calculated_event(self, fen, score, info):
        for l in self.eventListeners:
            l.on_move_calculated(fen, score, info)

    def start_next_move(self, fen):
        self.fenlist.put(fen)

    def pp(self, x):
        self.pprinter(x)

# class C:
#     d = 10
#     def f1(self, a, b):
#         time.sleep(5)
#         print("f1", a, b, self.d)
#     def f2(self, b):
#         t = threading.Thread(target=self.f1, args=('aaa',b))
#         t.start()
