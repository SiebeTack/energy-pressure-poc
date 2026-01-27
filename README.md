ENERGY PRESSURE POC
Analyse en voorspelling van elektriciteitsverbruik als indicator voor energiedruk


BESCHRIJVING
------------
Dit project is een backend-gedreven proof-of-concept ontwikkeld in het kader van
de graduaatsproef Graduaat in het Programmeren aan HoGent.

De applicatie analyseert historisch elektriciteitsverbruik en maakt eenvoudige
voorspellingen om potentiële energiedruk te visualiseren.
De focus ligt op software-architectuur, data-pipeline, schaalbaarheid en ML,
niet op exacte operationele voorspellingen.


ARCHITECTUUR
------------
Backend        : FastAPI (Python)
Data processing: Pandas, NumPy
Machine learning: scikit-learn
Database       : SQLite
Dashboard      : Streamlit

Projectstructuur:
energy-pressure-poc/
- backend/        FastAPI backend + ML + database
- dashboard/      Streamlit dashboard
- requirements.txt
- README.txt


VEREISTEN
---------
- Python 3.10 of 3.11
- Git
- Windows / macOS / Linux

Controleer Python:
python --version


INSTALLATIE
-----------
1) Repository clonen
git clone https://github.com/SiebeTack/energy-pressure-poc.git
cd energy-pressure-poc


2) Virtuele omgeving aanmaken
python -m venv .venv

Activeren:

Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

macOS / Linux:
source .venv/bin/activate


3) Dependencies installeren
pip install --upgrade pip
pip install -r requirements.txt


BACKEND STARTEN (FASTAPI)
------------------------
Vanuit de project root:

python -m uvicorn app.main:app --reload --app-dir backend

Backend draait op:
http://127.0.0.1:8000

Swagger API-documentatie:
http://127.0.0.1:8000/docs


DATA INGESTEN (EENMALIG)
-----------------------
Via Swagger (/docs):

POST /ingest/fake-hourly-cities
Klik op Execute

Dit genereert:
- 10 jaar uurlijkse data
- 50 Belgische steden
- ±4,3 miljoen records

De SQLite database wordt automatisch aangemaakt.


DASHBOARD STARTEN (STREAMLIT)
-----------------------------
Gebruik een tweede terminal en activeer opnieuw de venv.

streamlit run dashboard/app.py

Dashboard:
http://localhost:8501


FUNCTIONALITEITEN
-----------------
- Historisch elektriciteitsverbruik per stad
- Maandelijkse trendanalyse
- Uurlijkse ML-voorspelling (volgende 24 uur)
- Visualisatie van pieken en seizoenspatronen
- MAE-evaluatie van ML-modellen


MACHINE LEARNING (KORT)
----------------------
Model:
- HistGradientBoostingRegressor

Features:
- Lag-features (1h, 24h, 168h)
- Rolling statistics
- Tijd- en seizoensfeatures (sin/cos)

Evaluatie:
- Time-based split
- MAE (Mean Absolute Error)

Forecasting:
- Recursive forecasting (uur per uur vooruit)

De voorspellingen dienen als indicator en niet als exacte netcapaciteitsberekening.


VEELVOORKOMENDE PROBLEMEN
------------------------
Uvicorn niet gevonden:
pip install uvicorn

PowerShell execution policy error:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

Dashboard vindt backend niet:
Controleer in dashboard/app.py:
API = "http://127.0.0.1:8000"


DISCLAIMER
----------
Dit project is een proof-of-concept voor educatieve doeleinden.
De gebruikte data is synthetisch en de voorspellingen zijn indicatief.


AUTEUR
------
Siebe Tack
Graduaat Programmeren – HoGent
GitHub: https://github.com/<jouw-username>
