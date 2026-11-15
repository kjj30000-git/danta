import pandas as pd,numpy as np,pathlib
O=pathlib.Path('/tmp/audit');q=pd.read_pickle(O/'reps.pkl');q['mode']=q.entry_mode;q.loc[q.entry_mode.eq('PRE_HISTORY')&q.pre_entry_type.eq('FIRST_75_PASS'),'mode']='FIRST_75_PASS';q=q[q['mode'].isin(['BASE','FIRST_75_PASS','PULLBACK_BALANCE_BREAKOUT','PULLBACK_STRUCTURE_ENTRY','PULLBACK_SNAPSHOT_DIRECT','PULLBACK_SNAPSHOT_RECLAIM'])].copy();q['versiongroup']=q.folder.str.split('(').str[0];q['day']=q.entry_time.str[:10];q['entry']=pd.to_datetime(q.entry_time,format='mixed');q['exit']=pd.to_datetime(q.exit_time,format='mixed');q['entry_price']=pd.to_numeric(q.entry_price);q['net_scenario']=q.net.fillna(q.gross_return_pct-.24)
res=[];selected=[]
for (version,mode),g in q.groupby(['versiongroup','mode']):
 g=g[g.session.eq('MAIN')] if 'session' in g else g
 if mode in ['BASE','FIRST_75_PASS']:g=g[(g.entry.dt.strftime('%H:%M:%S')>='09:05:00')&(g.entry.dt.strftime('%H:%M:%S')<'09:30:00')]
 for day,h in g.groupby('day'):
  active=[];seen=set();cnt=0;cash=6000000.;pnl=0.;capitaltotal=0.
  for _,r in h.sort_values(['entry','stock_code']).iterrows():
   for a in active[:]:
    if a[0]<=r.entry:cash+=a[1]+a[2];active.remove(a)
   if cnt>=5 or len(active)>=5 or r.stock_code in seen:continue
   qty=int(1000000/r.entry_price);cap=qty*r.entry_price
   if qty<1 or cap>cash:continue
   p=cap*r.net_scenario/100;active.append((r.exit,cap,p));cash-=cap;cnt+=1;seen.add(r.stock_code);pnl+=p;capitaltotal+=cap;selected.append(dict(version=version,mode=mode,day=day,code=r.stock_code,pnl=p,capital=cap))
  res.append(dict(version=version,mode=mode,day=day,n=cnt,pnl=pnl,capital=capitaltotal))
d=pd.DataFrame(res);d.to_csv(O/'portfolio_daily_all.csv',index=False);pd.DataFrame(selected).to_csv(O/'portfolio_selected_all.csv',index=False)
print(d[d.version.isin(['2.3.3','2.3.4'])].groupby(['version','mode']).agg(n=('n','sum'),pnl=('pnl','sum'),days=('day','nunique')).to_string())
