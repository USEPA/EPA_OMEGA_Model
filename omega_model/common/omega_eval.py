"""

**Code to handle runtime compilation of eval statemetns.**

----

**CODE**

"""

from common.omega_types import *


class Eval(OMEGABase):
    """
        **Class to cache compiled eval statements and return their values.**

    """
    _compiled_source = dict()

    @classmethod
    def eval(cls, source, global_vars=None, local_vars=None):
        """
            Like python eval() except on first use it compiles the statement and caches the code for future use.
            
            The source must be a string representing a Python expression.
            The globals must be a dictionary and locals can be any mapping,
            defaulting to the current globals and locals.
            If only globals is given, locals defaults to it.
            
        Args:
            source (str): the statement to be evaluated
            global_vars (dict): dict of global variables
            local_vars (mapping): dict/mapping of local variables

        Returns:

        """
        if source not in cls._compiled_source:
            cls._compiled_source[source] = compile(str(source), '<string>', 'eval')

        return eval(cls._compiled_source[source], global_vars, local_vars)


if __name__ == "__main__":
    try:
        import time

        start_time = time.time()
        print(Eval.eval('1+1'))
        print(time.time() - start_time)

        start_time = time.time()
        print(Eval.eval('1+1'))
        print(time.time() - start_time)

        foo = 42
        start_time = time.time()
        print(Eval.eval('foo+1', globals()))
        print(time.time() - start_time)

        start_time = time.time()
        print(Eval.eval('foo+1', {}, locals()))
        print(time.time() - start_time)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
