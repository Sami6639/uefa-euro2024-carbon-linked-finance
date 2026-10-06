#!/usr/bin/env python3
"""Build auditable, tidy CSV transcriptions; this is not an emissions model.

All numerical literals below are reviewed public-source values. Values computed
here are unit conversions or explicitly labelled reconciliation diagnostics.
No individual-level data, absolute emission factors, or project outcomes are
imputed. See data/README_DATA.txt and the row-level source/page columns.
"""
from pathlib import Path
import csv, datetime as dt, hashlib, importlib.metadata, json, platform, re, shutil, subprocess, sys
from lxml import html
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data'; RAW=D/'raw'
CAT={s['source_id']:s for s in json.loads((D/'source_catalog.json').read_text())}
TODAY='2026-10-06' # fixed snapshot date of the reviewed source archive

def write_csv(name, rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (D/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def provenance(source_id, page='', locator=''):
    s=CAT[source_id]
    return {'source_id':source_id,'source_date':s['source_date'],'retrieved_date_utc':TODAY,
            'source_url':s['url'],'source_pdf_page':page,'source_locator':locator}

manifest=[]
for sid,s in CAT.items():
    path=RAW/(sid+'.'+s['extension']); b=path.read_bytes()
    receipt_path=RAW/(sid+'.retrieval.json')
    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    row={**s,'raw_relative_path':str(path.relative_to(ROOT)),'retrieved_date_utc':TODAY,
         'retrieved_at_utc':receipt.get('retrieved_at_utc',''),
         'retrieval_time_precision':'exact' if receipt else 'date_only',
         'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'downloaded_and_read',
         'pdf_pages':'','pdf_creation_date':'','pdf_modification_date':''}
    if s['extension']=='pdf':
        reader=PdfReader(path);row['pdf_pages']=len(reader.pages)
        row['pdf_creation_date']=reader.metadata.get('/CreationDate','')
        row['pdf_modification_date']=reader.metadata.get('/ModDate','')
        subprocess.run(['pdftotext','-layout',str(path),str(path.with_suffix('.txt'))],check=True)
    else:
        tree=html.fromstring(b)
        articles=tree.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," article_body ")]')
        if articles:
            article=articles[0]
            text='\n'.join(t.strip() for t in article.itertext() if t.strip())
        else:
            for e in tree.xpath('//script|//style|//nav|//footer|//header'): e.drop_tree()
            text='\n'.join(t.strip() for t in tree.itertext() if t.strip())
        path.with_suffix('.txt').write_text(text,encoding='utf-8')
    manifest.append(row)
write_csv('source_manifest.csv',manifest)

metrics=[]
def m(sid,metric,value,unit,scope,status,page='',locator='',notes='',year=2024,qualifier='reported'):
    metrics.append(dict(metric_id=f'{sid}__{metric}',metric=metric,value=value,unit=unit,
        event_year=year,scope=scope,observation_status=status,value_qualifier=qualifier,
        notes=notes,**provenance(sid,page,locator)))

# UEFA emissions are estimates from a footprint calculator, not directly observed tonnes.
U='uefa_esg_2024'; DK='dekra_expost_2024'; O='oeko_exante_2022'
for metric,val,scope,status in [
 ('operations_emissions',67955,'UEFA operations','ex_post_estimate'),
 ('ticket_travel_emissions',248957,'UEFA ticket-holder travel','ex_post_estimate'),
 ('total_emissions',316912,'UEFA operations plus ticket-holder travel','ex_post_estimate'),
 ('operations_forecast',78000,'UEFA operations forecast','ex_ante_estimate'),
 ('ticket_travel_forecast',330000,'UEFA ticket-holder travel forecast','ex_ante_estimate')]:
    m(U,metric,val,'tCO2e',scope,status,12,'Achieving reduction; Reduction results','2022 DEFRA factors stated in footnote. Forecasts are source-reported retrospectively.')
m(U,'forecast_total_arithmetic',408000,'tCO2e','UEFA operations plus ticket-holder travel forecast','derived_sum',12,'78,000 plus 330,000','Sum of the two displayed forecasts; distinct from the 280,000-tonne minimum fund basis.',qualifier='derived')
m(U,'fund_rounded',8000000,'EUR','Climate fund, ESG report version','reported_rounded',13,'Advocacy','Page 14 says just over €8m; do not replace with the later €7.925m.')
m(U,'club_projects_investment_rounded',5900000,'EUR','Club projects, ESG report version','reported_rounded',14,'Investing in climate resilience')
for metric,val,unit in [('clubs',227,'clubs'),('mitigation_projects',328,'projects'),('regional_associations',21,'associations'),('fund_applicants',5586,'clubs'),('average_project_cost',30400,'EUR')]:
    m(U,metric,val,unit,'Climate fund, ESG report version','administrative_report',14,'Investing in climate resilience','Different units/counts and versions are retained rather than reconciled by assumption.')
