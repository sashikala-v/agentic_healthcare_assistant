import streamlit as st
import pandas as pd
from assistant_core import run,book,patient_data,metrics,list_patients,evaluate_query,module_performance
 # run once, then comment out the DROP TABLE line inside it
st.set_page_config(page_title='Agentic Healthcare Assistant',page_icon='🏥',layout='wide')
st.title('🏥 Agentic Healthcare Assistant')
st.caption('Educational capstone prototype • Synthetic data only • Not medical advice')

patients=list_patients()
labels={f"{p['patient_id']} - {p['name']}":p['patient_id'] for p in patients}
selected_label=st.sidebar.selectbox('Select patient',list(labels.keys()))
pid=labels[selected_label]

p,_=patient_data(pid)
if p: st.sidebar.write(f"**{p['name']}**, age {p['age']}"); st.sidebar.warning(p['alert'])
q=st.text_area('User request','Book a nephrologist appointment for my father and summarize CKD treatment information.')

if st.button('▶ Run assistant',type='primary'): 
    result = run(pid,q)
    st.session_state.result=result
    if 'error' not in result:
        st.session_state.last_eval = evaluate_query(pid, q, result['response'])
r=st.session_state.get('result')
if r:
    if 'error' in r: st.error(r['error'])
    else:
        st.subheader('1. Agent plan')
        for i,x in enumerate(r['plan'],1): st.write(f'{i}. {x}')
        st.subheader('2. Patient history'); st.dataframe(pd.DataFrame(r['records']),width='stretch')
        st.subheader('3. Appointment options')
        if r['slots']:
            st.dataframe(pd.DataFrame(r['slots']),width='stretch')
            aid=st.selectbox('Choose appointment ID',[x['appointment_id'] for x in r['slots']])
            st.warning('Booking requires explicit confirmation.')
            if st.button('✅ Confirm booking'):
                if book(aid): st.success(f'Appointment {aid} booked.'); st.rerun()
                else: st.error('Booking failed or slot unavailable.')
        st.subheader('4. RAG sources')
        for s in r['sources']:
            with st.expander(f"{s['title']} — score {s['score']}"): st.code(s['source']); st.write(s['text'])
        st.subheader('5. Assistant response'); st.markdown(r['response'])

        st.subheader('6. Response evaluation')
        ev = st.session_state.get('last_eval')
        if ev is None:
            st.info('This query had nothing in the database to grade against (e.g. a booking-only request).')
        else:
            c1, c2 = st.columns(2)
            c1.metric('Grade', ev['grade'])
            c2.metric('Score', ev['score'] if ev['score'] is not None else 'n/a')
            st.caption(f"Evaluated as **{ev['category']}** using **{ev['judge']}** grading.")

        st.divider(); st.subheader('7. Monitoring')
        logs,total,rate=metrics(); st.write(f'Logged events: **{total}** | Success rate: **{rate}%**')
        if logs: st.dataframe(pd.DataFrame(logs),width='stretch')

        st.subheader('8. Performance by module')
        perf = module_performance()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Booking success rate', f"{perf['booking_success_rate']}%" if perf['booking_success_rate'] is not None else 'n/a')
        c2.metric('Agent run success rate', f"{perf['agent_run_success_rate']}%" if perf['agent_run_success_rate'] is not None else 'n/a')
        c3.metric('History precision', f"{perf['history_summary_precision']}%" if perf['history_summary_precision'] is not None else 'n/a')
        c4.metric('Search precision', f"{perf['search_response_precision']}%" if perf['search_response_precision'] is not None else 'n/a')
        st.caption(f"Based on {perf['total_eval_runs']} evaluated query(ies) so far.")