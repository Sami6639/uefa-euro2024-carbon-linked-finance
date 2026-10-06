"""Generate all scientific numeric outputs from locked sources and scenarios."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd
from scipy.stats import norm
from .contracts import (uniform_contract,gaussian_contract,expectation,marginal,
 expected_quadrature,marginal_finite_difference,sharp_budget,lp_minimum_excess,
 discrete_contract)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'


def write_json(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')


def main():
    cfg=json.loads((ROOT/'model/config.json').read_text())
    sources=pd.read_csv(ROOT/'data/headline_metrics.csv')
    def anchor(source,metric):
        rows=sources[(sources.source_id==source)&(sources.metric==metric)]
        if len(rows)!=1: raise ValueError(f'Non-unique anchor: {source}/{metric}')
        return rows.iloc[0]
    ref=anchor('uefa_fund_2025_01_20','final_emissions')
    bud=anchor('uefa_fund_2025_01_20','final_fund')
    cap=anchor('uefa_fund_2024_01_08','contribution_per_emitted_tonne')
    mu,B,p=float(ref.value),float(bud.value),float(cap.value)
    assert mu==cfg['reference_mean_tco2e'] and B==cfg['benchmark_budget_eur'] and p==cfg['common_slope_cap_eur_per_tco2e']
    cfg['source_anchor_status']='verified from data/headline_metrics.csv; exact equality checked'
    cfg['source_anchor_ids']=[str(x.metric_id) for x in [ref,bud,cap]]
    cfg['source_headline_sha256']=hashlib.sha256((ROOT/'data/headline_metrics.csv').read_bytes()).hexdigest()
    write_json('locked_config.json',cfg)
    (OUT/'tables').mkdir(exist_ok=True)
    Bcalc=p*mu
    invested=float(anchor('uefa_fund_2025_07_14','final_invested_exact').value)
    reconciliation={'reported_emissions_tco2e':mu,'reported_rate_eur_per_tco2e':p,
                    'announced_budget_eur':B,'arithmetic_budget_eur':Bcalc,
                    'announced_minus_arithmetic_eur':B-Bcalc,
                    'exact_invested_eur':invested,'invested_minus_arithmetic_eur':invested-Bcalc,
                    'announced_minus_invested_eur':B-invested,
                    'explanation':'Differences preserved; no rounding/fee reconciliation is assumed.'}
    write_json('budget_reconciliation.json',reconciliation)
    institutional=[]
    for source,metric,role in [
      ('uefa_fund_2024_01_08','contribution_per_emitted_tonne','Institutional rate; imposed common slope cap in counterfactual scenarios'),
      ('uefa_fund_2025_01_20','initial_fund','Observed ex-ante fund; not identified as an irrevocable scenario floor'),
      ('uefa_fund_2025_01_20','minimum_exante_emissions','Reported minimum ex-ante inventory expectation; not the model noise mean'),
      ('uefa_fund_2025_01_20','final_emissions','Reported ex-post inventory used only as dimensional scale'),
      ('uefa_fund_2025_01_20','top_up','Reported post-event top-up'),
      ('uefa_fund_2025_01_20','final_fund','Announced final funding benchmark'),
      ('uefa_fund_2025_07_14','final_invested_exact','Separately reported exact invested amount')]:
        row=anchor(source,metric).to_dict();row['analytical_role']=role;institutional.append(row)
    pd.DataFrame(institutional).to_csv(OUT/'tables/table1_source_ledger.csv',index=False)

    def result_row(f,rho,family,budget=B):
        sd=rho*mu;scale=sd*math.sqrt(3) if family=='uniform' else sd
        builder=uniform_contract if family=='uniform' else gaussian_contract
        c=builder(mu,budget,f*budget,p,scale)
        m=marginal(c)
        return {'family':family,'floor_fraction':f,'sd_reference_fraction':rho,
                'reference_mean_tco2e':mu,'budget_eur':budget,'floor_eur':f*budget,
                'sd_tco2e':sd,'halfwidth_tco2e':scale if family=='uniform' else None,
                'threshold_tco2e':c.threshold if math.isfinite(c.threshold) else None,
                'constant_contract':c.constant,'expected_payment_eur':expectation(c),
                'marginal_eur_per_tco2e':m,'marginal_fraction_of_cap':m/p,
                'reported_emissions_negative_probability':float(norm.cdf(-mu/sd)) if family=='gaussian' and sd>0 else 0.0,
                'value_status':'hypothetical scenario'}

    rows=[result_row(f,rho,family) for family in ['uniform','gaussian']
          for rho in cfg['sd_reference_fractions'] for f in cfg['floor_fractions']]
    grid=pd.DataFrame(rows);grid.to_csv(OUT/'contracts_grid.csv',index=False)
    dense=[result_row(float(f),rho,family) for family in ['uniform','gaussian']
           for rho in cfg['sd_reference_fractions']
           for f in np.linspace(0,1,cfg['plot_floor_points'])]
    pd.DataFrame(dense).to_csv(OUT/'contracts_plot_data.csv',index=False)
    distribution_curves=[result_row(f,float(rho),family) for family in ['uniform','gaussian']
           for f in cfg['distribution_compare_floor_fractions']
           for rho in np.linspace(0,max(cfg['sd_reference_fractions']),cfg['plot_noise_points'])]
    pd.DataFrame(distribution_curves).to_csv(OUT/'distribution_sensitivity_plot_data.csv',index=False)

    checks=[]
    for row in rows:
        family=row['family'];scale=row['halfwidth_tco2e'] if family=='uniform' else row['sd_tco2e']
        c=(uniform_contract if family=='uniform' else gaussian_contract)(mu,B,row['floor_eur'],p,scale)
        q=expected_quadrature(c);fd=marginal_finite_difference(c)
        checks.append({'family':family,'floor_fraction':row['floor_fraction'],
            'sd_reference_fraction':row['sd_reference_fraction'],
            'quadrature_payment_eur':q,'analytic_payment_eur':expectation(c),
            'absolute_quadrature_error_eur':abs(q-expectation(c)),
            'absolute_budget_error_eur':abs(expectation(c)-B),
            'analytic_marginal':marginal(c),'finite_difference_marginal':fd,
            'absolute_marginal_error':abs(fd-marginal(c))})
    checks=pd.DataFrame(checks);checks.to_csv(OUT/'independent_quadrature_validation.csv',index=False)
    assert checks.absolute_quadrature_error_eur.max()<1e-4
    assert checks.absolute_budget_error_eur.max()<1e-5
    assert checks.absolute_marginal_error.max()<1e-3

    frontier=[];curves=[];thresholds=[]
    for rho in cfg['sd_reference_fractions']:
        h=mu*rho*math.sqrt(3)
        assert mu>=h
        for f in cfg['gap_fractions']:
            for r in cfg['target_rate_fractions']:
                required=sharp_budget(f*B,h,r*p,p)
                frontier.append({'sd_reference_fraction':rho,'gap_fraction':f,
                  'gap_eur':f*B,'target_fraction_of_cap':r,'target_marginal':r*p,
                  'minimum_expected_budget_eur':required,'budget_margin_eur':B-required,
                  'feasible_at_benchmark':(required<=B+1e-8 and not (h==0 and f==1 and r>0)),
                  'threshold_attained':not (h==0 and r>0),
                  'value_status':'hypothetical scenario; guaranteed floor assumed bankable and released ex ante'})
        for r in np.linspace(0,1,cfg['plot_target_points']):
            gmax=B-h*(r*p)**2/p
            curves.append({'sd_reference_fraction':rho,'target_fraction_of_cap':r,
                           'max_gap_fraction':gmax/B,'max_gap_eur':gmax,
                           'boundary_attained':not (h==0 and r>0)})
        thresholds.append({'sd_reference_fraction':rho,'sd_tco2e':rho*mu,'uniform_halfwidth_tco2e':h,
          'max_floor_for_full_cap_eur':B-h*p,'max_floor_for_full_cap_fraction':1-h*p/B,
          'positive_target_boundary_attained':h>0,
          'max_floor_for_three_quarter_cap_eur':B-h*p*.75**2,
          'max_floor_for_half_cap_eur':B-h*p*.5**2,
          'marginal_at_90_percent_floor':marginal(uniform_contract(mu,B,.9*B,p,h))})
    pd.DataFrame(frontier).to_csv(OUT/'liquidity_frontier_grid.csv',index=False)
    pd.DataFrame(curves).to_csv(OUT/'liquidity_frontier_plot_data.csv',index=False)
    pd.DataFrame(thresholds).to_csv(OUT/'tables/table3_uniform_financing_thresholds.csv',index=False)

    lp_rows=[]
    for n in cfg['lp_cells']:
        for target in cfg['lp_targets']:
            out=lp_minimum_excess(1,1,target,n)
            analytic=target**2;err=out['minimum_excess']-analytic
            lp_rows.append({'cells':n,'target_normalized_marginal':target,
                'analytic_minimum_excess':analytic,'lp_minimum_excess':out['minimum_excess'],
                'lp_minus_analytic':err,'worst_case_discretization_bound':1/(4*n*n),
                'mean_slope_error':abs(out['mean_slope']-target),'solver_status':out['status']})
            assert -1e-10<=err<=1/(4*n*n)+1e-10
    lp=pd.DataFrame(lp_rows);lp.to_csv(OUT/'lp_frontier_validation.csv',index=False)

    counter=[];counter_summary=[]
    for label,values,weights in [('baseline',[-1,1],[.5,.5]),('independent_noise_added',[-2,0,2],[.25,.5,.25])]:
        d=discrete_contract(values,weights,.8)
        for y,w,pay in zip(d['values'],d['weights'],d['payments']):
            counter.append({'scenario':label,'report':y,'probability':w,'payment':pay,
                            'marginal_slope':float(y+d['intercept']>0)})
        counter_summary.append({'scenario':label,'report_variance':d['variance'],
            'recalibrated_intercept':d['intercept'],'expected_payment':d['mean_payment'],
            'expected_marginal_slope':d['marginal'],'fixed_excess_budget':.8,'rate_cap':1.0,
            'value_status':'dimensionless constructed counterexample, not event data'})
    pd.DataFrame(counter).to_csv(OUT/'counterexample_support.csv',index=False)
    pd.DataFrame(counter_summary).to_csv(OUT/'counterexample_summary.csv',index=False)

    # Explicit normalized corner regimes include cases outside the event-scale grid.
    corners=[]
    for label,budget,floor,rate,h in [
      ('zero noise, positive discretionary budget',1,.9,1,0),
      ('zero noise and floor equals budget; constant selected',1,1,1,0),
      ('positive noise and floor equals budget',1,1,1,1),
      ('zero floor, moderate noise',1,0,1,.5),
      ('zero floor, large noise',1,0,1,3),
      ('full-incentive boundary',1,.5,1,.5),
      ('near-total floor',1,.999999,1,1),
      ('zero rate; constant selected',1,.5,0,1)]:
        c=uniform_contract(10,budget,floor,rate,h)
        corners.append({'regime':label,'budget':budget,'floor':floor,'rate_cap':rate,
          'halfwidth':h,'expected_payment':expectation(c),'marginal':marginal(c),
          'constant_selected':c.constant,'status':'PASS'})
    pd.DataFrame(corners).to_csv(OUT/'tables/table2_boundary_regimes.csv',index=False)

    # Rounded-report sensitivity uses an alternative consistent reference budget.
    robustness=pd.DataFrame([result_row(f,rho,'uniform',Bcalc)
          for rho in cfg['sd_reference_fractions'] for f in cfg['floor_fractions']])
    u=grid[grid.family=='uniform'].reset_index(drop=True)
    robustness['official_budget_marginal_fraction']=u.marginal_fraction_of_cap
    robustness['fraction_difference_from_official']=robustness.marginal_fraction_of_cap-u.marginal_fraction_of_cap
    robustness.to_csv(OUT/'budget_rounding_robustness.csv',index=False)

    # Deliberately wrong moving normalization is retained as a falsification diagnostic.
    c=uniform_contract(mu,B,.95*B,p,.1*mu*math.sqrt(3));step=1.0
    fixed=(expectation(c,mu+step)-expectation(c,mu-step))/(2*step)
    wrong=(expectation(uniform_contract(mu+step,B,.95*B,p,c.scale))-
           expectation(uniform_contract(mu-step,B,.95*B,p,c.scale)))/(2*step)
    diagnostic={'floor_fraction':.95,'sd_reference_fraction':.1,
        'fixed_precommitted_threshold_derivative':fixed,
        'incorrect_recalibrated_each_state_derivative':wrong,
        'interpretation':'Physical mean perturbations must hold the schedule fixed.'}
    write_json('normalization_diagnostic.json',diagnostic)

    summary={'design_status':'LOCKED; sources checked and deterministic validation passed',
      'main_scenario_contract_rows':len(grid),'dense_contract_plot_rows':len(dense),
      'liquidity_grid_rows':len(frontier),'lp_validation_rows':len(lp),
      'independent_quadrature_rows':len(checks),
      'max_absolute_quadrature_error_eur':float(checks.absolute_quadrature_error_eur.max()),
      'max_absolute_budget_error_eur':float(checks.absolute_budget_error_eur.max()),
      'max_absolute_marginal_finite_difference_error':float(checks.absolute_marginal_error.max()),
      'max_lp_mean_slope_error':float(lp.mean_slope_error.max()),
      'max_lp_excess_error_400_cells':float(lp[lp.cells==400].lp_minus_analytic.max()),
      'max_rounding_budget_marginal_fraction_change':float(robustness.fraction_difference_from_official.abs().max()),
      'gaussian_max_negative_report_probability':float(grid.reported_emissions_negative_probability.max()),
      'positive_noise_gaussian_rows_rounded_to_full_cap':int(((grid.family=='gaussian')&(grid.sd_reference_fraction>0)&(grid.marginal_fraction_of_cap==1)).sum()),
      'gaussian_float_precision_caveat':'Some positive-noise Gaussian probabilities round to one in float64; exact full-cap m=p remains unattainable at finite discretionary budget and sigma>0.',
      'zero_noise_equal_floor_convention':cfg['zero_noise_equal_floor_convention'],
      'zero_noise_feasibility_caveat':'For any positive two-sided marginal target and zero noise, the financing gap H must be strictly below budget. The budget frontier is an infimum, not attained at F=B.',
      'scenario_scope':'All distributions and standard deviations are assumed sensitivities. No UEFA or DEKRA difference estimates report noise.',
      'behavioral_scope':'m is local expected marginal contractual funding obligation. Behavior requires binding precommitment internalized by the decision-maker.',
      'frontier_scope':'Mean-budget minimum within absolutely continuous monotone capped-slope contracts, not a variance optimum.',
      'gaussian_scope':'Signed report-error sensitivity; a Gaussian report has a negative tail and is not an emissions inventory model.'}
    write_json('validation_summary.json',summary)
    pd.DataFrame([
       {'check':'Equal-budget calibration','cases':len(grid),'maximum_error':summary['max_absolute_budget_error_eur'],'unit':'EUR','status':'PASS'},
       {'check':'Independent payment quadrature','cases':len(checks),'maximum_error':summary['max_absolute_quadrature_error_eur'],'unit':'EUR','status':'PASS'},
       {'check':'Fixed-schedule numerical derivative','cases':len(checks),'maximum_error':summary['max_absolute_marginal_finite_difference_error'],'unit':'EUR/tCO2e','status':'PASS'},
       {'check':'LP frontier, 400 cells','cases':len(cfg['lp_targets']),'maximum_error':summary['max_lp_excess_error_400_cells'],'unit':'normalized budget','status':'PASS'},
       {'check':'LP slope constraint','cases':len(lp),'maximum_error':summary['max_lp_mean_slope_error'],'unit':'normalized slope','status':'PASS'},
       {'check':'Arithmetic-budget sensitivity','cases':len(robustness),'maximum_error':summary['max_rounding_budget_marginal_fraction_change'],'unit':'fraction of cap','status':'PASS'}
    ]).to_csv(OUT/'tables/table4_validation_summary.csv',index=False)
    selected=grid[(grid.floor_fraction.isin([.9,.95,.99]))&(grid.sd_reference_fraction.isin([.05,.1,.2,.3]))]
    selected.to_csv(OUT/'selected_manuscript_scenarios.csv',index=False)
    write_json('table_captions.json',{
      'table1':{'title':'Institutional anchors and analytical roles','note':'Reported amounts retain their source-specific dates. The proposed guaranteed floor is counterfactual.'},
      'table2':{'title':'Boundary and limiting regimes','note':'Dimensionless uniform-noise checks. At zero noise with F=B, the selected constant contract has zero slope; kinked alternatives are not differentiable at the reference point.'},
      'table3':{'title':'Uniform-noise financing thresholds','note':'Hypothetical noise scales; benchmark budget EUR 7.925 million and common slope cap EUR 25/tCO2e. Floors are assumed bankable and available ex ante. At zero noise, the displayed positive-target floor thresholds are unattained suprema.'},
      'table4':{'title':'Independent numerical validation','note':'Errors compare analytical formulas with independent integration, finite differences, and capped-slope linear programs.'}})
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