m(U,'expected_lifetime_savings',67000,'tonnes_carbon_emissions','Fund projects over their lifecycle','expected_lifetime_estimate',14,'Investing in climate resilience','Page 13 uses past-tense avoided wording, but p14 explicitly says expected over the life cycle. Not measured realised savings.',qualifier='roughly')
m(DK,'total_emissions',778968,'tCO2e','DEKRA full boundary including fan zones and accommodation','ex_post_estimate',21,'Table 1 and Figure 11','Source total retained; rounded category values do not all sum exactly.')
m(DK,'restricted_boundary_emissions',463970.80,'tCO2e','DEKRA Table 19 excluding fan zones and accommodation','ex_post_estimate',43,'Table 19','This boundary approximation is not equal to the UEFA inventory; reconciliation is unresolved.')
m(DK,'all_mobility_emissions',683975,'tCO2e','All mobility including fan zones and EURO GmbH','ex_post_estimate',23,'Table 4 / section 3.2','Do not confuse with 445,169 main transport block, which excludes fan-zone mobility and EURO GmbH business travel.')
m(DK,'baseline_exante_emissions',490000,'tCO2e','Öko-Institut ex-ante boundary as reported by DEKRA','ex_ante_estimate',31,'Table 12','Rounded; also verified directly in the original Öko-Institut report.')
m(DK,'minimum_fund_basis',280000,'tCO2e','Original UEFA fund basis','ex_ante_estimate',44,'Climate responsibility','Different boundary and planned reduction strategies, footnote 23.',qualifier='around')
m(DK,'hypothetical_restricted_fund',11600000,'EUR','DEKRA restricted boundary at €25/tCO2e','source_hypothetical',44,'Climate responsibility','Source rounding, not actual UEFA commitment.',qualifier='rounded')
m(O,'baseline_exante_emissions',490000,'tCO2e','Öko-Institut full ex-ante event boundary','ex_ante_estimate',20,'Figure 3-1','Prepared autumn 2021 to spring 2022; cover dated 6 July 2022.',qualifier='approximately')
for price,budget in [(25,12000000),(50,24000000),(100,48000000)]:
    m(O,f'illustrative_budget_at_{price}',budget,'EUR','Öko-Institut source illustrative price scenario','source_hypothetical',59,'Table 6-1',f'Source gives rounded figure at {price} EUR/tCO2e; do not silently replace with arithmetic product.',qualifier='source_rounded')
J='uefa_fund_2024_01_08'; JUL='uefa_fund_2024_07_10'; F='uefa_fund_2025_01_20'; C='uefa_fund_2025_07_14'; L='uefa_fund_landing'
for sid in [J,L]:
    for metric,val,unit,status in [('contribution_per_emitted_tonne',25,'EUR/tCO2_emitted','policy_rule'),('initial_fund',7000000,'EUR','announced_budget'),('max_grant',250000,'EUR','policy_rule'),('club_contribution_rate',10,'percent','policy_rule'),('club_contribution_cap',5000,'EUR','policy_rule'),('simplified_application_threshold',25000,'EUR','policy_rule')]:
        m(sid,metric,val,unit,'UEFA climate fund',status,locator='Fund description and application terms',notes='€25 denominator is tournament emissions produced, not funded-project tonnes avoided. Initial fund is approximately €7m. Contribution wording: minimum 10% of requested grant capped at €5,000.')
for metric,val,unit,status in [('fund',7000000,'EUR','announced_allocation'),('clubs',190,'clubs','administrative_report'),('regional_associations',21,'associations','administrative_report'),('club_funding',4900000,'EUR','reported_rounded'),('regional_allocation_each',100000,'EUR','reported_allocation'),('third_round',698000,'EUR','reported_allocation'),('third_round_clubs',30,'clubs','administrative_report'),('applications',5586,'clubs','administrative_report'),('expected_lifetime_savings',60000,'tonnes_carbon_emissions','expected_lifetime_estimate')]:
    m(JUL,metric,val,unit,'UEFA climate fund July 2024 version',status,locator='Article body; Over 5,000 applications',notes='Club funding stated over €4.9m; total just over €7m. Savings are rough lifecycle expectations, not realised outcomes. 80+81+30=191 round counts differs from reported total 190.')
for metric,val,unit,status in [('initial_fund',7000000,'EUR','announced_budget'),('minimum_exante_emissions',280000,'tCO2e','ex_ante_estimate'),('final_emissions',316912,'tCO2e','ex_post_estimate'),('top_up',925000,'EUR','reported_allocation'),('final_fund',7925000,'EUR','reported_allocation'),('additional_clubs',35,'clubs','administrative_report'),('total_clubs',225,'clubs','administrative_report'),('energy_projects',184,'projects','administrative_report'),('water_projects',20,'projects','administrative_report'),('waste_projects',9,'projects','administrative_report'),('mobility_projects',12,'projects','administrative_report')]:
    m(F,metric,val,unit,'UEFA final-round fund version',status,locator='Opening paragraphs; More than 200 clubs',notes='Original emissions basis explicitly a minimum. Article posted 2025-01-20 and last updated 2025-02-18.')
