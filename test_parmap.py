import unittest
import warnings
import parmap
import time
import multiprocessing

def _identity(*x):
    """ Dummy function to not do anything"""
    time.sleep(0.2)
    return x


def _fun_with_keywords(x, a = 0, b = 1):
    return x + a + b


class TestParmap(unittest.TestCase):
    def test_map(self):
        items = range(4)
        pfalse = parmap.map(_identity, items, pm_parallel=False)
        ptrue = parmap.map(_identity, items, pm_parallel=True)
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_map_kwargs(self):
        items = range(4)
        pfalse = parmap.map(_fun_with_keywords, items, pm_parallel=False, a=10)
        ptrue = parmap.map(_fun_with_keywords, items, pm_parallel=True, a=10)
        noparmap = [ x + 10 + 1 for x in items]
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_map_progress(self):
        items = range(10)
        pfalse = parmap.map(_identity, items, pm_pbar=False)
        ptrue = parmap.map(_identity, items, pm_pbar=True)
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_map_async(self):
        items = range(4)
        pfalse = parmap.map_async(_identity, items, pm_parallel=False)
        ptrue = parmap.map_async(_identity, items, pm_parallel=True)
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue.get())
        self.assertEqual(pfalse, noparmap)

    def test_map_async2(self):
        items = list(range(4))
        try:
            pool = multiprocessing.Pool(8)
            pfalse = parmap.map_async(_identity, items, pm_parallel=False, pm_pool=pool)
            mytime = time.time()
            ptrue = parmap.map_async(_identity, items, pm_parallel=True, pm_pool=pool)
            mytime = time.time() - mytime
            self.assertTrue(mytime < 0.2)
        finally:
            pool.close()
            pool.join()
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue.get())
        self.assertEqual(pfalse, noparmap)

    def test_starmap(self):
        items = [(1, 2), (3, 4), (5, 6)]
        pfalse = parmap.starmap(_identity, items, 5, 6, pm_parallel=False)
        ptrue = parmap.starmap(_identity, items, 5, 6, pm_parallel=True)
        self.assertEqual(pfalse, ptrue)

    def test_starmap_async(self):
        items = [(1, 2), (3, 4), (5, 6)]
        pfalse = parmap.starmap_async(_identity, items, 5, 6, pm_parallel=False)
        ptrue = parmap.starmap_async(_identity, items, 5, 6, pm_parallel=True)
        self.assertEqual(pfalse, ptrue.get())

    def test_warn_wrong_argument_map(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parmap.map(range, [1, 2], pm_processes=-3)
            self.assertTrue(len(w) > 0)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    unittest.main()
