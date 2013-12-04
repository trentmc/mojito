"""
Holds knowledge about allowable topology combinations.
"""
import types

class Schema(dict):
    """      
    @attributes
      self -- dict mapping varname : possible_values_list
      
    @notes
      Note the inheritance from dict.
    """
    def __init__(self, *args):
        #initialize parent class
        dict.__init__(self,*args)
        for varname, varval in self.items():
            assert isinstance(varname, types.StringType)
            assert isinstance(varval, types.ListType)
        self.checkConsistency()

    def checkConsistency(self):
        """
        @description
          Will raise a ValueError if not consistent. Checks include:
          -are there duplicates in any schema's values?
        """
        for key, val in self.items():
            if len(val) != len(set(val)):
                raise ValueError(self)
                
    def __str__(self):
        #print the dict with vars sorted
        varnames = sorted(self.keys())
        s = "{"
        for i, varname in enumerate(varnames):
            s += "%s: %s" % (varname, self[varname])
            if i < len(varnames)-1: s += ", "
        s += "}"
        return s

class Schemas(list):
    """      
    @attributes
      self -- list of schema
      
    @notes
      Note the inheritance from list.
    """
    
    def __init__(self, *args):
        #initialize parent class
        list.__init__(self,*args)

        #consistent?
        self.checkConsistency()

    def checkConsistency(self):
        """
        @description
          Will raise a ValueError if not consistent. Currently, checks include:
          -call to each schema's _checkConsistency
          -FIXME: are there any overlaps in logic input space?
        """
        for schema in self:
            assert isinstance(schema, Schema)
            schema.checkConsistency()

    def __str__(self):        
        s = "[\n"
        for schema in self:
            s += str(schema) + ",\n"
        s += "]\n"
        return s

    def numPermutations(self):
        """
        @description
          Returns # possible topology permutations

        @arguments
          <<none>> (gets info from self)

        @return
          count -- int
        """
        count = 0
        for schema in self:
            assert isinstance(schema, Schema), schema
            schema_count = 1
            for varname, possible_values in schema.items():
                assert isinstance(possible_values, types.ListType), \
                       possible_values
                schema_count *= len(possible_values)
            count += schema_count
            
        return count
        
    def merge(self):
        """
        @description
          Tries to find schemas where the possible_values lists
          can be merged, and merges them.

          Example: if the input is:
            [{'loadrail_is_vdd': [0, 1], 'cascode_recurse': [1]}
            {'loadrail_is_vdd': [0, 1], 'cascode_recurse': [0]}]
          Then it output is:
            [{'loadrail_is_vdd': [0, 1], 'cascode_recurse': [0,1]}]

        @arguments
          <<none>> (gets list of schemas info from self)

        @return
          <<may modify self to shrink list size>>
        """
        while True:
            found_merge = self._mergeOnceIfPossible()
            if not found_merge:
                break

        self.checkConsistency()
        return

    def _mergeOnceIfPossible(self):
        """
        @description
          Tries to find _any_ merge, and performs it if possible.

        @arguments
          <<none>> (gets info from self)

        @return
          found_merge -- bool -- found a merge to do?
          <<may modify self>>
        """
        #corner case
        if len(self) == 0:
            return False
        
        for i, schema_i in enumerate(self):
            for j, schema_j in enumerate(self):
                if j <= i: continue

                vars_i = sorted(schema_i.keys())
                vars_j = sorted(schema_j.keys())
                if vars_i != vars_j: continue #no match: vars not identical

                values_i = [schema_i[var] for var in vars_i]
                values_j = [schema_j[var] for var in vars_j]
                diff_locs = [loc
                             for loc, (value_i, value_j) in
                             enumerate(zip(values_i, values_j))
                             if value_i != value_j]
                num_diff = len(diff_locs)
                num_vars = len(schema_i)
                assert num_diff > 0, "should never be identical"
                if num_diff > 1: continue #no match: too many different values

                #match found!
                merge_var = vars_i[diff_locs[0]]
                merge_val = values_i[diff_locs[0]] + values_j[diff_locs[0]]
                merge_val = sorted(list(set(merge_val)))

                new_schemas = []
                for k,schema in enumerate(self):
                    if k == i:
                        merged_schema = schema
                        merged_schema[merge_var] = merge_val
                        new_schemas.append(schema)
                    elif k == j:
                        pass
                    else:
                        new_schemas.append(schema)

                list.__init__(self, new_schemas)
                return True

        return False

