For setup:
1. Open Anaconda Prompt.
2. Run: 
conda create -n freshops python=3.11 -y
conda activate freshops
cd "C:\Users\Akash S\Documents\Data Science Learnings\FreshOps"
pip install -r requirements.txt
streamlit run app.py

3. Use this same conda activate freshops whenever you work on FreshOps.

For killing:
1. Open a new Prompt terminal.
2. netstat -ano | findstr :8501
3. You’ll see something like:
TCP 0.0.0.0:8501 0.0.0.0:0 LISTENING 34184 
TCP [::]:8501 [::]:0 LISTENING 34184 
TCP [::1]:8501 [::1]:53512 ESTABLISHED 34184 
TCP [::1]:8501 [::1]:55383 ESTABLISHED 34184 
TCP [::1]:53512 [::1]:8501 ESTABLISHED 15256 
TCP [::1]:55383 [::1]:8501 ESTABLISHED 15256 
TCP [::1]:55955 [::1]:8501 TIME_WAIT 0
4. taskkill /PID 34184  /F
5. deactivate
6. deactivate.