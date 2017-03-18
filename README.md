#morphosyntactic_parser_nl#

Wrapper around the Dutch Alpino parser. It takes as input a text/NAF/KAF file with either raw text or tokens (processed by a tokeniser and sentence splitter)
and generates the term layer (lemmas and rich morphological information), the constituency layer and the dependency layer.

##Requirements and installation##

There are two dependencies, the Alpino parser, and the KAfNafParserPy library for parsing NAF/KAF objects.

For the Alpino parser you have two choices.
For a local install, visit http://www.let.rug.nl/vannoord/alp/Alpino/ and follow the instructions to get Alpino installed, or run install_alpino.sh.
Make sure to set ALPINO_HOME to point to the installation.

For using an alpino server instance (e.g. through alpino-docker), point ALPINO_SERVER to the HTTP address of the server (e.g. ALPINO_SERVER=http://localhost:5002)

The KafNafParserPy library can be install through pip or from https://github.com/cltl/KafNafParserPy

Once you have the previous 2 steps completed, the last step is to clone this repository to your machine. You will need to tell the library where Alpino
has been installed in your machine. There are two ways to do this. The first one is by setting the environment variable ALPINO_HOME, and point it to the
correct path on your local machine.

```shell
export ALPINO_HOME=/home/a/b/c/Alpino
```

##Usage##

The simplest way to call to the parser is to call to the script `run_parser.sh`, which can be found in the root folder of the repository. It will read a NAF/KAF
file from the input stream and will write the NAF/KAF resulting file in the output stream. In the subfolder examples you can find 2 example input files with the
corresponding and expected output files. From the command line and being on the root folder you can run:
```shell
cat examples/file1.in.kaf | run_parser.sh > my_output.kaf
```

The result in `my_output.kaf` should be the same than the file `examples/file1.out.kaf` (with exception of the time stamps).

You can specify also the maximum number of seconds that Alpino will take to parse every sentence. Sentences taking longer that this value will be skipped
from the parsing, and there will not be term, constituency nor dependency information for all the tokens of those sentences. The parameter to be used is `-t` or `--time`.
You can get the whole description of the parameters by calling `python core/morph_syn_parser.py -h`. You will the this information:
```shell
usage: morph_syn_parser.py [-h] [-v] [-t MAX_MINUTES]

Morphosyntactic parser based on Alpino

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -t MAX_MINUTES, --time MAX_MINUTES
                        Maximum number of minutes per sentence. Sentences that
                        take longer will be skipped and not parsed (value must
                        be a float)
```

If you want to use this library from a python module, it is possible to import the main function and reuse it in other python scripts. The main module is located
in the script `core/morph_syn_parser.py`, and it is called `run_morph_syn_parser`. This function takes two parameters, and input and an output file, which can be
file names (strings), open file descriptors or streams.

##Contact##
* Ruben Izquierdo
* Vrije University of Amsterdam
* ruben.izquierdobevia@vu.nl  rubensanvi@gmail.com
* http://rubenizquierdobevia.com/