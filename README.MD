⚗️ ChemVis Pro (Hybrid Web + Desktop App)ChemVis Pro is a full-stack data visualization and analytics tool designed for monitoring chemical equipment parameters. It features a unified Django backend that serves both a React.js Web Dashboard and a PyQt5 Desktop Application simultaneously.🚀 FeaturesHybrid Architecture: Single Django backend powering both Web and Desktop interfaces.Data Analytics: Automatic calculation of statistics (Total Count, Avg Pressure, Avg Temperature) and "Health Status" detection (Critical/Warning/OK) using Pandas.Visualizations: Interactive Bar and Pie charts (Chart.js on Web, Matplotlib on Desktop).User System: Secure Login/Registration with Token Authentication.History Management: User-specific upload history with the ability to reload past datasets.Reporting: Automated PDF report generation with embedded charts.🛠️ Tech StackLayerTechnologyPurposeBackendPython, Django REST FrameworkAPI, Auth, Data ProcessingData ProcessingPandasCSV Parsing & AnalyticsWeb FrontendReact.js, Chart.js, AxiosWeb DashboardDesktop FrontendPython, PyQt5, MatplotlibNative Desktop DashboardReportingjsPDF (Web), ReportLab (Desktop)PDF GenerationDatabaseSQLiteData Persistence📦 Installation & Setup GuidePrerequisitesPython 3.8+ installed.Node.js & npm installed.Git installed.1. Clone the Repositorygit clone [https://github.com/YOUR_USERNAME/ChemVisPro.git](https://github.com/YOUR_USERNAME/ChemVisPro.git)
cd ChemVisPro
2. Backend Setup (Django)Open a terminal window.Navigate to the backend directory:cd backend
Create and Activate Virtual Environment:Windows:python -m venv venv
..\venv\Scripts\activate
Mac/Linux:python3 -m venv venv
source ../venv/bin/activate
Install Python Dependencies:pip install django djangorestframework django-cors-headers pandas matplotlib pyqt5 requests reportlab
Run Migrations & Start Server:python manage.py makemigrations
python manage.py migrate
python manage.py runserver
✅ The backend is now running at http://127.0.0.1:8000/3. Web Frontend Setup (React)Open a new terminal window.Navigate to the web frontend directory:cd frontend-web
Install Node Modules:npm install
Start the Application:npm start
✅ The web app will open at http://localhost:3000/4. Desktop Frontend Setup (PyQt5)Open a new terminal window.Navigate to the desktop directory:cd desktop
Activate the Virtual Environment (Same as backend):Windows:..\venv\Scripts\activate
Mac/Linux:source ../venv/bin/activate
Run the Desktop App:python DesktopMonitor.py
📝 Usage InstructionsRegister/Login:Open the Web or Desktop app.Click Register to create a new account (or use admin/admin if you created a superuser).Login with your credentials.Upload Data:Click "Upload CSV".Select the provided sample_equipment_data.csv (located in the data/ folder).The dashboard will populate with charts and a data grid.View History:Your uploads are saved to your account.Click on any item in the History sidebar to reload that specific report.Generate Report:Click the "Download Report" card (Web) or button (Desktop) to download a PDF summary including charts.📂 Directory StructureChemVisPro/
├── backend/                # Django Project
│   ├── api/                # API App (Views, Models, Serializers)
│   ├── core/               # Project Settings
│   ├── media/              # Uploaded CSVs storage
│   └── db.sqlite3          # Database
├── frontend-web/           # React Application
│   ├── src/                # Components & Logic
│   └── package.json
├── desktop/                # Desktop Application
│   └── DesktopMonitor.py   # PyQt5 Entry Point
├── data/                   # Sample Data
│   └── sample_equipment_data.csv
└── README.md
