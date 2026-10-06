"""Render publication figures from generated CSVs, never narrative constants."""
import os
from pathlib import Path
import json
os.environ.setdefault('MPLCONFIGDIR', '/tmp/euro-finance-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/euro-finance-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter,MultipleLocator
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';FIG=ROOT/'figures'
COLORS={.025:'#1F4E79',.05:'#B07D24',.1:'#B35A29',.2:'#708238',.3:'#A75983'}
STYLES={.025:'-',.05:'--',.1:'-.',.2:':',.3:(0,(5,1))}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,
 'axes.titlesize':12,'axes.labelsize':11,'xtick.labelsize':10,'ytick.labelsize':10,
 'legend.fontsize':9.5,'axes.edgecolor':'#555555','axes.labelcolor':'#252525',
 'text.color':'#252525','xtick.color':'#444444','ytick.color':'#444444',
 'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,
 'lines.linewidth':2.0,'savefig.facecolor':'white','figure.facecolor':'white',
 'pdf.fonttype':42,'svg.fonttype':'none'})

def style(ax,percent=True):
    ax.set_axisbelow(True);ax.grid(axis='y',color='#E5E5E5',linewidth=.6)
    ax.tick_params(length=3,width=.6)
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.set_ylim(-.015,1.06)

def save(fig,name):
    FIG.mkdir(exist_ok=True)
    for suffix in ['png','pdf','svg']:
        fig.savefig(FIG/f'{name}.{suffix}',dpi=300,bbox_inches='tight')
    plt.close(fig)

