'''
Copyright (c) 2020, Board of Trustees of the University of Iowa.
All rights reserved.

Use of this source code is governed by a BSD 3-Clause License that
can be found in the LICENSE file.
'''

from lark import Lark, Transformer, ParseError
from edu.uiowa.parser.Formula import PLTLFormula
import logging

#PLTL Formula Grammar
pLTL_grammar = r"""
        ?start: formula
        
        ?formula: _binary_expression
                |_unary_expression
                | constant
                | variable
        !constant: "Top"
                | "Bottom"
        _binary_expression: binary_op "(" formula "," formula ")"
        _unary_expression: unary_op ["("] formula [")"]

        !binary_op: "&" | "|" |"S" | "=>"
        !unary_op: "G"| "H" | "O" | "!" | "Y" 
        
        variable: CNAME

        CNAME: ("-"|"_"|LETTER) ("-"|"_"|LETTER|DIGIT)*

        %import common.LETTER
        %import common.DIGIT
        
        %import common.SIGNED_NUMBER
        %import common.WS
        %ignore WS 
"""

#ADT Grammar    
adt_grammar = r"""
        ?start: "(define-fun" func ")"
         
        ?func: _ID "() Formula" formula 
         
        ?formula: "(" "Op2" _binary_expression ")"
                | "(" "Op1" _unary_expression ")"
                | "(" "P" variable ")" 
                | constants
        
        _unary_expression: unary_op formula 

        _binary_expression: binary_op formula formula 
        
        !binary_op: "AND" | "OR" |"IMPLIES" | "S"
        !unary_op: "NOT" | "Y" | "H" | "O"
        
        !variable: NUMBER
        !constants: "Top" | "Bottom"
        _ID: /[A-Za-z_][A-Za-z_0-9]*/
        
        %import common.NUMBER

        %import common.WS
        %ignore WS 
"""

#    s_input = '(define-fun phi 
# (
#   (failure (_ BitVec 5)) 
#   (alarm   (_ BitVec 5))
# ) 
# (_ BitVec 5)

# (let 
#  (
#    (_let_0 (Y failure) )
#  ) 
# (bvimpl failure (bvimpl (O _let_0) (Y (Y _let_0))))))'
#    s_input = '(define-fun phi ((failure (_ BitVec 5)) 
# (alarm (_ BitVec 5))) 
# (_ BitVec 5) (bvimpl failure (bvnot (Y (bvor failure (Y (bvnot (Y failure))))))))'

#BitVector Grammar
bv_grammar = r"""

        ?start: bv_fun
        bv_fun: "(define-fun" func_def  _let_formula ")"
        
        func_def: "phi" "(" _vars  ")" _type 
        
        _let_formula: "(" _let_def formula ")" | formula 
        _let_def: "let" "(" _let_vars")"
        _let_vars: _let_vars | let_exp
        let_exp: "(" CNAME formula ")"
         
        _vars: _vars _var | _var 
        _var: "(" CNAME _type ")" 
        _type: "(" "_" "BitVec" NUMBER ")"

        ?formula: "(" _unary_expression ")"
                | "(" _binary_expression ")"
                | variable 
                | constants
        
        _unary_expression: unary_op formula 

        _binary_expression: binary_op formula formula 
        
        !binary_op: "S" | "bvimpl" | "bvor" | "bvand"
        !unary_op: "Y" | "H" | "O" | "bvnot"
        !constants: "S_TRUE" | "S_FALSE"
        !variable: CNAME

        CNAME: ("-"|"_"|LETTER) ("-"|"_"|LETTER|DIGIT)*
    
        %import common.LETTER
        %import common.DIGIT
                
        %import common.NUMBER

        %import common.WS
        %ignore WS 
"""

class TreeToFormula(Transformer):
         
        def formula(self, formulaArgs):
            return PLTLFormula(formulaArgs)
        
        def variable(self, varName):
            return PLTLFormula([str(varName[0]), None, None])
        
        def binary_op(self, args):
            return str(args[0])
        
        def unary_op(self, args):
            return str(args[0])
        
