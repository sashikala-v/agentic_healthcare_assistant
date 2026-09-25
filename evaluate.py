from assistant_core import run
cases=[('P001','Book a nephrologist appointment and summarize CKD treatment.'),('P001',"Show my father's medical history.")]
passed=0
for pid,q in cases:
    r=run(pid,q); ok=bool(r.get('plan'))
    print('PASS' if ok else 'FAIL',q); passed+=ok
print(f'Evaluation result: {passed}/{len(cases)} cases passed')
