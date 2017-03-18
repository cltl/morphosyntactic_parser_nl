import logging
import argparse
import sys

from . import parse, __version__

try:
    # python3: sys.stdin.buffer contains the 'bytes'
    input_file = sys.stdin.buffer
except AttributeError:
    # python2: sys.stdin contains bytes (aka 'str)
    input_file = sys.stdin
user_max = None

parser = argparse.ArgumentParser(description='Morphosyntactic parser based on Alpino')
parser.add_argument('-t', '--time', dest='max_minutes', type=float, help='Maximum number of minutes per sentence. Sentences that take longer will be skipped and not parsed (value must be a float)')
parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
parser.add_argument('-V', '--version', action='version', version="{} ({})".format(__name__, __version__))

args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                    format='[%(asctime)s %(name)-12s %(levelname)-5s] %(message)s')

in_obj = parse(input_file, max_min_per_sent=args.max_minutes)
in_obj.dump()
