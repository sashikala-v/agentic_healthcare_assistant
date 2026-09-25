import sqlite3, json, time, re
from pathlib import Path
from rag_engine import SimpleRAG
DB=Path(__file__).parent/'healthcare.db'
def conn(): return sqlite3.connect(DB)
def log(event,payload,status,ms):
    c=conn(); c.execute('INSERT INTO audit_logs(event_type,payload,status,duration_ms) VALUES (?,?,?,?)',(event,json.dumps(payload),status,ms)); c.commit(); c.close()
def patient_data(pid):
    c=conn(); c.row_factory=sqlite3.Row
    p=c.execute('SELECT * FROM patients WHERE patient_id=?',(pid,)).fetchone(); rs=c.execute('SELECT * FROM medical_records WHERE patient_id=? ORDER BY record_date DESC',(pid,)).fetchall(); c.close()
    return (dict(p) if p else None),[dict(x) for x in rs]
def list_patients():
    c = conn(); c.row_factory = sqlite3.Row
    rows = c.execute('SELECT patient_id, name FROM patients ORDER BY patient_id').fetchall()
    c.close()
    return [dict(x) for x in rows]
def find_patient_by_name(query):
    c=conn(); c.row_factory=sqlite3.Row
    rows=c.execute('SELECT * FROM patients').fetchall(); c.close()
    q=re.sub(r'[^a-z0-9 ]',' ',query.lower())
    for row in rows:
        name=row['name'].lower()
        if name in q or all(part in q for part in name.split()): return dict(row)
    return None
def find_patient_by_id(query):
    # Explicit patient IDs in the request always take priority over the sidebar.
    match = re.search(r"\b(?:patient\s*id\s*[:#-]?\s*)?(P\d{3,})\b", query, flags=re.IGNORECASE)
    if not match:
        return None
    requested_id = match.group(1).upper()
    c = conn(); c.row_factory = sqlite3.Row
    row = c.execute("SELECT * FROM patients WHERE upper(patient_id)=?", (requested_id,)).fetchone()
    c.close()
    return dict(row) if row else {"patient_id": requested_id, "name": None}

def resolve_patient(selected_pid,q):
    by_id = find_patient_by_id(q)
    if by_id:
        if by_id.get('name') is None:
            return None, f"The requested patient ID {by_id['patient_id']} does not exist."
        notice = None if by_id['patient_id'] == selected_pid else (
            f"The request explicitly specifies {by_id['patient_id']} ({by_id['name']}); this ID overrides the sidebar selection."
        )
        return by_id['patient_id'], notice
    named=find_patient_by_name(q)
    if named and named['patient_id'] != selected_pid:
        return named['patient_id'], f"The request names {named['name']} ({named['patient_id']}), which differs from the selected patient. The named patient was used."
    return selected_pid, None
def slots():
    c=conn(); c.row_factory=sqlite3.Row
    rows=c.execute("SELECT a.*,d.name,d.specialty,d.clinic FROM appointments a JOIN doctors d ON a.doctor_id=d.doctor_id WHERE a.status='AVAILABLE' AND d.specialty='Nephrologist' ORDER BY appointment_date,appointment_time").fetchall(); c.close(); return [dict(x) for x in rows]
def book(aid):
    t=time.perf_counter(); c=conn(); cur=c.execute("UPDATE appointments SET status='BOOKED' WHERE appointment_id=? AND status='AVAILABLE'",(aid,)); c.commit(); ok=cur.rowcount==1; c.close(); log('book_slot',{'appointment_id':aid},'SUCCESS' if ok else 'FAILED',(time.perf_counter()-t)*1000); return ok
def plan(q):
    q=q.lower(); p=['Identify patient and requested tasks']
    if any(x in q for x in ['book','appointment','nephrologist']): p += ['Retrieve patient context','Find available nephrologist slots','Request explicit confirmation before booking']
    if any(x in q for x in ['ckd','treatment','summarize','information','latest']): p += ['Retrieve CKD educational documents','Generate source-grounded educational summary']
    return p+['Write audit trace and response']
def run(pid,q):
    t=time.perf_counter(); resolved_pid,notice=resolve_patient(pid,q); p,rs=patient_data(resolved_pid)
    if not p:return {'error':'Patient not found'}
    pl=plan(q); ss=slots() if any(x in q.lower() for x in ['book','appointment','nephrologist']) else []
    ans,src=SimpleRAG().answer(q) if any(x in q.lower() for x in ['ckd','treatment','summarize','information','latest']) else ('No medical search requested.',[])
    hist='\n'.join(f"- {r['record_date']}: {r['diagnosis']} — {r['treatment']}. {r['notes']}" for r in rs)
    response=(f"**Patient:** {p['name']} ({p['age']})\n\n" + (f"**Patient matching notice**\n{notice}\n\n" if notice else '') + f"**History**\n{hist}\n\n**Alert**\n{p['alert']}\n\n**Appointment options**\n" + ('\n'.join(f"- ID {s['appointment_id']}: {s['name']} — {s['appointment_date']} at {s['appointment_time']}" for s in ss) if ss else 'No slots found.') + f"\n\n**Medical information**\n{ans}\n\n**Booking status:** No booking made automatically; confirmation is required.")
    log('agent_run',{'patient_id':resolved_pid,'request':q,'plan':pl,'patient_match_notice':notice},'SUCCESS',(time.perf_counter()-t)*1000)
    return {'plan':pl,'patient':p,'records':rs,'slots':ss,'sources':src,'response':response,'patient_match_notice':notice}
def metrics():
    c=conn(); c.row_factory=sqlite3.Row; rows=[dict(x) for x in c.execute('SELECT * FROM audit_logs ORDER BY log_id DESC').fetchall()]; c.close(); total=len(rows); good=sum(x['status']=='SUCCESS' for x in rows); return rows,total,round(good/total*100,1) if total else 0

