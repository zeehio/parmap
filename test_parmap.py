import unittest
import warnings
import parmap
import time
import multiprocessing

def _identity(*x):
    """ Dummy function to not do anything"""
    time.sleep(0.2)
    return x


class TestParmap(unittest.TestCase):
    def test_map(self):
        items = range(4)
        pfalse = parmap.map(_identity, items, parallel=False)
        ptrue = parmap.map(_identity, items, parallel=True)
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_map_async(self):
        items = range(4)
        pfalse = parmap.map_async(_identity, items, parallel=False)
        ptrue = parmap.map_async(_identity, items, parallel=True)
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue.get())
        self.assertEqual(pfalse, noparmap)

    def test_map_async(self):
        items = list(range(4))
        try:
            pool = multiprocessing.Pool(8)
            pfalse = parmap.map_async(_identity, items, parallel=False, pool=pool)
            mytime = time.time()
            ptrue = parmap.map_async(_identity, items, parallel=True, pool=pool)
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
        pfalse = parmap.starmap(_identity, items, 5, 6, parallel=False)
        ptrue = parmap.starmap(_identity, items, 5, 6, parallel=True)
        self.assertEqual(pfalse, ptrue)

    def test_starmap_async(self):
        items = [(1, 2), (3, 4), (5, 6)]
        pfalse = parmap.starmap_async(_identity, items, 5, 6, parallel=False)
        ptrue = parmap.starmap_async(_identity, items, 5, 6, parallel=True)
        self.assertEqual(pfalse, ptrue.get())

    def test_warn_wrong_argument_map(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parmap.map(range, [1, 2], processes=-3)
            assert len(w) == 1

    def test_warn_wrong_argument_starmap(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parmap.starmap(range, [(0, 2), (2, 5)], processes=-3)
            assert len(w) == 1


if __name__ == '__main__':
    try:
        import multiprocessing
        multiprocessing.freeze_support()
    except:
        pass
    unittest.main()
