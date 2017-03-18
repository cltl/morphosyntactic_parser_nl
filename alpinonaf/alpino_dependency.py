import logging
import re
import sys
from xml.sax.saxutils import escape

from KafNafParserPy import Cdependency

'''
This class encapsultes a parser for a single dependency line from Alpino, like:
name:Koningin/[17,18]|mwp/mwp|name:Nederlanden/[19,20]|/tmp/tmpF2UGFY/1.xml
It extracts the fields and generates the dependency
'''

class Calpino_dependency:
    def __init__(self,line):
        self.ok = True
        self.begin_from = self.begin_to = self.end_from = self.end_to = self.sentence = ''
        fields = line.split('|')
        if len(fields) == 4:
            token_to = fields[0]
            match =  re.match(r'(.+)/\[(\d+),(\d+)\]', token_to)
            if match is not None:
                self.lemma_to = match.group(1)
                self.begin_to = int(match.group(2))
                self.end_to = int(match.group(3))
                
                token_from = fields[2]
                match2 =  re.match(r'(.+)/\[(\d+),(\d+)\]', token_from)
                if match2 is not None:
                    self.lemma_from = match2.group(1)
                    self.begin_from = int(match2.group(2))
                    self.end_from = int(match2.group(3))
                    self.relation = fields[1]
                else:
                    self.ok = False
            else:
                self.ok = False
        else:
            self.ok = False
        
    def is_ok(self):
        return self.ok
            
    def __repr__(self):
        r = 'From: %d-%d to %d-%d' % (self.begin_from,self.end_from,self.begin_to,self.end_to)
        return r
    
    def generate_dependencies(self, list_term_ids):
        # This will creathe dependency
        dependencies = []
        try:
            terms_from = [ list_term_ids[idx] for idx in range(self.begin_from,self.end_from) ]
            terms_to = [ list_term_ids[idx] for idx in range(self.begin_to,self.end_to) ]
            for t_from in terms_from:
                for t_to in terms_to:
                    ##Creating comment
                    str_comment = ' '+self.relation+'('+self.lemma_to+','+self.lemma_from+') '
                    str_comment = escape(str_comment)
                    
                    my_dep = Cdependency()
                    my_dep.set_from(t_to)
                    my_dep.set_to(t_from)
                    my_dep.set_function(self.relation)
                    my_dep.set_comment(str_comment)
                    
                    dependencies.append(my_dep)
        except Exception as e:
            logging.exception("Error on generating dependencies")
        return dependencies
