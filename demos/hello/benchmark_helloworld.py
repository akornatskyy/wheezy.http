""" ``benchmark_hello`` module.
"""

from wheezy.core.benchmark import Benchmark

from test_helloworld import HelloWorldTestCase


class BenchmarkTestCase(HelloWorldTestCase):
    """"""

    def runTest(self):  # noqa: N802
        """Perform bachmark and print results."""
        p = Benchmark((self.test_welcome, self.test_not_found), 20000)
        p.report(
            "hello", baselines={"test_welcome": 1.0, "test_not_found": 1.3}
        )