for metric,val,unit,status in [('final_budget',7925000,'EUR','reported_budget'),('final_invested_exact',7923013,'EUR','reported_disbursement'),('club_allocation',5825000,'EUR','reported_allocation'),('regional_allocation',2100000,'EUR','reported_allocation'),('appointed_clubs',225,'clubs','administrative_report'),('club_reports_verified',211,'clubs','administrative_report'),('club_reports_pending',14,'clubs','administrative_report'),('regional_associations',21,'associations','administrative_report'),('regional_reports_received',13,'associations','administrative_report'),('regional_reports_pending',8,'associations','administrative_report'),('required_contracts_signed',66,'contracts','administrative_report')]:
    m(C,metric,val,unit,'UEFA closure version',status,locator='Reporting and transparency; Financial overview',notes='Status as of 1 June 2025, published 14 July 2025. Allocations sum to €7.925m while total invested is separately reported as €7,923,013. Final reports still pending within agreed deadlines.')
write_csv('headline_metrics.csv',metrics)

# Appendix 1 is an emissions hierarchy: category totals and components are NOT additive together.
appendix=[
('transport','Transport',445169,57.1,51,'category_total'),
('transport','International stadium-visitor travel',371712,47.7,51,'component'),
('transport','National stadium-visitor travel',69209,8.9,51,'component'),
('transport','National-team arrival and departure',983,0.1,51,'component'),
('transport','National-team domestic travel',681,0.1,51,'component'),
('transport','Volunteer mobility',366,0.0,51,'component'),
('transport','Other mobility',2219,0.3,51,'component'),
('energy','Energy',496,0.1,51,'category_total'),
('energy','Stadium electricity',266,0.0,51,'component'),
('energy','Stadium natural gas',142,0.0,51,'component'),
('energy','Stadium diesel and renewable fuel',56,0.0,51,'component'),
('energy','Stadium refrigerants',32,0.0,51,'component'),
('catering','Catering',6875,0.9,51,'category_total'),
('catering','Stadium drinks',3709,0.5,51,'component'),
('catering','Stadium food public',1917,0.2,51,'component'),
('catering','Stadium food hospitality',567,0.1,51,'component'),
('catering','Stadium food staff',346,0.0,51,'component'),
('catering','Stadium food and beverage dispensing materials',336,0.0,51,'component'),
('accommodation','Accommodation',31811,4.1,51,'category_total'),
('accommodation','German-resident fans',7558,1.0,51,'component'),
('accommodation','International-resident fans',22439,2.9,51,'component'),
('accommodation','Teams',1453,0.2,51,'component'),
('accommodation','Officials',2,0.0,51,'component'),
('accommodation','Other persons',170,0.0,51,'component'),
('accommodation','Volunteers',188,0.0,51,'component'),
('organisation','Organisation',1953,0.3,51,'category_total'),
('organisation','EURO GmbH office electricity',0.03,0.0,51,'component'),
('organisation','EURO GmbH office heat',2,0.0,51,'component'),
('organisation','EURO GmbH office materials',0.001,0.0,51,'component'),
('organisation','EURO GmbH fleet',10,0.0,51,'component'),
('organisation','EURO GmbH staff business travel arrival and departure',1817,0.2,51,'component'),
('organisation','EURO GmbH staff business-travel accommodation',117,0.0,51,'component'),
('organisation','EURO GmbH waste',6,0.0,51,'component'),
('materials','Materials',9147,1.2,51,'category_total'),
('materials','Merchandising',2333,0.3,51,'component'),
('materials','Advertising and branding',308,0.0,51,'component'),
('materials','Stadium conversion and fit-out',3315,0.4,51,'component'),
('materials','International Broadcasting Centre',3159,0.4,51,'component'),
('materials','Water supply',32,0.0,51,'component'),
('waste','Waste',330,0.0,51,'category_total'),
('waste','Stadium waste',330,0.0,51,'component'),
('fan_zones','Fan zones',283186,36.4,52,'category_total'),
('fan_zones','Regional visitor travel',7660,1.0,52,'component'),
('fan_zones','Supraregional visitor travel',23962,3.1,52,'component'),
('fan_zones','International visitor travel Europe',113958,14.6,52,'component'),
('fan_zones','International visitor travel non-Europe',91408,11.7,52,'component'),
('fan_zones','Electricity',66,0.0,52,'component'),
('fan_zones','Fuel',243,0.0,52,'component'),
('fan_zones','Food',2075,0.3,52,'component'),
('fan_zones','Drinks',4258,0.5,52,'component'),
('fan_zones','Food and beverage dispensing materials',460,0.1,52,'component'),
('fan_zones','Materials',911,0.1,52,'component'),
('fan_zones','Waste',632,0.1,52,'component'),
('fan_zones','Services',10592,1.4,52,'component'),
('fan_zones','Refrigerants',0.35,0.0,52,'component'),
('fan_zones','Accommodation',26441,3.4,52,'component'),
('fan_zones','Transport and logistics',520,0.1,52,'component'),
('all','Total emissions',778968,100.0,52,'grand_total')]
components=[dict(component_id=f'DK_APPENDIX_{i:02d}',category=a,item=b,emissions_tco2e=c,
    reported_share_percent=d,row_type=f,event_year=2024,unit='tCO2e',
    observation_status='ex_post_estimate',notes='Rounded source values; zero share is rounded percentage, not zero emissions.',
    **provenance(DK,e,'Appendix 1')) for i,(a,b,c,d,e,f) in enumerate(appendix,1)]
