#!/bin/bash

this_dir=$(dirname $0)

python $this_dir/core/morph_syn_parser.py

#For instance to set the maximum number of minutes per sentence to 5 minutes:
###python $this_dir/core/morph_syn_parser.py -t 5

#Maximum 30 seconds per setence:
###python $this_dir/core/morph_syn_parser.py -t 0.5