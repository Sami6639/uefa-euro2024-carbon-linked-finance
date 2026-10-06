import math
import unittest
import numpy as np
from model.contracts import (uniform_contract,gaussian_contract,expectation,marginal,
 expected_quadrature,marginal_finite_difference,sharp_budget,lp_minimum_excess,
 discrete_contract,all_in_budget)

class TestContracts(unittest.TestCase):
    def test_invalid_budget(self):
        for builder in [uniform_contract,gaussian_contract]:
            with self.assertRaises(ValueError): builder(10,1,2,1,1)
    def test_uniform_budget_and_slope(self):
        for h in [0,.1,1,3]:
            for f in [0,.5,.95,1]:
                c=uniform_contract(10,1,f,1,h)
                self.assertAlmostEqual(expectation(c),1,places=11)
                self.assertAlmostEqual(expected_quadrature(c),1,places=10)
                self.assertGreaterEqual(marginal(c),0)
                self.assertLessEqual(marginal(c),1)
                # At full-incentive boundary, finite differences cross a support end.
                self.assertAlmostEqual(marginal_finite_difference(c),marginal(c),delta=2e-5)
    def test_gaussian_budget_and_slope(self):
        for sd in [0,.01,.2,1,5]:
            for f in [0,.5,.95,.999999,1]:
                c=gaussian_contract(10,1,f,1,sd)
                self.assertAlmostEqual(expectation(c),1,places=10)
                self.assertAlmostEqual(expected_quadrature(c),1,places=8)
                self.assertAlmostEqual(marginal_finite_difference(c),marginal(c),delta=2e-6)
    def test_zero_floor_not_full_slope_unconditionally(self):
        c=uniform_contract(10,1,0,1,3)
        self.assertAlmostEqual(marginal(c),math.sqrt(1/3),places=12)
    def test_zero_noise(self):
        for builder in [uniform_contract,gaussian_contract]:
            c=builder(10,1,.99,1,0)
            self.assertAlmostEqual(marginal(c),1)
            c=builder(10,1,1,1,0)
            self.assertTrue(c.constant)
            self.assertEqual(marginal(c),0)
    def test_uniform_full_boundary(self):
        c=uniform_contract(10,1,.5,1,.5)
        self.assertEqual(marginal(c),1)
        self.assertEqual(c.threshold,9.5)
    def test_zero_rate(self):
        c=uniform_contract(10,1,.5,0,1)
        self.assertEqual(expectation(c),1)
        self.assertEqual(marginal(c),0)
    def test_mean_preserving_spread_reverses_slope(self):
        a=discrete_contract([-1,1],[.5,.5],.8)
        b=discrete_contract([-2,0,2],[.25,.5,.25],.8)
        self.assertAlmostEqual(a['intercept'],.6)
        self.assertAlmostEqual(b['intercept'],.4)
        self.assertAlmostEqual(a['marginal'],.5)
        self.assertAlmostEqual(b['marginal'],.75)
        self.assertAlmostEqual(a['variance'],1)
        self.assertAlmostEqual(b['variance'],2)
    def test_fixed_not_moving_calibration(self):
        c=uniform_contract(10,1,.9,1,1)
        step=1e-4
        fixed=(expectation(c,10+step)-expectation(c,10-step))/(2*step)
        cp=uniform_contract(10+step,1,.9,1,1)
        cm=uniform_contract(10-step,1,.9,1,1)
        moving=(expectation(cp)-expectation(cm))/(2*step)
        self.assertGreater(fixed,.3)
        self.assertAlmostEqual(moving,0,places=8)
    def test_lp_frontier_and_convergence(self):
        errors=[]
        for n in [25,50,100,200]:
            out=lp_minimum_excess(1,1,.37,n)
            error=out['minimum_excess']-sharp_budget(0,1,.37,1)
            self.assertGreaterEqual(error,-1e-12)
            self.assertLessEqual(error,1/(4*n*n)+1e-12)
            self.assertAlmostEqual(out['mean_slope'],.37,places=10)
            errors.append(error)
        self.assertLessEqual(errors[-1],errors[0]+1e-12)
    def test_all_in_extension(self):
        self.assertAlmostEqual(all_in_budget(.5,1,.5,1,.1,.2),.95)
    def test_monotonicity_within_families(self):
        for builder in [uniform_contract,gaussian_contract]:
            ms=[marginal(builder(10,1,.9,1,s)) for s in [.01,.1,.5,1,2]]
            self.assertTrue(np.all(np.diff(ms)<=1e-12))
            ms=[marginal(builder(10,1,f,1,1)) for f in [0,.5,.9,.95,1]]
            self.assertTrue(np.all(np.diff(ms)<=1e-12))

if __name__=='__main__': unittest.main()
