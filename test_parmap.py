import multiprocessing
import time
import unittest
import warnings

import parmap

# The fact that parallelization is happening is controlled via reasonable
# guesses of the parmap overhead and the CPU speeds


# Overhead of map_async, should be less than TIME_PER_TEST
TIME_OVERHEAD = 0.4

# The time each call takes to return in the _wait test
TIME_PER_TEST = 0.8

def _wait(x):
    """ Dummy function to not do anything"""
    time.sleep(TIME_PER_TEST)
    return x

def _identity(*x):
    return x

_DEFAULT_B = 1
def _fun_with_keywords(x, a = 0, b = _DEFAULT_B):
    return x + a + b


class TestParmap(unittest.TestCase):
    def test_map_without_parallel_timings(self):
        NUM_TASKS = 6
        items = range(NUM_TASKS)
        mytime = time.time()
        pfalse = parmap.map(_wait, items, pm_parallel=False)
        elapsed = time.time() - mytime
        self.assertTrue(elapsed >= TIME_PER_TEST*NUM_TASKS)
        self.assertEqual(pfalse, list(range(NUM_TASKS)))

    def test_map_with_parallel_timings(self):
        NUM_TASKS = 6
        items = range(NUM_TASKS)
        mytime = time.time()
        ptrue = parmap.map(_wait, items, pm_processes=NUM_TASKS,
                           pm_parallel=True)
        elapsed = time.time() - mytime
        self.assertTrue(elapsed >= TIME_PER_TEST)
        self.assertTrue(elapsed < TIME_PER_TEST*(NUM_TASKS-1))
        self.assertEqual(ptrue, list(range(NUM_TASKS)))

    def test_map_kwargs(self):
        items = range(2)
        pfalse = parmap.map(_fun_with_keywords, items, pm_parallel=False, a=10)
        ptrue = parmap.map(_fun_with_keywords, items, pm_parallel=True, a=10)
        noparmap = [ x + 10 + _DEFAULT_B for x in items]
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_map_progress(self):
        items = range(4)
        pfalse = parmap.map(_wait, items, pm_pbar=False)
        ptrue = parmap.map(_wait, items, pm_pbar=True)
        noparmap = list(map(_wait, items))
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_map_async_started_simultaneously_timings(self):
        items = list(range(4))
        mytime0 = time.time()
        # These are started in parallel:
        with parmap.map_async(_wait, items, pm_processes=4) as compute1:
            elapsed1 = time.time() - mytime0
            mytime = time.time()
            with parmap.map_async(_wait, items, pm_processes=4) as compute2:
                elapsed2 = time.time() - mytime
                mytime = time.time()
                result1 = compute1.get()
                elapsed3 = time.time() - mytime0
                mytime = time.time()
                result2 = compute2.get()
                elapsed4 = time.time() - mytime0
        self.assertTrue(elapsed1 < TIME_OVERHEAD)
        self.assertTrue(elapsed2 < TIME_OVERHEAD)
        self.assertTrue(elapsed3 < 4*TIME_PER_TEST+2*TIME_OVERHEAD)
        self.assertTrue(elapsed4 < 4*TIME_PER_TEST+2*TIME_OVERHEAD)
        self.assertEqual(result1, result2)
        self.assertEqual(result1, items)

    def test_map_async_noparallel_started_simultaneously_timings(self):
        NTASKS = 4
        items = list(range(NTASKS))
        mytime = time.time()
        # These are started in parallel:
        with parmap.map_async(_wait, items, pm_parallel=False) as compute1:
            elapsed1 = time.time() - mytime
            mytime = time.time()
            with parmap.map_async(_wait, items, pm_parallel=False) as compute2:
                elapsed2 = time.time() - mytime
                mytime = time.time()
                result1 = compute1.get()
                result2 = compute2.get()
                finished = time.time() - mytime
        self.assertTrue(elapsed1 >= NTASKS*TIME_PER_TEST)
        self.assertTrue(elapsed2 >= NTASKS*TIME_PER_TEST)
        self.assertTrue(finished <= 2*TIME_OVERHEAD)
        self.assertEqual(result1, result2)
        self.assertEqual(result1, items)


    def test_map_async(self):
        NUM_TASKS = 6
        NCPU = 6
        items = range(NUM_TASKS)
        mytime = time.time()
        pfalse = parmap.map_async(_wait, items, pm_parallel=False).get()
        elapsed_false = time.time() - mytime
        mytime = time.time()
        with parmap.map_async(_wait, items, pm_processes=NCPU) as ptrue:
            elap_true_async = time.time() - mytime
            mytime = time.time()
            ptrue_result = ptrue.get()
            elap_true_get = time.time() - mytime
        noparmap = list(items)
        self.assertEqual(pfalse, ptrue_result)
        self.assertEqual(pfalse, noparmap)
        self.assertTrue(elapsed_false > TIME_PER_TEST*(NUM_TASKS-1))
        self.assertTrue(elap_true_async < TIME_OVERHEAD)
        self.assertTrue(elap_true_get < TIME_PER_TEST*(NUM_TASKS-1))

    def test_starmap(self):
        items = [(1, 2), (3, 4), (5, 6)]
        pfalse = parmap.starmap(_identity, items, 5, 6, pm_parallel=False)
        ptrue = parmap.starmap(_identity, items, 5, 6, pm_parallel=True)
        self.assertEqual(pfalse, ptrue)

    def test_starmap_async(self):
        items = [(1, 2), (3, 4), (5, 6)]
        pfalse = parmap.starmap_async(_identity, items, 5, 6, pm_parallel=False)
        ptrue = parmap.starmap_async(_identity, items, 5, 6, pm_parallel=True)
        self.assertEqual(pfalse.get(), ptrue.get())

    def test_warn_wrong_argument_map(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parmap.map(range, [1, 2], pm_processes=-3)
            self.assertTrue(len(w) > 0)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    unittest.main()
