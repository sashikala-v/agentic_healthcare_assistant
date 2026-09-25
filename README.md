# Agentic Healthcare Assistant

Educational prototype using synthetic data only.

## Windows PowerShell
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python seed_data.py
streamlit run app.py
```

## Demo
1. Select patient Rajesh Kumar.
2. Enter: `Book a nephrologist appointment for my father and summarize CKD treatment information.`
3. Click Run assistant.
4. Review the plan, history, slots, RAG sources, response, and logs.
5. Select a slot and explicitly confirm booking.