write_csv('dekra_emissions_components.csv',components)
restricted=[('transport',445169.13,95.95),('energy',495.53,0.11),('catering',6875.12,1.48),
            ('organisation',1953.33,0.42),('materials',9147.35,1.97),('waste',330.34,0.07),
            ('total',463970.80,100.0)]
write_csv('dekra_restricted_boundary.csv',[dict(category=a,emissions_tco2e=b,reported_share_percent=c,
    row_type='total' if a=='total' else 'component',unit='tCO2e',event_year=2024,
    observation_status='ex_post_estimate',notes='Table19 boundary excludes fan zones and accommodation; not the UEFA published inventory.',
    **provenance(DK,43,'Table 19')) for a,b,c in restricted])

# Visual transcriptions of raster tables 13-18, checked against stored page images.
mode_labels={'air_long':'Flugzeug (Langstrecke)','air_medium':'Flugzeug (Mittelstrecke)',
 'air_short':'Flugzeug (Kurzstrecke)','rail_long':'Bahn (Fernverkehr)','coach':'Reisebus',
 'car':'Pkw','rail_local':'Bahn (Nahverkehr)','bus_local':'Linienbus (Nahverkehr)',
 'tram_metro':'Straßen-, Stadt- und U-Bahn','ebike_scooter':'E-Bike/E-Scooter','cycle_walk':'Fahrrad/Fuß'}
tables={
13:('ticket_holders','international',35,1926.96,[('air_long',411.14,21.34),('air_medium',192.55,9.99),('air_short',485.42,25.19),('rail_long',416.91,21.64),('coach',31.48,1.63),('car',389.46,20.21)]),
14:('ticket_holders','national',36,640.31,[('air_short',30.18,4.71),('rail_long',183.34,28.63),('coach',4.14,0.65),('car',175.59,27.42),('rail_local',162.36,25.36),('bus_local',16.87,2.63),('tram_metro',64.49,10.07),('ebike_scooter',0.09,0.01),('cycle_walk',3.24,0.51)]),
15:('fan_zone_visitors','international',36,976.68,[('air_long',668.83,68.48),('air_medium',86.64,8.87),('air_short',121.72,12.46),('rail_long',35.46,3.63),('coach',5.88,0.60),('car',45.81,4.69),('rail_local',8.44,0.86),('bus_local',1.47,0.15),('tram_metro',2.23,0.23),('ebike_scooter',0.20,0.02),('cycle_walk',0.00,0.00)]),
16:('fan_zone_visitors','national',37,307.95,[('air_short',7.83,2.54),('rail_long',108.29,35.21),('coach',4.51,1.47),('car',97.11,31.57),('rail_local',41.39,13.46),('bus_local',8.19,2.66),('tram_metro',39.00,12.68),('ebike_scooter',1.27,0.41),('cycle_walk',0.00,0.00)]),
17:('national_teams','international',38,3.24,[('air_medium',0.16,5.04),('air_short',3.05,94.09),('coach',0.03,0.87)]),
18:('national_teams','national',38,3.67,[('air_short',1.98,53.95),('coach',0.49,13.30),('rail_long',1.20,32.75)])}
activity=[]
for table,(group,route,page,total,rows) in tables.items():
    for mode,million,share in rows+[('total',total,100.0)]:
        missing=(group=='fan_zone_visitors' and mode=='cycle_walk')
        notes=''
        if missing: notes='Source displays 0.00 but footnote says walking/cycling activity could not be included due to data availability; not an observed zero.'
        elif table==18 and mode=='air_short': notes='Table share 53.95%; adjacent narrative says 53.59%. Table retained; discrepancy logged.'
        activity.append(dict(activity_id=f'DK_T{table}_{mode}',population=group,travel_scope=route,
            mode=mode,source_mode_label=mode_labels.get(mode,'Gesamt'),reported_activity_million_pkm=million,
            activity_pkm=None if missing else round(million*1000000),reported_share_percent=share,
            source_unit='million passenger-km',unit='passenger-km',event_year=2024,
            row_type='total' if mode=='total' else 'component',
            observation_status='not_observed_source_placeholder_zero' if missing else 'ex_post_activity_estimate',
            absolute_emission_factor='',absolute_factor_status='not_disclosed_in_tables_13_18',notes=notes,
            **provenance(DK,page,f'Table {table}')))
write_csv('transport_activity.csv',activity)

factors=[]
for mode,val in [('air_medium',-238),('air_short',-251),('car',-112)]:
    factors.append(dict(factor_id='DK_SHIFT_'+mode,from_mode=mode,to_mode='rail_long',factor_value=val,
       factor_unit='gCO2e/passenger-km',factor_kind='difference_new_minus_old',
       absolute_factor_available=False,activity_year=2024,observation_status='source_counterfactual_parameter',
       notes='Published change when shifting to long-distance rail. Rail assumed 20% longer than flight distance, footnote 7. Absolute mode factors are not disclosed here; do not infer them.',
       **provenance(DK,35,'Text beside Table 13; footnote 7')))
