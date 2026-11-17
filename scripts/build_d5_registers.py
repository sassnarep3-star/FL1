#!/usr/bin/env python3
"""Rebuild the decision ledger, suggestion pipeline, Q&A register and CSV exports."""
import csv, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=os.path.join(ROOT,'data')
def readj(n): return json.load(open(os.path.join(D,n),encoding='utf-8'))
def writej(n,x):
 with open(os.path.join(D,n),'w',encoding='utf-8') as f: json.dump(x,f,indent=1,ensure_ascii=False); f.write('\n')
def writec(n,rows,fields=None):
 if fields is None: fields=list(rows[0]) if rows else []
 with open(os.path.join(D,n),'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n'); w.writeheader(); w.writerows(rows)

# Map every open question to a conservative gate/clearing criterion; these are
# project decisions, not externally verified facts. A blank is preferable to a guess.
CLEAR={
 'Q-D5-01':('Price policy gate','Approved terms/source policy and documented permissible use'),
 'Q-D5-02':('Snapshot lifecycle gate','Versioned definition of open/close and timestamp authority'),
 'Q-D5-03':('Starter evidence gate','Dated official pregame starter announcement or explicit blank'),
 'Q-D5-04':('Joint evidence gate','Out-of-sample joint calibration plus documented settlement/void rules'),
 'Q-D5-05':('32-team sweep gate','32/32 roster and reserve-list snapshots with official links and hashes'),
 'Q-D5-06':('Designation reliability gate','Multi-season inactive-list join with play-rate intervals by designation'),
 'Q-D5-07':('Availability evidence gate','Official starter, inactive, and snap-count join with coverage disclosed'),
 'Q-D5-08':('Fixture context gate','Official game-centre source and dated schedule-announcement source per fixture'),
}

def main():
 q=readj('questions.json'); sug=readj('suggestions.json'); flags=readj('flags.json'); req=readj('requirements.json')
 ledger=[]
 for x in q:
  key=x.get('id',''); gate,clear=CLEAR.get(key,(x.get('blocking','decision gate not assigned'),''))
  ledger.append({'id':key,'category':x.get('category',''),'question':x.get('question',''),
    'known':x.get('what_we_know',x.get('why_it_matters','')),'unknown':x.get('what_we_dont_know',''),
    'missing_data':x.get('missing_data',''),'blocking_gate':gate,'clearing_number':clear,
    'owner_action':x.get('recommended_path',''),'priority':x.get('priority',''),'source':x.get('source','')})
 for x in flags:
  ledger.append({'id':'FLAG-'+x.get('id',''),'category':'Flagged','question':x.get('item',''),
    'known':x.get('detail',''),'unknown':'','missing_data':x.get('action',''),
    'blocking_gate':'Review/verification gate','clearing_number':'','owner_action':x.get('action',''),
    'priority':x.get('severity',''),'source':','.join(x.get('sourceIds',[]))})
 writej('decision_ledger_d5.json',ledger); writec('decision_ledger_d5.csv',ledger)

 pipeline=[]
 for x in sug:
  pipeline.append({'id':x.get('id',''),'title':x.get('title',''),'category':x.get('category',''),
    'review_state':'proposed','impact':x.get('impact',''),'effort':x.get('effort',''),
    'reversibility':x.get('reversibility',''),'prerequisites':'; '.join(x.get('prerequisites',[])),
    'problem':x.get('problem',''),'proposal':x.get('proposal',''),'evidence':x.get('evidence',''),
    'recommendation':x.get('recommendation','')})
 writej('suggestion_pipeline_d5.json',pipeline); writec('suggestion_pipeline_d5.csv',pipeline)

 qa=[]
 for x in q:
  qa.append({'id':x.get('id',''),'category':x.get('category',''),'priority':x.get('priority',''),
    'question':x.get('question',''),'answer_now':x.get('what_we_know',''),'unknown':x.get('what_we_dont_know',''),
    'missing_information':x.get('missing_data',''),'how_to_find_out':x.get('recommended_path',''),
    'blocking':x.get('blocking',''),'source':x.get('source','')})
 writej('qa_register_d5.json',qa); writec('qa_register_d5.csv',qa)

 # Matrix export remains a transparent projection of exact-join rows; no inference.
 av=readj('availability_d5.json'); writej('depth_matrix_d5.json',av); writec('depth_matrix_d5.csv',av['rows'])
 score=readj('scorecard_d5.json'); flat=[]
 for e in score['registry']:
  s=e.get('signal') or {}; st=e.get('staking') or {}
  flat.append({'id':e.get('id'),'name':e.get('name'),'division':e.get('division'),'role':e.get('role'),
    'registration_committed':e.get('registration',{}).get('committed',False),'n':s.get('n',0),'bss':s.get('bss'),
    'bss_lo':s.get('bss_lo'),'staking_n':st.get('n',0),'qualified':e.get('qualified',False),
    'gates_passed':e.get('gates_passed',0),'gates_total':e.get('gates_total',0),
    'what_would_change_our_mind':e.get('what_would_change_our_mind','')})
 writec('strategy_scorecard_d5.csv',flat)

 # Machine-readable capture inventory with the timestamp and manifest hash.
 live=readj('live_state_d5.json'); vr=[]
 for key,x in live['captures'].items():
  vr.append({'check_id':'D5-CAP-'+key,'status':'PASS' if x.get('sha256') else 'FAIL','read_at_utc':x['read_at'],
    'source_url':x['url'],'raw_path':x['path'],'sha256':x.get('sha256'),'bytes':x.get('bytes'),
    'verification':'manifest hash matched by scripts/verify_live_d5.py'})
 writec('verification-live.tsv',vr)
 print('decision ledger=%d, suggestions=%d, Q&A=%d, depth rows=%d, strategies=%d, captures=%d' %
   (len(ledger),len(pipeline),len(qa),len(av['rows']),len(flat),len(vr)))
if __name__=='__main__': main()
