import unittest
from tree import tree
import pandas as pd


class TreeTestCase(unittest.TestCase):

    def test_smoke(self):
        data = pd.read_csv("test/data/smoke_1.csv",header = None)
        t = tree(data)
        level1_topic = list(t.keys())
        self.assertEqual(['T1', 'T2'], level1_topic)  # add assertion here

    def test_smoke2(self):
        data = pd.read_csv("test/data/smoke.csv", header=None)
        t = tree(data)
        level1_topic = list(t.keys())
        self.assertEqual(['T1', 'T2'], level1_topic)
        self.assertEqual(0, len(t['T2']))
        t1_subtopic = list(t['T1'].keys())
        self.assertEqual(['TS1', 'TS2'], t1_subtopic)



if __name__ == '__main__':
    unittest.main()
