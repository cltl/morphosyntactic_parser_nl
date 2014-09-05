#morphosyntactic_parser_nl#

Morphosyntactic parser for Dutch based on the Alpino parser. It takes as input a NAF/KAF file with tokens (processed by a tokeniser and sentence splitter)
and generates the term layer (lemmas and rich morphological information), the constituency layer and the dependency layer. The Alpino parser is only
called once to improve the performance of our module.

##Requirements and installation##

There are two dependencies, the Alpino parser, and the KAfNafParserPy libraty for parsing NAF/KAF objects.

For the Alpino parser you will need to visit http://www.let.rug.nl/vannoord/alp/Alpino/ and follow the instructions to get Alpino installed. Please
make use you use the last version of Alpino (preferably in Linux) as previous version do not provide rich morphological information.

The KafNafParserPy library can be found at https://github.com/cltl/KafNafParserPy . You will need just to clone the repository to your machine, and make
sure it is accesible by Python (or add it to the PYTHON_PATH environment variable).

Once you have the previous 2 steps completed, the last step is to clone this repository to your machine. You will need to tell the library where Alpino
has been installed in your machine. There are two ways to do this. The first one is by setting the environment variable ALPINO_HOME, and point it to the
correct path on your local machine.
```shell
export ALPINO_HOME=/home/a/b/c/Alpino
```

The second option is to hard code it. You will need to edit the script `core/morph_syn_parser.py`, find the function `set_up_alpino`, and find, uncomment and and modify the next
line properly.
```shell
#os.environ['ALPINO_HOME'] = '/home/izquierdo/tools/Alpino'
```

##Usage##

The simplest way to call to the parser is to call to the script `run_parser.sh`, which can be found in the root folder of the repository. It will read a NAF/KAF
file from the input stream and will write the NAF/KAF resulting file in the output stream. In the subfolder examples you can find 2 example input files with the
corresponding and expected output files. From the command line and being on the root folder you can run:
```shell
cat examples/file1.in.kaf | run_parser.sh > my_output.kaf
```

The result in `my_output.kaf` should be the same than the file `examples/file1.out.kaf` (with exception of the time stamps).

If you want to use this library from a python module, it is possible to import the main function and reuse it in other python scripts. The main module is located
in the script `core/morph_syn_parser.py`, and it is called `run_morph_syn_parser`. This function takes two parameters, and input and an output file, which can be
file names (strings), open file descriptors or streams.

##Contact##
* Ruben Izquierdo
* Vrije University of Amsterdam
* ruben.izquierdobevia@vu.nl