def main():
    cfg=json.loads((OUT/'locked_config.json').read_text())
    d=pd.read_csv(OUT/'contracts_plot_data.csv')
    fig,ax=plt.subplots(figsize=(7.2,4.7))
    for rho in cfg['sd_reference_fractions']:
        sub=d[(d.family=='uniform')&np.isclose(d.sd_reference_fraction,rho)]
        if rho==0:
            keep=sub.floor_fraction<1
            ax.plot(sub.loc[keep,'floor_fraction'],sub.loc[keep,'marginal_fraction_of_cap'],
                color='#555555',ls='--',lw=1.4,label='Zero noise')
            ax.plot([1],[1],marker='o',mfc='white',mec='#555555',ms=5,zorder=5)
            ax.plot([1],[0],marker='o',color='#555555',ms=4,zorder=5)
        else:
            ax.plot(sub.floor_fraction,sub.marginal_fraction_of_cap,
                color=COLORS[rho],ls=STYLES[rho],label=f'$\\sigma/e^*=$ {rho:.1%}')
    ax.set_title('Guaranteed funding and marginal obligation',loc='left',pad=12)
    ax.set_xlabel('Guaranteed floor as a share of budget, $F/B$')
    ax.set_ylabel('Expected marginal obligation, $m/p$')
    ax.set_xlim(0,1.015);style(ax)
    ax.legend(loc='lower left',ncol=2,frameon=False)
    fig.tight_layout();save(fig,'figure1_floor_marginal_obligation')

    d=pd.read_csv(OUT/'liquidity_frontier_plot_data.csv')
    fig,ax=plt.subplots(figsize=(7.2,4.7))
    for rho in [0,.05,.1,.2,.3]:
        sub=d[np.isclose(d.sd_reference_fraction,rho)]
        ax.plot(sub.target_fraction_of_cap,sub.max_gap_fraction,
                color='#555555' if rho==0 else COLORS[rho],
                ls='--' if rho==0 else STYLES[rho],
                label='Zero-noise supremum' if rho==0 else f'$\\sigma/e^*=$ {rho:.0%}')
    ax.set_title('Upfront financing and a required marginal obligation',loc='left',pad=12)
    ax.set_xlabel('Required marginal obligation as a share of the cap, $q/p$')
    ax.set_ylabel('Maximum upfront gap as a share of budget, $H/B$')
    ax.set_xlim(0,1.01);style(ax);ax.set_ylim(0,1.07)
    ax.legend(loc='lower left',ncol=2,frameon=False)
    ax.text(.59,.35,'Feasible below each boundary',fontsize=10,color='#555555',ha='center')
    fig.tight_layout();save(fig,'figure2_liquidity_feasibility')

    d=pd.read_csv(OUT/'distribution_sensitivity_plot_data.csv')
    fig,axs=plt.subplots(1,2,figsize=(8.3,4.25),sharex=True,sharey=True)
    for ax,f in zip(axs,cfg['distribution_compare_floor_fractions']):
        for family,col,ls in [('uniform','#1F4E79','-'),('gaussian','#B35A29','--')]:
            sub=d[(d.family==family)&np.isclose(d.floor_fraction,f)]
            ax.plot(sub.sd_reference_fraction,sub.marginal_fraction_of_cap,
                color=col,ls=ls,label=family.capitalize())
        ax.set_title(f'Guaranteed floor: {f:.0%} of budget',loc='left',pad=10)
        ax.set_xlabel('Assumed noise scale, $\\sigma/e^*$')
        ax.set_xlim(0,.3);ax.xaxis.set_major_locator(MultipleLocator(.1));style(ax)
    axs[0].set_ylabel('Expected marginal obligation, $m/p$')
    axs[0].legend(loc='lower left',frameon=False)
    fig.tight_layout(w_pad=1.5);save(fig,'figure3_distribution_sensitivity')

    d=pd.read_csv(OUT/'counterexample_support.csv');summary=pd.read_csv(OUT/'counterexample_summary.csv')
    fig,axs=plt.subplots(1,3,figsize=(9.2,3.65),gridspec_kw={'width_ratios':[1,1,1.05]})
    for ax,label,title in zip(axs[:2],['baseline','independent_noise_added'],
                             ['A. Original report','B. Independent noise added']):
        sub=d[d.scenario==label];ax.vlines(sub.report,0,sub.probability,color='#1F4E79',lw=2)
        ax.scatter(sub.report,sub.probability,s=36,c='#1F4E79',zorder=4)
        ax.set_xticks([-2,-1,0,1,2]);ax.set_ylim(0,.58);ax.set_xlim(-2.45,2.45)
        ax.set_title(title,loc='left',pad=10,fontsize=11)
        ax.set_xlabel('Centered report (normalized)')
        ax.set_axisbelow(True);ax.grid(axis='y',color='#E5E5E5',linewidth=.6)
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    axs[0].set_ylabel('Probability mass')
    ax=axs[2]
    vals=summary.expected_marginal_slope.to_numpy()
    ax.bar([0,1],vals,width=.55,color=['#1F4E79','#B35A29'],edgecolor='#333333',linewidth=.5)
    for i,v in enumerate(vals):ax.text(i,v+.025,f'{v:.0%}',ha='center',fontsize=11)
    ax.set_xticks([0,1],['Original','Noise added']);ax.set_ylim(0,1)
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.set_title('C. Expected marginal slope',loc='left',pad=10,fontsize=11)
    ax.set_xlabel('Equal expected payment\nin both cases')
    ax.set_axisbelow(True);ax.grid(axis='y',color='#E5E5E5',linewidth=.6)
    fig.tight_layout(w_pad=1.5);save(fig,'figure4_noise_counterexample')
    captions={
      'figure1':{'file':'figure1_floor_marginal_obligation','title':'Guaranteed funding and marginal obligation.',
        'note':'Uniform hypothetical report noise; sigma/e* denotes an assumed standard deviation. B=EUR 7.925m, p=EUR 25/tCO2e. At zero noise and F=B, the selected constant contract has m=0; the upper endpoint is open.'},
      'figure2':{'file':'figure2_liquidity_feasibility','title':'Upfront financing and required marginal obligation.',
        'note':'Uniform hypothetical noise with the same benchmark budget and cap. Financing gaps are assumed bankable and payable from the floor before verification. At zero noise, g=B is excluded for any positive target.'},
      'figure3':{'file':'figure3_distribution_sensitivity','title':'Distribution-dependent marginal obligations.',
        'note':'Hypothetical uniform and Gaussian errors have equal variance at each sigma/e*; each schedule is calibrated to the same expected budget. Gaussian reporting is a signed-error sensitivity, with a negative-report tail.'},
      'figure4':{'file':'figure4_noise_counterexample','title':'A mean-preserving spread can raise the marginal obligation.',
        'note':'Dimensionless counterexample, not event data. Adding an independent symmetric unit noise raises variance from 1 to 2 and the local expected slope from 0.50 to 0.75; expected payment remains 0.80 and p=1.'}}
    (OUT/'figure_captions.json').write_text(json.dumps(captions,indent=2)+'\n', newline="\n")
    print('Rendered four figures in PNG, PDF and SVG.')

if __name__=='__main__':main()
