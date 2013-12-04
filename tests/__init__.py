import __main__
defaultGlobalDict = __main__.__dict__
import os, unittest
from types import StringTypes
    
# shared, default config root for testing
_root = None

def importSuite(specs, globalDict=defaultGlobalDict):

    """Create a test suite from import specs"""
    from unittest import TestSuite
    return TestSuite(
        [t() for t in importSequence(specs,globalDict)]
    )
    

def importObject(spec, globalDict=defaultGlobalDict):

    """Convert a possible string specifier to an object

    If 'spec' is a string or unicode object, import it using 'importString()',
    otherwise return it as-is.
    """

    if isinstance(spec,StringTypes):
        return importString(spec, globalDict)

    return spec


def importSequence(specs, globalDict=defaultGlobalDict):

    """Convert a string or list specifier to a list of objects.

    If 'specs' is a string or unicode object, treat it as a
    comma-separated list of import specifications, and return a
    list of the imported objects.

    If the result is not a string but is iterable, return a list
    with any string/unicode items replaced with their corresponding
    imports.
    """

    if isinstance(specs,StringTypes):
        return [importString(x.strip(),globalDict) for x in specs.split(',')]
    else:
        return [importObject(s,globalDict) for s in specs]


def importString(name, globalDict=defaultGlobalDict):

    """Import an item specified by a string

    Example Usage::

        attribute1 = importString('some.module:attribute1')
        attribute2 = importString('other.module:nested.attribute2')

    'importString' imports an object from a module, according to an
    import specification string: a dot-delimited path to an object
    in the Python package namespace.  For example, the string
    '"some.module.attribute"' is equivalent to the result of
    'from some.module import attribute'.

    For readability of import strings, it's sometimes helpful to use a ':' to
    separate a module name from items it contains.  It's optional, though,
    as 'importString' will convert the ':' to a '.' internally anyway."""

    if ':' in name:
        name = name.replace(':','.')

    path  = []

    for part in filter(None,name.split('.')):

        if path:

            try:
                item = getattr(item, part)
                path.append(part)
                continue

            except AttributeError:
                pass

        path.append(part)
        item = __import__('.'.join(path), globalDict, globalDict, ['__name__'])

    return item

    

def addModules(dirname):
    mod_names = []

    for filename in os.listdir(dirname):
        pathname = dirname + '/' + filename
        if (pathname[-8:] == '_test.py'):
            mod_names.append(os.path.splitext(os.path.split(pathname)[1])[0])
        elif ((os.path.isdir(pathname)) and
              (not os.path.islink(pathname)) and
              (filename[0] != '.')):
            mod_names.extend(addModules(pathname))

    return mod_names
    
def default_test_suite(module=None):
    dir = os.path.dirname(getattr(module,'__file__',''))
    modules = map(__import__, addModules(dir))
    load = unittest.defaultTestLoader.loadTestsFromModule
    return unittest.TestSuite(map(load, modules))

allSuites = [
    'adts.test.test_suite',
    'engine.test.test_suite',
    'problems.test.test_suite',
    'regressor.test.test_suite',
    'util.test.test_suite',
]

def test_suite():
    return importSuite(allSuites, globals())

if __name__=="__main__":
    unittest.main(defaultTest='test_suite') 
