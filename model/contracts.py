"""Precommitted capped-slope contracts; all noise inputs are declared scenarios.

Units: emissions/report/threshold in tCO2e; budget/floor in EUR;
rate and expected marginal contractual obligation in EUR/tCO2e.
Calibration occurs ONLY at the fixed reference mean. Evaluation at another
physical mean retains the calibrated threshold.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq, linprog
from scipy.special import ndtr
from scipy.stats import norm


@dataclass(frozen=True)
class Contract:
    mean: float
    budget: float
    floor: float
    rate: float
    scale: float
    family: str
    threshold: float
    constant: bool = False

    def payment(self, report):
        y = np.asarray(report)
        ans = np.full_like(y, self.budget, dtype=float) if self.constant else self.floor + self.rate * np.maximum(y-self.threshold, 0.0)
        return float(ans) if ans.ndim == 0 else ans

    def slope(self, report):
        y = np.asarray(report)
        ans = np.zeros_like(y, dtype=float) if self.constant else self.rate * (y > self.threshold)
        return float(ans) if ans.ndim == 0 else ans


def _check(mean, budget, floor, rate, scale):
    if not all(math.isfinite(x) for x in [mean, budget, floor, rate, scale]):
        raise ValueError('Inputs must be finite.')
    if budget < floor or floor < 0 or rate < 0 or scale < 0:
        raise ValueError('Require budget >= floor >= 0, rate >= 0, scale >= 0.')


def uniform_contract(mean, budget, floor, rate, halfwidth):
    _check(mean, budget, floor, rate, halfwidth)
    d = budget-floor
    if d == 0 or rate == 0:
        return Contract(mean,budget,floor,rate,halfwidth,'uniform',math.inf,True)
    if halfwidth == 0 or d >= rate*halfwidth:
        k = mean-d/rate
    else:
        k = mean+halfwidth-2*math.sqrt(halfwidth*d/rate)
    return Contract(mean,budget,floor,rate,halfwidth,'uniform',k)


def normal_stoploss(z):
    """E[(Z+z)+] for standard normal Z; stable enough on validated tails."""
    return float(norm.pdf(z)+z*ndtr(z))


def gaussian_contract(mean,budget,floor,rate,sd):
    _check(mean,budget,floor,rate,sd)
    d=budget-floor
    if d == 0 or rate == 0:
        return Contract(mean,budget,floor,rate,sd,'gaussian',math.inf,True)
    if sd == 0:
        k=mean-d/rate
    else:
        target=d/(rate*sd)
        z=brentq(lambda x: normal_stoploss(x)-target,-38.0,max(1.0,target+1.0),xtol=1e-13)
        k=mean-sd*z
    return Contract(mean,budget,floor,rate,sd,'gaussian',k)


def expectation(contract, physical_mean=None):
    """Analytical expectation, keeping the precommitted schedule fixed."""
    c=contract
    e=c.mean if physical_mean is None else physical_mean
    if c.constant:
        return c.budget
    if c.scale == 0:
        return c.payment(e)
    if c.family == 'uniform':
        h=c.scale
        l,u=e-h,e+h
        if c.threshold >= u: return c.floor
        if c.threshold <= l: return c.floor+c.rate*(e-c.threshold)
        return c.floor+c.rate*(u-c.threshold)**2/(4*h)
    z=(e-c.threshold)/c.scale
    return c.floor+c.rate*c.scale*normal_stoploss(z)


def marginal(contract, physical_mean=None):
    c=contract
    e=c.mean if physical_mean is None else physical_mean
    if c.constant: return 0.0
    if c.scale == 0:
        if e == c.threshold: return math.nan
        return c.rate*float(e > c.threshold)
    if c.family == 'uniform':
        return c.rate*float(np.clip((e+c.scale-c.threshold)/(2*c.scale),0,1))
    return c.rate*float(ndtr((e-c.threshold)/c.scale))


def expected_quadrature(contract, physical_mean=None):
    """Independent direct integration of the payment, not its moment formula."""
    c=contract
    e=c.mean if physical_mean is None else physical_mean
    if c.constant or c.scale == 0:
        return c.payment(e)
    if c.family == 'uniform':
        k=(c.threshold-e)/c.scale
        points=[k] if -1<k<1 else None
        return quad(lambda x: c.payment(e+c.scale*x)/2,-1,1,points=points,epsabs=1e-7,epsrel=1e-11)[0]
    k=(c.threshold-e)/c.scale
    f=lambda x: c.payment(e+c.scale*x)*norm.pdf(x)
    # Split at the kink AND around the density's central mass. An unbounded
    # interval beginning at a remote kink can otherwise miss the density.
    breaks=[-np.inf]+sorted(set([-12.0,-8.0,0.0,8.0,12.0,k]))+[np.inf]
    return sum(quad(f,a,b,epsabs=1e-9,epsrel=1e-11)[0]
               for a,b in zip(breaks[:-1],breaks[1:]))


def marginal_finite_difference(contract, step=None):
    step = max(1e-5,abs(contract.mean)*1e-6,contract.scale*1e-5) if step is None else step
    if contract.scale == 0 and not contract.constant:
        step = min(step, abs(contract.mean-contract.threshold)/100)
    return (expectation(contract,contract.mean+step)-expectation(contract,contract.mean-step))/(2*step)


def sharp_budget(floor,halfwidth,target,rate):
    if floor < 0 or halfwidth < 0 or rate <= 0 or target < 0 or target > rate:
        raise ValueError('Require nonnegative floor/halfwidth and target in [0, rate], rate>0.')
    return floor+halfwidth*target**2/rate


def all_in_budget(gap,halfwidth,target,rate,fixed_verification=0.0,guarantee_loading=0.0):
    if fixed_verification < 0 or guarantee_loading < 0:
        raise ValueError('Verification costs and guarantee loading must be nonnegative.')
    return sharp_budget(gap,halfwidth,target,rate)+fixed_verification+guarantee_loading*gap


def lp_minimum_excess(halfwidth,rate,target,n_cells):
    """Independent finite-dimensional LP over ALL cellwise admissible slopes.

    Slopes v_j in [0,p] on equal report intervals. Minimize integrated
    payment with T(lower)=F; impose mean slope m. Coefficients integrate
    the continuous expectation exactly for each piecewise-linear schedule.
    No hinge shape is imposed on the optimizer.
    """
    if halfwidth<=0 or rate<=0 or target<0 or target>rate or n_cells<1:
        raise ValueError('Invalid LP domain.')
    edges=np.linspace(-halfwidth,halfwidth,n_cells+1)
    mids=(edges[:-1]+edges[1:])/2
    weights=(halfwidth-mids)/n_cells
    result=linprog(weights,A_eq=np.full((1,n_cells),1/n_cells),b_eq=[target],
                   bounds=[(0,rate)]*n_cells,method='highs')
    if not result.success:
        raise RuntimeError(result.message)
    return {'minimum_excess':float(result.fun), 'slopes':result.x,
            'status':int(result.status),'message':result.message,
            'mean_slope':float(result.x.mean())}


def discrete_contract(values,weights,excess,rate=1.0,floor=0.0):
    """Calibrate F+(a+pY)+ and retain atomic support for the counterexample."""
    y=np.asarray(values,dtype=float); w=np.asarray(weights,dtype=float)
    if len(y)!=len(w) or np.any(w<0) or not np.isclose(w.sum(),1) or excess<=0 or rate<=0:
        raise ValueError('Require valid probability mass and positive excess/rate.')
    a=brentq(lambda a: np.dot(w,np.maximum(a+rate*y,0))-excess,
             -rate*y.max(),excess-rate*y.min())
    payment=floor+np.maximum(a+rate*y,0)
    mean=float(np.dot(w,y))
    return {'intercept':float(a),'values':y,'weights':w,'payments':payment,
            'mean_payment':float(np.dot(w,payment)),
            'marginal':float(rate*np.dot(w,(a+rate*y)>0)),
            'variance':float(np.dot(w,(y-mean)**2))}
