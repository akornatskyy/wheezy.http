
""" ``benchmark_hello`` module.
"""

from wheezy.core.benchmark import Benchmark

from test_helloworld import HelloWorldTestCase


class BenchmarkTestCase(HelloWorldTestCase):
    """
        cd demos/hello
        ../../env/bin/nosetests-2.7 -qs -m benchmark benchmark_helloworld.py
    """

    def runTest(self):
        """ Perform bachmark and print results.
        """
        p = Benchmark((
            self.test_welcome,
            self.test_not_found
            ), 20000)
        p.report('hello', baselines={
                'test_welcome': 1.0,
                'test_not_found': 1.3
        })