def _build_reference(pid, q):
    """Build a ground-truth reference for THIS query from live DB content.
    - If the query is about a patient's history -> reference = that patient's own records.
    - If the query is about a diagnosis/treatment -> reference = matching medical_records rows.
    Returns (category, reference_text, key_terms) or (None, None, None) if nothing to grade against.
    """
    c = conn(); c.row_factory = sqlite3.Row
    ql = q.lower()

    if any(x in ql for x in ['history', 'summarize', 'records', 'summary']):
        rs = [dict(x) for x in c.execute(
            'SELECT * FROM medical_records WHERE patient_id=? ORDER BY record_date DESC', (pid,)).fetchall()]
        p = c.execute('SELECT * FROM patients WHERE patient_id=?', (pid,)).fetchone()
        c.close()
        if not rs:
            return None, None, None
        reference = ' '.join(f"{r['diagnosis']}: {r['treatment']}. {r['notes']}" for r in rs)
        key_terms = [p['alert']] if p and p['alert'] else None
        return 'history', reference, key_terms

    if any(x in ql for x in ['treatment', 'ckd', 'information', 'latest', 'diagnosis']):
        rows = [dict(x) for x in c.execute('SELECT DISTINCT diagnosis, treatment, notes FROM medical_records').fetchall()]
        c.close()
        matched = None
        for r in rows:
            d = (r['diagnosis'] or '').lower()
            if d and (d in ql or any(w in ql for w in d.split())):
                matched = r
                break
        if not matched:
            return None, None, None
        reference = f"{matched['treatment']}. {matched['notes']}"
        key_terms = [w for w in re.findall(r'[A-Za-z]{4,}', matched['treatment'])][:4]
        return 'search', reference, key_terms

    c.close()
    return None, None, None


def _token_overlap_grade(prediction, reference, key_terms):
    pred_l = (prediction or '').lower()
    if key_terms:
        terms = [t.lower() for t in key_terms if t]
        hit = sum(t in pred_l for t in terms) / max(len(terms), 1)
        return ('CORRECT' if hit >= 0.5 else 'INCORRECT'), round(hit, 2)
    ref_tokens = set(re.findall(r'[a-z0-9]+', (reference or '').lower()))
    pred_tokens = set(re.findall(r'[a-z0-9]+', pred_l))
    overlap = len(ref_tokens & pred_tokens) / max(len(ref_tokens), 1)
    return ('CORRECT' if overlap >= 0.3 else 'INCORRECT'), round(overlap, 2)


def _llm_judge(question, prediction, reference):
    """Wire to a real LLM client when available. None -> caller falls back to offline grading."""
    return None


def evaluate_query(pid, q, response_text):
    """Grade the response the assistant just gave to THIS specific user query.
    Called right after run(), using its own output rather than a separately generated batch."""
    category, reference, key_terms = _build_reference(pid, q)
    if category is None:
        return None  # nothing in the DB to grade this query against (e.g. a booking-only request)

    judge_grade = _llm_judge(q, response_text, reference)
    if judge_grade:
        grade, score, judge = judge_grade, None, 'llm-judge'
    else:
        grade, score = _token_overlap_grade(response_text, reference, key_terms)
        judge = 'key-term/offline'

    c = conn()
    c.execute('INSERT INTO eval_results(category,patient_id,question,reference,prediction,grade,score,judge,created_at) '
              'VALUES (?,?,?,?,?,?,?,?,datetime("now"))',
              (category, pid, q, reference, response_text, grade, score, judge))
    c.commit(); c.close()
    return {'category': category, 'question': q, 'grade': grade, 'score': score, 'judge': judge}

def module_performance():
    c = conn(); c.row_factory = sqlite3.Row
    logs = [dict(x) for x in c.execute('SELECT * FROM audit_logs').fetchall()]
    evals = [dict(x) for x in c.execute('SELECT * FROM eval_results ORDER BY eval_id DESC').fetchall()]
    c.close()

    def rate(event_type):
        rows = [l for l in logs if l['event_type'] == event_type]
        return round(100 * sum(l['status'] == 'SUCCESS' for l in rows) / len(rows), 1) if rows else None

    def precision(category):
        rows = [e for e in evals if e['category'] == category]
        return round(100 * sum(e['grade'] == 'CORRECT' for e in rows) / len(rows), 1) if rows else None

    return {
        'booking_success_rate': rate('book_slot'),
        'agent_run_success_rate': rate('agent_run'),
        'history_summary_precision': precision('history'),
        'search_response_precision': precision('search'),
        'total_eval_runs': len(evals),
    }

def evaluate():
    """QAEvalChain-style evaluation: grade SimpleRAG answers against a reference eval set."""
    eval_set = json.loads((Path(__file__).parent / 'eval_set.json').read_text())
    rag = SimpleRAG()
    c = conn()
    results = []
    for item in eval_set:
        ans, _ = rag.answer(item['question'])
        judge_grade = _llm_judge(item['question'], ans, item['reference'])
        if judge_grade:
            grade, score, judge = judge_grade, None, 'llm-judge'
        else:
            grade, score, judge = *_token_overlap_grade(ans, item['reference'], item.get('key_terms')), 'key-term/offline'
        c.execute('INSERT INTO eval_results(question,reference,prediction,grade,score,judge,created_at) '
                  'VALUES (?,?,?,?,?,?,datetime("now"))',
                  (item['question'], item['reference'], ans, grade, score, judge))
        results.append({'question': item['question'], 'grade': grade, 'score': score})
    c.commit(); c.close()
    accuracy = round(100 * sum(r['grade'] == 'CORRECT' for r in results) / len(results), 1) if results else None
    return results, accuracy



