import os, sys, argparse, logging
from typing import Literal

MYDEBUG = False if 'ProductionBuild' in os.environ else True

print(f'MYDEBUG {MYDEBUG}')

### argument parsing
parser = argparse.ArgumentParser()
parser.add_argument( '-log',
                     '--loglevel',
                     default='error',
                     help='Provide logging level. Example --loglevel debug, default=warning' )

args = parser.parse_args()
loglevel = 'INFO' if MYDEBUG else args.loglevel.upper()


logger = logging.getLogger()
logger.setLevel(logging.INFO)

logFormatter = logging.Formatter('%(module)-20s: %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setLevel(loglevel)
stream_handler.setFormatter(logFormatter)
logger.addHandler(stream_handler)

fileHandler = logging.FileHandler('helper.log', mode='w')
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

# Other file logging

fhlist = {}
if MYDEBUG:
    try:
        fhlist['uci_outlog'] = open('debug.log', 'w')
        fhlist['uci_cmdlog'] = open('uci_cmd.log', 'w')
    except:
        logger.error('Failed to create logfile')
        sys.exit()

def flog(fname: Literal['uci_outlog', 'uci_cmdlog'], msg: str):
    if MYDEBUG:
        fhlist[fname].write(msg)


def cleanup():
    for _, fh in fhlist.items():
        try:
            fh.close()
        except:
            pass
