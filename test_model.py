import unittest
from model import calculate, DEFAULTS as NEW_DEFAULTS, validate
DEFAULTS=NEW_DEFAULTS | {"cuMinDed":0.0}
class ModelTests(unittest.TestCase):
    def test_baseline(self):
        r=calculate(DEFAULTS)
        for k,x in {'N':267.5691205843078,'F':24.765567032308645,'M':-4.872002961471885,'implied':-109.06982954308458}.items():
            self.assertAlmostEqual(r[k],x)
    def test_inverse(self):
        for share in [0,50,99.9]:
            v=DEFAULTS|{'share':share}
            self.assertAlmostEqual(calculate(v|{'spot':calculate(v)['implied']})['M'],20)
        self.assertIsNone(calculate(DEFAULTS|{'share':100})['implied'])
    def test_finance_and_payable(self):
        r=calculate(DEFAULTS)
        self.assertAlmostEqual(r['q'],.2316)
        self.assertEqual(calculate(DEFAULTS|{'finance':'no'})['F'],0)
        self.assertEqual(calculate(DEFAULTS|{'rate':0})['F'],0)
        self.assertEqual(calculate(DEFAULTS|{'metals':'no'})['fin'][1:], [0,0])
        self.assertEqual(calculate(DEFAULTS|{'auDed':20})['qa'],0)
        self.assertLess(calculate(DEFAULTS|{'cuRec':90})['fc'],0)
    def test_minimum_deduction(self):
        self.assertAlmostEqual(calculate(NEW_DEFAULTS)["q"],.23)
        self.assertAlmostEqual(calculate(NEW_DEFAULTS|{"cuGrade":40})["q"],.386)
        self.assertEqual(calculate(NEW_DEFAULTS|{"cuGrade":.5})["q"],0)
        self.assertAlmostEqual(calculate(NEW_DEFAULTS|{"spot":calculate(NEW_DEFAULTS)["implied"]})["M"],20)
    def test_invalid(self):
        for patch in [{'fx':0},{'share':101},{'rate':-1},{'cuPrice':float('nan')},{'mode':'bad'}]:
            with self.assertRaises(ValueError): validate(DEFAULTS|patch)
if __name__=='__main__': unittest.main()