class ADTTreeToFormula(Transformer):
         
        def formula(self, formulaArgs):
            return PLTLFormula(formulaArgs)

        def constants(self, varName):
            const = str(varName[0])
            if (const == "Top"):
                const = "TRUE"
            elif (const == "Bottom"):
                const = "FALSE"    
            return PLTLFormula([const, None, None])
        
        def variable(self, number):
            var = 'p'+ number[0]
            return PLTLFormula([var, None, None])
                        
        def binary_op(self, args):
            bop = str(args[0])
            
            if (bop == "AND"):
                bop = "&"
            if (bop == "OR"):
                bop = "|"
            if (bop == "IMPLIES"):
                bop = "=>"    
            return bop
        
        def unary_op(self, args):
            nop = str(args[0])
            if (nop == "NOT"):
                nop = "!"
            
            return nop

class BVTreeToFormula(Transformer):
        var_dict = {}    
        
        def bv_fun(self, formulaArgs):
            return formulaArgs[-1]
        
        def formula(self, formulaArgs):
            return PLTLFormula(formulaArgs)

        def constants(self, varName):
            const = str(varName[0])
            if (const == "S_TRUE"):
                const = "TRUE"
            elif (const == "S_FALSE"):
                const = "FALSE"    
            return PLTLFormula([const, None, None])
        
        def variable(self, cname):
            var = cname[0]
            if var in self.var_dict:
               return self.var_dict[var]     
            return PLTLFormula([var, None, None])
                        
        def binary_op(self, args):
            bop = str(args[0])
                        
            if (bop == "bvand"):
                bop = "&"
            elif (bop == "bvor"):
                bop = "|"
            elif (bop == "bvimpl"):
                bop = "=>"

            return bop
        
        def unary_op(self, args):
            nop = str(args[0])
            if (nop == "bvnot"):
                nop = "!"
            
            return nop

        def let_exp(self, args):

           # print(">>>>>>>>",args, args)
            key = str(args[0])
            value =  args[1]
            self.var_dict[key] =  value
            print(self.var_dict)
#            self.let_vars.add(args[0], args[1])

class pLTLParser:
    
    
    def parse(self, s_input):
 
        fml = None
        
        parser = Lark(pLTL_grammar, parser='lalr', lexer='standard', transformer=TreeToFormula())
        
        try:
            fml = parser.parse(s_input)            
            logging.info('Parsed PLTL Formula: %s'%(str(fml)))

        except ParseError as e:    
            logging.error('Failed to Parse LTL Formula, error:')
            logging.error(str(e))                
#            quit
            

        return fml   
    
    def parse_adt(self, s_input):
 
        fml = None
        
        parser = Lark(adt_grammar, parser='lalr', lexer='standard', transformer=ADTTreeToFormula())
        
        try:
            fml = parser.parse(s_input)            
        except ParseError as e:    
            logging.error('Failed to Parse LTL Formula, error:')
            logging.error(str(e))                

        return fml   


    def parse_bv(self, s_input):
 
        fml = None
        
        parser = Lark(bv_grammar, parser='lalr', lexer='standard', transformer=BVTreeToFormula())
        
        try:
            fml = parser.parse(s_input)            
        except ParseError as e:    
            logging.error('Failed to Parse LTL Formula, error:')
            logging.error(str(e))                
            
        return fml   

    def dict_var(self, f, vars_dict):
        
        if f is None:
            return None

        if(f._isLeaf()):
            if f.label == 'TRUE' or f.label == 'FALSE':
                var_name = f.label
            else:                   
                var_name = vars_dict[f.label]
            f = PLTLFormula([var_name, None, None])
            return f
        
        left = self.dict_var(f.left, vars_dict)
        right = self.dict_var(f.right, vars_dict)
        
        return PLTLFormula([f.label, left, right])

if __name__ == "__main__":

    parser = pLTLParser()

#    s_input = '(define-fun phi ((failure (_ BitVec 5)) (alarm (_ BitVec 5))) (_ BitVec 5) (let ((_let_0 (Y failure))) (bvimpl failure (bvimpl (O _let_0) (Y (Y _let_0))))))'
    s_input = '(define-fun phi ((failure (_ BitVec 5)) (alarm (_ BitVec 5))) (_ BitVec 5) (bvimpl failure (bvnot (Y (bvor failure (Y (bvnot (Y failure))))))))'
    f = parser.parse_bv(s_input)
    print('>>',f)
