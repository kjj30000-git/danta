import pandas as pd,json,numpy as np,pathlib,sqlite3,collections
P=pathlib.Path('REPO_ROOT_PLACEHOLDER/data/2.3.4(261109~261113)');o=pathlib.Path('/tmp/audit');o.mkdir(exist_ok=True)
d=pd.read_csv(P/'opening_events_v234.csv',dtype=str,keep_default_na=False);d['j']=d.details.map(json.loads)
f=d[d.event=='FILL'].copy();x=d[d.event=='EXIT'].copy();q=f.merge(x,on=['candidate_id','policy'],suffixes=('_f','_x'),validate='one_to_one');q['entry']=pd.to_datetime(q.at_f,format='mixed');q['exit']=pd.to_datetime(q.at_x,format='mixed');q['day']=q.entry.dt.strftime('%Y-%m-%d');q['net']=q.j_x.map(lambda j:j.get('net_pct'));q['gross']=q.j_x.map(lambda j:j.get('gross_pct'));q['price']=q.j_f.map(lambda j:j['price']);q['exitprice']=q.j_x.map(lambda j:j.get('price'));q['code']=q.stock_code_f
names=d[d.event=='CANDIDATE'].set_index('candidate_id').j.map(lambda j:j['name']);q['name']=q.candidate_id.map(names);q['rs']=q.j_f.map(lambda j:j['signal'].get('market',{}).get('relative_strength_pp'));q['lag']=q.apply(lambda r:(r.entry-pd.Timestamp(r.j_f['signal'].get('detected',r.j_f['signal'].get('at')))).total_seconds(),axis=1)
def stat(g):
 n=g.net.dropna();return {'n':len(g),'days':g.day.nunique(),'symbols':g.code.nunique(),'mean_net':n.mean(),'gross':g.gross.mean(),'pf':n[n>0].sum()/-n[n<0].sum(),'win':(n>0).mean()*100,'missing':g.net.isna().sum()}
print('OPEN',q.groupby('policy').apply(stat).to_string());print('DAILY',q.groupby(['policy','day']).net.agg(['size','mean','sum']).to_string());print('RS missing',q.groupby('policy').rs.apply(lambda s:s.isna().sum()));print('lag',q.groupby('policy').lag.describe().to_string())
print('OPEN symbols',q[q.policy=='OPENING_FIRST_PULLBACK'][['name','code']].drop_duplicates().to_string(index=False))
# strict 5 trades/day, 5 concurrent, 1m per stock, 6m equity, unique stock/day; time ordering
rows=[];chosen=[]
for mode,g in q.groupby('policy'):
 for day,h in g.groupby('day'):
  active=[];seen=set();count=0;cash=6000000.;pnl=0.;
  for ix,r in h.sort_values(['entry','code']).iterrows():
   for a in active[:]:
    if a['exit']<=r.entry:cash+=a['capital']+a['pnl'];active.remove(a)
   if count>=5 or len(active)>=5 or r.code in seen:continue
   if pd.isna(r.net):continue
   qty=int(1000000/r.price);capital=qty*r.price
   if qty<1 or capital>cash:continue
   netp=capital*r.net/100;cash-=capital;active.append({'exit':r.exit,'capital':capital,'pnl':netp});seen.add(r.code);count+=1;pnl+=netp;chosen.append({**r.to_dict(),'capital':capital,'pnl_won':netp})
  rows.append({'policy':mode,'day':day,'entries':count,'net_won':pnl,'return_on_6m_pct':pnl/6000000*100})
s=pd.DataFrame(rows);s.to_csv(o/'opening_portfolio_daily.csv',index=False);pd.DataFrame(chosen).drop(columns=['j_f','j_x']).to_csv(o/'opening_selected.csv',index=False);q.drop(columns=['j_f','j_x']).to_csv(o/'opening_trades.csv',index=False)
print('PORTFOLIO',s.to_string(index=False));print('sum',s.groupby('policy').agg({'entries':'sum','net_won':'sum','return_on_6m_pct':'sum'}).to_string())
for mode,g in q.groupby('policy'):
 daily=g.groupby('day').net.agg(['sum','size']);rng=np.random.default_rng(261115);a=daily.to_numpy();b=a[rng.integers(0,len(a),(10000,len(a)))];v=b[:,:,0].sum(1)/b[:,:,1].sum(1);print('CI',mode,np.quantile(v,[.025,.975]),'dropbestday',g[~g.day.eq(daily['sum'].idxmax())].net.mean())
print('events dup',d.event_id.duplicated().sum(),'candidates',len(names),'firsttick',sum(d.event=='OBSERVATION_START'))
print('BAR invalid',d[d.event=='BAR'].j.map(lambda j:j['valid']).value_counts().to_dict())
print('exitstatus',x.groupby('policy').j.apply(lambda s:dict(collections.Counter(j['status'] for j in s))).to_string())
con=sqlite3.connect('file:'+str(P/'opening_state_v234.sqlite3')+'?mode=ro',uri=True);print('DB',con.execute('pragma quick_check').fetchall());print('tables',con.execute("select name from sqlite_master where type='table'").fetchall())