write_csv('transport_differential_factors.csv',factors)

factor_sources=[
 ('transport','person-km and travel-time data','UBA; DEFRA','2024 DEFRA, UBA undated',19,'Transport and logistics factors; complete numerical mapping not disclosed.'),
 ('energy','energy/fuel/refrigerant consumption','Energy suppliers; BAFA; DEFRA','BAFA 2022; DEFRA 2024',19,'Specific supplier factors preferred; upstream emissions included.'),
 ('catering','food and beverage quantities','ifeu; ecoinvent; Eaternity','ifeu 2020; ecoinvent v3.10; Eaternity undated',19,'Exact food-item quantities and assigned factors not all published.'),
 ('accommodation','person-nights','UBA; DEFRA','DEFRA 2024; German location',19,'Country-specific German accommodation values used.'),
 ('materials','material quantities and expenditure','European Commission; ecoinvent; BAFA; ctrl+s','European Commission 2014; ecoinvent v3.10; other dates vary',20,'Textile/material factors and spend-based factors; no complete activity-factor cells published.'),
 ('services','purchased service expenditure','ctrl+s','undated',20,'Spend-based calculation; amounts and exact factors not completely public.'),
 ('waste','waste quantities','ifeu','2021 study for Berlin 2020',20,'Waste treatment credits excluded.'),
 ('fan_zones','mixed activities, some visitor-based extrapolation','same factors as stadiums','mixed, as above',20,'Same factors for comparability; missing activity records were extrapolated.'),
 ('uefa_inventory','UEFA Carbon Footprint Calculator inputs','DEFRA','2022',12,'Version explicitly stated; do not harmonise with DEKRA factors without new primary data.')]
write_csv('factor_provenance.csv',[dict(category=a,activity_basis=b,factor_source_family=c,
    reported_factor_version=d,numeric_factor_available=False,observation_status='method_disclosure',notes=f,
    **provenance(U if a=='uefa_inventory' else DK,e,'Methodology / factor-source description')) for a,b,c,d,e,f in factor_sources])

input_rows=[
('stadium_tickets',2800000,2680461,'tickets'),('german_resident_ticket_share',68,56,'percent'),
('tickets_per_person',2.1,1.5,'tickets/person'),('international_fan_travel',1400000000,1926963518,'passenger-km'),
('team_travel',5200000,6916399,'passenger-km'),('officials',4500,4500,'persons'),
('media',14000,14000,'persons'),('volunteers',16000,13900,'persons'),('other_staff',110000,110000,'persons'),
('german_resident_fan_nights',950000,598129,'person-nights'),('international_resident_fan_nights',1800000,1793624,'person-nights'),
('other_person_nights',380000,79837,'person-nights'),('stadium_electricity',11000000,10123350,'kWh'),
('stadium_diesel',270000,21000,'litres'),('stadium_food',1300000,1770000,'servings'),
('stadium_drinks',4300000,4700000,'servings'),('euro_gmbh_fleet',758,797,'vehicles'),
('distinct_fan_zone_visitors',3800000,6139300,'persons'),('total_emissions_rounded',490000,780000,'tCO2e')]
inputs=[]
for metric,before,after,unit in input_rows:
    for version,value in [('ex_ante',before),('ex_post',after)]:
        inputs.append(dict(input_id=f'DK_T12_{metric}_{version}',metric=metric,version=version,value=value,
        unit=unit,event_year=2024,observation_status='ex_ante_estimate' if version=='ex_ante' else 'source_ex_post_input_mixed_provenance',
        notes='Transcribed from Table 12; ex-post inputs may include surveys, extrapolations and assumptions. Rounded total is not the headline 778,968.',
        **provenance(DK,31,'Table 12')))
write_csv('exante_expost_inputs.csv',inputs)

