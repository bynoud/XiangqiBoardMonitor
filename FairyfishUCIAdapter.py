from queue import Queue
from collections.abc import Iterable
from contextlib import closing
import subprocess
import threading

from pprint import PrettyPrinter

DEFAULT_OPT = {'UCI_Variant':'xiangqi'}
DEFAULT_ENGPATH = 'fairy-stockfish-largeboard_x86-64-bmi2.exe'

class Engine():
    INFO_KEYWORDS = {'depth': int, 'seldepth': int, 'multipv': int, 'nodes': int, 'nps': int, 'time': int, 'score': list, 'pv': list}

    def __init__(self, enginePath=DEFAULT_ENGPATH, options=None):
        self.enginePath = enginePath
        self.options = DEFAULT_OPT if options is None else {**DEFAULT_OPT, **options}
        self.movetime = 2000
        self.reset()
        

    def reset(self):
        print('** Info: Start the UCI ')
        self.process = subprocess.Popen([self.enginePath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        self.multipv = Queue()
        self.pprinter = PrettyPrinter()
        self.lock = threading.Lock()
        self.paused = False

    def write(self, message, retry=True):
        with self.lock:
            self.process.stdin.write(message)
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

    def stop(self):
        self.write('stop\n')
        self.paused = True

    def toggle(self):
        if self.paused:
            self.analyze()
        else:
            self.stop()

    def quit(self):
        self.write('quit\n')

    def read(self):
        while self.process.poll() is None:
            yield self.process.stdout.readline()

    @classmethod
    def parse_info(cls, items):
        if len(items) > 1 and items[0] == 'info' and items[1] != 'string':
            key = None
            values = []
            info = {}
            for i in items[1:] + ['']:
                if not i or i in cls.INFO_KEYWORDS:
                    if key:
                        if values and not issubclass(cls.INFO_KEYWORDS[key], Iterable):
                            values = values[0]
                        info[key] = cls.INFO_KEYWORDS[key](values)
                    key = i
                    values = []
                else:
                    values.append(i)
            return info
        return None

    def start(self):
        def read_output():
            try:
                logfile = open('debug.log', 'w')
                for line in self.read():
                    logfile.write(line)
                    # print("OUT: ", line, end='')
                    items = line.split()
                    if len(items) == 0:
                        continue
                    if items[0] == 'info':
                        info = self.parse_info(items)
                        if info and 'score' in info:
                            # print(info)
                            self.multipv.put(info)
                    elif items[0] == 'bestmove':
                        self.multipv.put({'bestmove':items[1], 'ponder': None if len(items)<4 else items[3]}) # indicate the last of multipv for current search
                        # print(line, end='')
                        
            except RuntimeError:
                print('** Warn: Adapter thread closed')
                logfile.close()

        self.engine_thread = threading.Thread(target=read_output, daemon=True)
        self.engine_thread.start()
        self.initialize()
        # self.newgame()
        # self.position(initfen)

    def next_move(self, curfen='', nextmoveListener=None):
        self.write('stop\n') # make sure we stop previous move check
        self.write(f'go movetime {self.movetime}\n')
        infos = []
        bestmove = None
        while True:
            info = self.multipv.get()
            if 'bestmove' in info:
                bestmove = info
                break
            infos.append(info)

        if bestmove is None:
            print('** Error: No bestmove is found')
            return
        
        selinfo = None
        lastScore = -10000000000
        for info in infos:
            pv = info.get('pv', [])
            if len(pv)<2:
                continue
            if pv[0] != bestmove['bestmove'] or pv[1] != bestmove['ponder']:
                continue
            score = int(info.get('score',[-1,-100000000])[1])
            if (selinfo is None) or \
                (len(pv) > len(selinfo.get('pv',[])) and (score > 0 or score >= lastScore)):
                selinfo = info
                lastScore = score

        if nextmoveListener is None:
            print(lastScore, selinfo)
        else:
            nextmoveListener.on_move_caculated(curfen, lastScore, selinfo)

    def set_fen(self, fen, nextmoveListener=None):
        self.position(fen)
        if nextmoveListener is not None:
            t = threading.Thread(target=self.next_move, args=(fen, nextmoveListener))
            t.start()
            # self.next_move(curfen=fen, nextmoveListener=nextmoveListener)

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
