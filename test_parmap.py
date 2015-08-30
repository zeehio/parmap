import unittest
import parmap

def _identity(*x):
    return x


class TestParmap(unittest.TestCase):
    def test_map(self):
        items = range(4)
        pfalse = parmap.map(_identity, items, parallel=False)
        ptrue = parmap.map(_identity, items, parallel=True)
        noparmap = list(map(_identity, items))
        self.assertEqual(pfalse, ptrue)
        self.assertEqual(pfalse, noparmap)

    def test_starmap(self):
        items = [(1, 2), (3, 4), (5, 6)]
        pfalse = parmap.starmap(_identity, items, 5, 6, parallel=False)
        ptrue = parmap.starmap(_identity, items, 5, 6, parallel=True)
        self.assertEqual(pfalse, ptrue)


if __name__ == '__main__':
    unittest.main()