rules=[
('application_open','2024-01-08',J,'Article opening','Date'),
('application_close','2024-06-30',J,'Article opening','Date'),
('tournament_start','2024-06-14',DK,'Cover','Date'),
('tournament_end','2024-07-14',DK,'Cover','Date'),
('dekra_submission_cutoff','2024-09-13',DK,'p11 section 2.3','Data submitted after this cutoff excluded.'),
('dekra_inventory_window','mid-May to mid-August 2024',DK,'p12 section 2.4','Organisation/preparation and materials use other periods.'),
('final_topup_announcement','2025-01-20',F,'Article dateline','Current page last updated 2025-02-18.'),
('closure_status_asof','2025-06-01',C,'Opening paragraph','Not all beneficiary reports were complete.'),
('closure_article_date','2025-07-14',C,'Article dateline','English version.'),
('contribution_denominator','tonnes of emissions produced in connection with EURO 2024',J,'Fund description','Not avoided tonnes; not a carbon-credit price.'),
('cofinance_early_wording','minimum 10% of requested grant, capped at EUR 5,000',J,'Application terms','Preserved wording; later source describes 10% of total costs.'),
('cofinance_later_wording','10% of total costs, capped at EUR 5,000',JUL,'Over 5,000 applications','Do not force a single denominator across source versions.'),
('lifecycle_savings_period','average project lifecycles, years not enumerated',JUL,'Savings paragraph','No annual series, discount schedule or verified realised abatement is supplied.'),
('dekra_emissions_data_kind','inventory estimates, not exact measurements',DK,'pp45–46','Factors, extrapolation, incomplete data and survey uncertainty.'),
('fan_zone_missingness','three fan zones largely extrapolated; some other gaps',DK,'pp12,18,46','No uncertainty distribution or raw city microdata is published.'),
('survey_sample_ticket_holders','13387',DK,'p14 section 2.4.1','Expanded to 1.7m stadium visitors; assumed 56% domestic and 44% international.'),
('survey_sample_fan_zone_visitors','2728',DK,'p18 section 2.4.8','Expanded to 6.139m visitors.'),
('factors_uefa','2022 DEFRA emission factors',U,'pp11–12','Version as stated; not substituted with 2024 factors.'),
('factors_dekra','UBA and DEFRA 2024 transport factors plus multiple other databases',DK,'pp19–20,48–50','All factors include upstream emissions; exact complete factor-to-activity mapping is not disclosed.'),
('uefa_verification_status','assessment is being independently verified',U,'p11','Statement is ongoing verification, not evidence of a completed assurance certificate in this source.'),
('offsetting_status','climate responsibility funding rather than traditional credits',U,'p14','Expected project savings cannot be subtracted from event footprint as verified offsets.'),
('additionality_warning','baseline and actual savings difficult to establish; formal additionality not fulfilled',O,'p58','Source conceptual warning, not a project-level evaluation.')]
write_csv('timing_and_rules.csv',[dict(rule_id=a,reported_value=b,notes=e,**provenance(c,'',d)) for a,b,c,d,e in rules])

reconciliations=[
('scope_uefa_vs_dekra',316912,778968,'tCO2e','different_boundaries','Do not treat difference as sampling uncertainty. DEKRA includes fan zones and accommodation. Other method/factor differences persist.','UEFA p12; DEKRA pp21,43'),
('restricted_dekra_vs_uefa',463970.8,316912,'tCO2e','unresolved_difference','Removing DEKRA fan zones and accommodation does not reproduce UEFA. No bridge invented.','DEKRA Table19 p43; UEFA p12'),
('fund_budget_vs_invested',7925000,7923013,'EUR','distinct_concepts','Budget/allocations and exact invested sum are separately reported; difference 1,987 EUR is not assigned to a cause.','UEFA closure Financial overview'),
('rate_product_vs_budget',316912*25,7925000,'EUR','unresolved_difference','Arithmetic product is 7,922,800, 2,200 below announced budget. No rounding rule was published.','UEFA January 2025; original contribution rule'),
('rate_product_vs_invested',316912*25,7923013,'EUR','unresolved_difference','Exact invested sum is 213 above the arithmetic contribution product.','UEFA January/July 2025'),
('fund_esg_vs_closure',8000000,7925000,'EUR','source_version_difference','ESG report is approximately/just over 8m; later closure budget 7.925m.','UEFA pp13–14; closure'),
('clubs_esg_vs_closure',227,225,'clubs','source_version_difference','ESG report and final announcement report different totals; no club-level bridge supplied.','UEFA pp13–14; January/July 2025'),
('expected_savings_july_vs_esg',60000,67000,'tonnes_carbon_emissions','source_version_difference','Lifecycle expectations, not measured annual or realised reductions.','July 2024 article; ESG p14'),
('team_air_share_table_vs_text',53.95,53.59,'percent','internal_source_discrepancy','Table18 retained for activity dataset.','DEKRA p38'),
('july_round_clubs_vs_total',80+81+30,190,'clubs','internal_source_discrepancy','Round counts sum to 191; total says 190. No hidden duplicate assumption.','UEFA July 2024 article'),
('dekra_international_travel_table_vs_text',371712,317712,'tCO2e','internal_source_discrepancy','Appendix/Table3 gives 371,712; p23 prose says 317,712. Appendix value retained.','DEKRA pp22–23,51'),
('dekra_category_sum_vs_total',sum(x[2] for x in appendix if x[-1]=='category_total'),778968,'tCO2e','source_rounding_discrepancy','Printed category totals sum to 778,967; reported grand total preserved.','DEKRA Appendix pp51–52'),
('fund_basis_vs_esg_forecast',280000,408000,'tCO2e','distinct_forecast_concepts','280,000 is minimum fund basis, 408,000 is sum of operations and travel forecasts.','UEFA January 2025; ESG p12'),
('exante_illustrative_25_arithmetic',490000*25,12000000,'EUR','source_rounding_discrepancy','Source Table6-1 reports rounded €12m, retained independently from 12.25m arithmetic.','Öko-Institut p59')]
reconciliations.append(('fan_zone_domestic_activity_table_total',307.95,307.59,'million passenger-km',
 'internal_source_discrepancy','Table16 total differs from sum of printed components by 0.36m person-km, larger than two-decimal rounding can explain. Both retained; cause not assigned.','DEKRA Table16 p37'))
