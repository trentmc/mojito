"""This module holds utility routines that help with retrieving data
from simulator evaluation, including SPICE-generated files.

Includes the routines:
-getSpiceData
-removeWhitespace
-file2tokens
-string2tokens
-whitespaceAroundEquality
-subfile2strings
-file2str
"""
import string

import numpy

def getSpiceData(filename, number_width, start_line, num_vars):
    """
    @description
     Retreives data from a .tr0 or .sw0 (waveform) file

    @arguments    
      number_width -- int -- width of each number (eg 11)
      start_line -- int -- number of lines to skip to actually get to numbers 
                    (just inspect the .tr0 file and count).  Note that
                    it starts counting at line 0,1,...
      num_vars  -- int -- number of vars in .print.  

    @return    
      X -- 2d array of float -- retrieved data [1..numvars][1..num_datapoints]

    @notes
      -there is always one extra var present in the file, but we don't return it.
      -there is always one final useless value of 0.0 per var;don't return either
    """
    s = file2str(filename, start_line)
    s = removeWhitespace(s)

    num_floats = (len(s)-1) / number_width
    num_points = num_floats / (num_vars+1)

    X = numpy.zeros((num_vars+1, num_points))

    var_i, point_j = 0, 0
    st = 0
    fin = st + number_width

    for float_i in range(num_floats-1):
        st = float_i*number_width
        fin = st + number_width

        value = float(s[st:fin])
        X[var_i, point_j] = value

        var_i += 1
        if var_i > num_vars+1-1:
            var_i = 0
            point_j += 1

    #remove the extra var that was added in the 0th row
    X = numpy.take(X, range(1,num_vars+1), 0)
    
    #remove last point, which is a vector of 0.0's
    X = numpy.take(X, range(0,num_points-1), 1) 

    return X

def removeWhitespace(s):
    """Returns a version of string 's', without any whitespace"""
    l = s.split()
    return "".join(l)

def file2tokens(filename, startline=0):
    """
    @description
      Grab all the tokens out of a file, starting at 'startline'.
      A 'token' is a string that is separated by whitespace from
      other strings.

    @arguments
      filename -- string -- text file to grab tokens from
      startline -- int --

    @return
      tokens -- list of tokens (ie list of strings)
    """
    s = file2str(filename, startline)
    tokens = string2tokens(s)
    return tokens

def string2tokens(s):
    """Like a string.split() but has safety measures such
    as adding whitespace around '=' operator"""
    s = whitespaceAroundEquality(s)
    tokens = s.split()
    return tokens

def whitespaceAroundEquality(s):
    """Returns an altered version of string 's' in which there
    is a ' ' on either side of each occurrence of '=' and '==' if
     the whitespace does not exist yet."""
    s = s.replace('==','x0x0xxx')   #temporarily hide the '=='
    s = s.replace('=',' = ')        #add whitespace around the '='
    s = s.replace('x0x0xxx',' == ') #un-hide the '==' and add whitespace
    return s
        
def subfile2strings(filename, start_string, end_string):
    """
    @description
      Return a part of a file as a list of strings; one string per line
      -start with the line starting after the first encounter of 'start_string'
      -end with the line right before the next encounter of 'end_string'

    @arguments
      filename -- string -- text file to grab tokens from
      start_string -- string
      end_string -- string

    @return    
      string_per_line -- list of strings

    @exceptions
      Adds a ' ' to either side of '=' and '==' if they don't exist.
    """
    #retrieve a list of lines from file
    f = open(filename, 'r')
    lines_list = f.readlines()
    f.close()

    st, fin = None, None
    for index, line in enumerate(lines_list):
        if st is None:
            if start_string in line:
                st = index

        else:
            if end_string in line:
                fin = index
                break

    if st is None:
        return []
    elif fin is None:
        return lines_list[st+1:]
    else:
        return lines_list[st+1:fin]
    
def file2str(filename, startline=0):
    """
    @description    
     Grab all the tokens out of a file, starting at 'startline'.
     A 'token' is a string that is separated by whitespace from
     other strings.

    @arguments
      filename -- string -- text file to grab tokens from
      startline -- int --

    @return
      s -- string 

    @exceptions
      Adds a ' ' to either side of '=' and '==' if they don't exist.
    """
    #retrieve a list of lines from file
    f = open(filename, 'r')
    lines_list = f.readlines()
    f.close()

    #chop off some lines
    lines_list[:startline] = []

    #convert lines_list to one big string
    big_string = string.join(lines_list)
    return big_string

