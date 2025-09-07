Campus Event Reporting System

Hi, this is my project for Webknot campus drive.
I am still learning coding so this is my try to make a system for colleges to create events, register students, and keep attendance.

What this project does

College can create events (like workshops, fests, hackathons).

Students can register for events.

Attendance can be marked.

Feedback can be given (1–5 stars).

Reports can be seen like most popular event, active students, etc.

How to run it (in VS Code)

Download or clone this project.

Open the folder in VS Code.

Make a virtual environment (only first time):

python -m venv venv


Activate venv:

On PowerShell:

.\venv\Scripts\Activate.ps1


If you see an error, run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass


Or on Command Prompt:

.\venv\Scripts\activate.bat


Install requirements:

pip install -r requirements.txt


Run the server:

uvicorn main:app --reload


Open this link in your browser:
http://localhost:8000/docs