write_csv('source_reconciliation.csv',[dict(check_id=a,left_value=b,right_value=c,difference_left_minus_right=round(b-c,6),unit=d,status=e,interpretation=f,source_locator=g) for a,b,c,d,e,f,g in reconciliations])

dictionary={
 'source_manifest.csv':'One row per preserved official source, with SHA-256 and provenance. PDF dates are metadata, not publication dates.',
 'headline_metrics.csv':'One row per metric and source version. Never sum across versions. Emissions are ex-post estimates; administrative counts are source reports.',
 'dekra_emissions_components.csv':'One row per appendix category/component/total. Sum category_total rows only for category comparison, not category totals plus components.',
 'dekra_restricted_boundary.csv':'One row per Table19 category plus total, with source precision, distinct from both UEFA and the full DEKRA boundary.',
 'transport_activity.csv':'One row per DEKRA transport mode, population, travel scope and table; reported_activity_million_pkm is source precision. activity_pkm is a unit conversion; missing walking/cycling values stay blank.',
 'transport_differential_factors.csv':'Published emission-factor differences for shifts to rail; negative means reduced emissions. Not absolute emission factors.',
 'factor_provenance.csv':'Source-disclosed activity and emission-factor families by category; numeric factors are not supplied or reverse-engineered.',
 'exante_expost_inputs.csv':'Long-form Table12 input comparison. Ex-post does not establish a purely observed value; surveys and estimates are mixed.',
 'timing_and_rules.csv':'One source-backed timing rule, methodological convention or grant rule per row.',
 'source_reconciliation.csv':'Discrepancies and scope/concept differences, retained rather than forced to match.'}
fields={
 'source_id':'Join key to source_manifest.csv and source_catalog.json.',
 'source_date':'Visible report cover/article date; blank when unavailable. Not a guaranteed first-publication date.',
 'event_year':'Year of EURO event, 2024, independent of source/report/announcement year.',
 'retrieved_date_utc':'Archive acquisition date, UTC. Archived bytes and hashes fix the reviewed source version.',
 'source_pdf_page':'One-based PDF physical page; printed pages coincide for the extracted tables.',
 'source_locator':'Table, section or nearby paragraph for verification.',
 'observation_status':'Distinguishes administrative reports, estimates, announced budgets, rules, hypothetical values and derived arithmetic.',
 'value_qualifier':'Source precision/qualification; no extra precision inferred.',
 'unit':'Measurement unit; EUR are nominal euros without inflation adjustment. tCO2e are metric tonnes CO2-equivalent.',
 'scope':'Accounting boundary or source-specific population. Not synonymous with GHG Protocol Scope 1/2/3.',
 'row_type':'component/category_total/grand_total or component/total. Prevents double counting.',
 'activity_pkm':'Converted passenger-km. Blank means unavailable, including source placeholder zeros accompanied by missing-data footnotes.',
 'absolute_emission_factor':'Always blank: no complete matching factor matrix disclosed in the reviewed activity tables.',
 'difference_left_minus_right':'Simple diagnostic arithmetic, not a model output or inferred causal effect.'}
