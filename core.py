import sqlite3, json, time
from pathlib import Path
DB=Path(__file__).parent/'healthcare.db'
def conn(): return sqlite3.connect(DB)
def log(event,payload,status,ms):
    c=conn(); c.execute('INSERT INTO audit_logs(event_type,payload,status,duration_ms) VALUES (?,?,?,?)',(event,json.dumps(payload),status,ms)); c.commit(); c.close()
def patient(pid):
    c=conn(); c.row_factory=sqlite3.Row
    p=c.execute('SELECT * FROM patients WHERE patient_id=?',(pid,)).fetchone(); r=c.execute('SELECT * FROM medical_records WHERE patient_id=? ORDER BY record_date DESC',(pid,)).fetchall(); c.close()
    return (dict(p) if p else None),[dict(x) for x in r]
def slots():
    c=conn(); c.row_factory=sqlite3.Row
    x=c.execute("SELECT a.*,d.name,d.specialty,d.clinic FROM appointments a JOIN doctors d ON a.doctor_id=d.doctor_id WHERE a.status='AVAILABLE' AND d.specialty='Nephrologist' ORDER BY appointment_date,appointment_time").fetchall(); c.close(); return [dict(v) for v in x]
def book(aid):
    c=conn(); x=c.execute("UPDATE appointments SET status='BOOKED' WHERE appointment_id=? AND status='AVAILABLE'",(aid,)); c.commit(); ok=x.rowcount==1; c.close(); return ok
def rag(query):
    words=set(query.lower().split()); out=[]
    for p in sorted((Path(__file__).parent/'medical_docs').glob('*.txt')):
        txt=p.read_text(encoding='utf8'); score=sum(w in txt.lower() for w in words)
        if score: out.append((score,p.name,txt))
    out.sort(reverse=True); return out[:3]
def plan(q):
    q=q.lower(); p=['Identify patient and requested tasks']
    if any(x in q for x in ['book','appointment','nephrologist']): p += ['Retrieve patient context','Find available nephrologist slots','Request explicit booking confirmation']
    if any(x in q for x in ['ckd','treatment','latest','information','disease']): p += ['Retrieve medical knowledge documents','Generate source-grounded educational summary']
    p += ['Write audit trace and response']; return p
def run(pid,q):
    t=time.perf_counter(); p,records=patient(pid); s=slots() if any(x in q.lower() for x in ['book','appointment','nephrologist']) else []; docs=rag(q) if any(x in q.lower() for x in ['ckd','treatment','latest','information','disease']) else []
    history='\n'.join(f"- {r['record_date']}: {r['diagnosis']} — {r['treatment']}. {r['notes']}" for r in records)
    med='\n\n'.join(f"**{name}**\n{txt}" for _,name,txt in docs) or 'No medical information search requested.'
    response=f"**Patient:** {p['name']} ({p['age']})\n\n**History**\n{history}\n\n**Alert**\n{p['alert']}\n\n**Available nephrologist slots**\n" + ('\n'.join(f"- ID {x['appointment_id']}: {x['name']} on {x['appointment_date']} at {x['appointment_time']}" for x in s) or 'None') + f"\n\n**Educational information**\n{med}\n\n**Booking status:** Not booked automatically; explicit confirmation is required."
    log('agent_run',{'patient_id':pid,'request':q,'plan':plan(q)},'SUCCESS',(time.perf_counter()-t)*1000)
    return {'plan':plan(q),'patient':p,'records':records,'slots':s,'docs':docs,'response':response}
def metrics():
    c=conn(); c.row_factory=sqlite3.Row; x=[dict(r) for r in c.execute('SELECT * FROM audit_logs ORDER BY log_id DESC').fetchall()]; c.close(); return x