fields.update({
 'absolute_factor_available':'False: an absolute mode-specific numeric factor is not supplied in this table.',
 'absolute_factor_status':'Disclosure status for the missing absolute factor; blank values must not be interpreted as zero.',
 'activity_basis':'Source description of quantities used with emission factors; not a promise that all quantities are public.',
 'activity_id':'Unique transport record identifier combining source table and mode.',
 'activity_year':'Year of activity to which the source factor/differential applies.',
 'author':'Institutional or named authors as printed in the source.',
 'bytes':'Exact byte length of the locally preserved raw source.',
 'category':'Source inventory category, translated into an English label or stable identifier.',
 'check_id':'Unique reconciliation diagnostic identifier.',
 'component_id':'Unique DEKRA appendix record identifier.',
 'emissions_tco2e':'Source-reported emissions, in metric tonnes of CO2-equivalent, retaining printed precision.',
 'extension':'Raw source file type: pdf or html.',
 'factor_id':'Unique published modal-shift differential identifier.',
 'factor_kind':'Here difference_new_minus_old, not an absolute mode factor.',
 'factor_source_family':'Source-disclosed database or institution providing emission factors.',
 'factor_unit':'Unit of the published differential, gCO2e per passenger-km.',
 'factor_value':'Signed published differential; negative means fewer emissions after the hypothetical modal shift.',
 'from_mode':'Original mode in the source modal-shift comparison.',
 'input_id':'Unique Table12 input/version identifier.',
 'interpretation':'Scope-controlled explanation of a source discrepancy or conceptual difference.',
 'item':'English description of the source inventory component.',
 'left_value':'First source value or explicitly identified arithmetic calculation in a reconciliation.',
 'metric':'Stable English identifier for the reported metric.',
 'metric_id':'Unique source-version and metric key.',
 'mode':'Stable transport-mode identifier; total marks the printed table total.',
 'notes':'Caveats, source wording differences, missingness or interpretation limits.',
 'numeric_factor_available':'False: this record identifies provenance, not a complete numeric factor mapping.',
 'pdf_creation_date':'Raw PDF /CreationDate metadata; not first-publication date.',
 'pdf_modification_date':'Raw PDF /ModDate metadata; may reveal later file versions.',
 'pdf_pages':'PDF physical page count.',
 'population':'Ticket holders, fan-zone visitors or national teams in DEKRA travel tables.',
 'raw_relative_path':'Path to preserved source bytes relative to the package root.',
 'reported_activity_million_pkm':'Direct transcription of printed distance, million passenger-km; including explicitly labelled missing-data zero placeholders.',
 'reported_factor_version':'Database edition/year stated by the report; mixed/undated if the report does not specify.',
 'reported_share_percent':'Source-printed share in percent; not recomputed from rounded rows.',
 'reported_value':'Source-backed text or date for a rule or timeline item.',
 'retrieval_time_precision':'exact when acquisition receipt has a timestamp; date_only for initial curl PDF downloads.',
 'retrieved_at_utc':'Exact timestamp where recorded by acquisition; blank when only retrieval date was preserved.',
 'right_value':'Second source value in a reconciliation.',
 'rule_id':'Unique timing/rule identifier.',
 'sha256':'SHA-256 hexadecimal checksum of the preserved bytes.',
 'source_mode_label':'Original German table label, retained for auditability.',
 'source_unit':'Unit printed in the source before any explicit conversion.',
 'source_url':'Official URL supporting the row; join to manifest for bytes and hashes.',
 'source_year':'Year attached to the source, separate from event year; blank when undated.',
 'status':'Source-acquisition or discrepancy classification, depending on dataset.',
 'title':'Official document or webpage title.',
 'to_mode':'Replacement mode in source comparison, long-distance rail.',
 'travel_scope':'International versus national travel as defined by the source table and footnotes.',
 'url':'Canonical official source URL in catalog/manifest.',
 'value':'Numeric reported or explicitly labelled derived value; interpret with unit, scope and observation_status.',
 'version':'Ex-ante or ex-post column of DEKRA Table12.',
 'version_notes':'Source-version details and dating limits.'})
dictionary_rows=[dict(dataset=k,field='*',description=v) for k,v in dictionary.items()]
for dataset in dictionary:
    columns=next(csv.reader((D/dataset).open()))
    for col in columns:
        assert col in fields, f'Undocumented column: {dataset}/{col}'
        dictionary_rows.append(dict(dataset=dataset,field=col,description=fields[col]))
write_csv('data_dictionary.csv',dictionary_rows)

# Reproducibility records reflect the actual runtime, not an unexecuted Conda claim.
packages={name:importlib.metadata.version(name) for name in ['pandas','numpy','scipy','matplotlib','pypdf','lxml','PyMuPDF']}
runtime={'recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'python_executable':sys.executable,
 'python_version':sys.version,'platform':platform.platform(),'packages':packages,
 'conda_path':shutil.which('conda'),'micromamba_path':shutil.which('micromamba'),'mamba_path':shutil.which('mamba'),
 'executed_under_conda':bool(__import__('os').environ.get('CONDA_PREFIX')),
 'pdftotext_path':shutil.which('pdftotext'), 'acquisition_and_build':'Executed in managed Python runtime; no packages installed.'}
(D/'runtime_environment.json').write_text(json.dumps(runtime,indent=2))

# Checks preserve source discrepancies; only exact identities are assertions.
assert 67955+248957==316912
assert 5825000+2100000==7925000
assert 184+20+9+12==225
assert 211+14==225 and 13+8==21
assert len({r['activity_id'] for r in activity})==len(activity)
assert all(r['source_id'] in CAT for r in metrics+components+activity+factors+inputs)
assert sum(r['activity_pkm'] is None for r in activity)==2
checks=[]
for table,(_,_,page,total,rows) in tables.items():
    checks.append(dict(check=f'table_{table}_rounded_activity_sum',reported_total=total,
       summed_components=round(sum(r[1] for r in rows),8),
       delta=round(sum(r[1] for r in rows)-total,8),unit='million passenger-km',
       status=('exact_at_printed_precision' if abs(sum(r[1] for r in rows)-total)<1e-8 else
               'unresolved_internal_source_discrepancy' if abs(sum(r[1] for r in rows)-total)>len(rows)*0.005+0.005 else
               'compatible_with_rounding'),source_page=page))
(D/'validation_report.json').write_text(json.dumps({'exact_identity_checks':'passed','activity_checks':checks,
 'source_discrepancies':'See source_reconciliation.csv. Differences are not corrected.',
 'factor_completeness':'Absolute activity-to-factor matrix not available; differential factors only.',
 'dataset_counts':{k:sum(1 for _ in csv.DictReader((D/k).open())) for k in dictionary}},indent=2))
hashes=[]
for p in sorted(D.glob('*')):
    if p.is_file() and p.name!='data_file_hashes.csv':
        hashes.append(dict(relative_path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
write_csv('data_file_hashes.csv',hashes)
print(json.dumps({'status':'built_and_validated','counts':{k:sum(1 for _ in csv.DictReader((D/k).open())) for k in dictionary}},indent=2))
