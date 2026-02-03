import sys
import requests
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QLineEdit, QFrame, QScrollArea, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Configuration
API_BASE = "http://127.0.0.1:8000/api"

# --- Styles (Mimicking the React App.css) ---
STYLES = """
    QMainWindow { background-color: #f0f2f5; }
    
    /* Login Box */
    QFrame#LoginBox { background-color: white; border-radius: 8px; border: 1px solid #ddd; }
    QLineEdit { padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
    
    /* Header */
    QFrame#Header { background-color: #2c3e50; }
    QLabel#HeaderTitle { color: white; font-size: 20px; font-weight: bold; }
    QPushButton#LogoutBtn { background-color: transparent; border: 1px solid white; color: white; padding: 5px 15px; border-radius: 4px; }
    QPushButton#LogoutBtn:hover { background-color: rgba(255,255,255,0.1); }

    /* Cards */
    QFrame#Card { background-color: white; border-radius: 8px; border: 1px solid #e1e4e8; }
    QLabel#CardTitle { color: #7f8c8d; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    QLabel#CardValue { color: #2c3e50; font-size: 24px; font-weight: bold; }
    
    /* Buttons */
    QPushButton#PrimaryBtn { background-color: #3498db; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold; }
    QPushButton#PrimaryBtn:hover { background-color: #2980b9; }
    QPushButton#SuccessBtn { background-color: #27ae60; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold; }
    QPushButton#SuccessBtn:hover { background-color: #219150; }
    
    /* Table */
    QTableWidget { border: 1px solid #ddd; background-color: white; gridline-color: #eee; }
    QHeaderView::section { background-color: #f8f9fa; padding: 8px; border: none; font-weight: bold; color: #555; }
"""

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.fig.tight_layout()

class LoginWindow(QWidget):
    success_signal = pyqtSignal(str, str) # token, username

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChemVis Pro - Login")
        self.setGeometry(300, 300, 400, 500)
        self.setStyleSheet(STYLES)
        self.is_registering = False
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Login Box Container
        container = QFrame()
        container.setObjectName("LoginBox")
        container.setFixedSize(350, 400)
        box_layout = QVBoxLayout(container)
        box_layout.setSpacing(15)
        box_layout.setContentsMargins(30, 30, 30, 30)
        
        self.lbl_title = QLabel("ChemVis Pro Login")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        box_layout.addWidget(self.lbl_title)
        
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Username")
        box_layout.addWidget(self.txt_user)
        
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Password")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        box_layout.addWidget(self.txt_pass)
        
        self.btn_action = QPushButton("Login")
        self.btn_action.setObjectName("PrimaryBtn")
        self.btn_action.clicked.connect(self.handle_auth)
        box_layout.addWidget(self.btn_action)
        
        self.btn_toggle = QPushButton("Don't have an account? Register here")
        self.btn_toggle.setFlat(True)
        self.btn_toggle.setStyleSheet("color: #3498db; font-weight: bold; text-align: center;")
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_mode)
        box_layout.addWidget(self.btn_toggle)
        
        box_layout.addStretch()
        layout.addWidget(container)

    def toggle_mode(self):
        self.is_registering = not self.is_registering
        if self.is_registering:
            self.lbl_title.setText("Create Account")
            self.btn_action.setText("Register")
            self.btn_action.setObjectName("SuccessBtn")
            self.btn_toggle.setText("Already have an account? Login here")
        else:
            self.lbl_title.setText("ChemVis Pro Login")
            self.btn_action.setText("Login")
            self.btn_action.setObjectName("PrimaryBtn")
            self.btn_toggle.setText("Don't have an account? Register here")
        
        # Force style refresh
        self.btn_action.style().unpolish(self.btn_action)
        self.btn_action.style().polish(self.btn_action)

    def handle_auth(self):
        username = self.txt_user.text()
        password = self.txt_pass.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return
            
        endpoint = "register/" if self.is_registering else "login/"
        url = f"{API_BASE}/{endpoint}"
        
        try:
            response = requests.post(url, json={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.success_signal.emit(data['token'], data['username'])
            else:
                try:
                    err_msg = response.json().get('error', 'Authentication failed')
                except:
                    err_msg = "Authentication failed"
                QMessageBox.warning(self, "Error", str(err_msg))
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to server.\n{str(e)}")

class DashboardWindow(QMainWindow):
    def __init__(self, token, username):
        super().__init__()
        self.token = token
        self.username = username
        self.setWindowTitle("ChemVis Pro - Desktop Dashboard")
        self.setGeometry(100, 100, 1400, 900) # Updated initial size
        self.setStyleSheet(STYLES)
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 1. Header ---
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("⚗️ ChemVis Pro")
        title.setObjectName("HeaderTitle")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        user_lbl = QLabel(f"Welcome, {self.username}")
        user_lbl.setStyleSheet("color: white; font-weight: bold; margin-right: 15px;")
        header_layout.addWidget(user_lbl)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("LogoutBtn")
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        
        main_layout.addWidget(header)
        
        # --- 2. Content Area (Splitter for Sidebar/Main) ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Sidebar (Controls)
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(20)
        
        # Upload Card
        upload_card = QFrame()
        upload_card.setObjectName("Card")
        uc_layout = QVBoxLayout(upload_card)
        uc_lbl = QLabel("📂 Upload CSV")
        uc_lbl.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.btn_upload = QPushButton("Select & Upload")
        self.btn_upload.setObjectName("SuccessBtn")
        self.btn_upload.clicked.connect(self.upload_file)
        uc_layout.addWidget(uc_lbl)
        uc_layout.addWidget(self.btn_upload)
        sidebar_layout.addWidget(upload_card)
        
        # History Card
        history_card = QFrame()
        history_card.setObjectName("Card")
        hc_layout = QVBoxLayout(history_card)
        hc_lbl = QLabel("📜 History")
        hc_lbl.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.history_list = QLabel("Loading...")
        self.history_list.setStyleSheet("color: #666; font-size: 13px;")
        self.history_list.setWordWrap(True)
        self.history_list.setAlignment(Qt.AlignTop)
        hc_layout.addWidget(hc_lbl)
        hc_layout.addWidget(self.history_list)
        hc_layout.addStretch()
        sidebar_layout.addWidget(history_card)
        
        sidebar_layout.addStretch()
        content_layout.addWidget(sidebar)
        
        # Dashboard Content
        dashboard = QWidget()
        dash_layout = QVBoxLayout(dashboard)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(20)
        
        # KPI Row
        kpi_row = QHBoxLayout()
        self.card_total = self.create_kpi_card("Total Equipment", "-")
        self.card_pressure = self.create_kpi_card("Avg Pressure", "-")
        self.card_temp = self.create_kpi_card("Avg Temp", "-")
        kpi_row.addWidget(self.card_total)
        kpi_row.addWidget(self.card_pressure)
        kpi_row.addWidget(self.card_temp)
        dash_layout.addLayout(kpi_row)
        
        # Charts Row
        charts_row = QHBoxLayout()
        # Bar Chart Frame
        bar_frame = QFrame()
        bar_frame.setObjectName("Card")
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.addWidget(QLabel("Pressure vs Temperature"))
        self.canvas_bar = MplCanvas(self, width=5, height=4, dpi=100)
        bar_layout.addWidget(self.canvas_bar)
        charts_row.addWidget(bar_frame, 2)
        
        # Pie Chart Frame
        pie_frame = QFrame()
        pie_frame.setObjectName("Card")
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.addWidget(QLabel("Type Distribution"))
        self.canvas_pie = MplCanvas(self, width=5, height=4, dpi=100)
        pie_layout.addWidget(self.canvas_pie)
        charts_row.addWidget(pie_frame, 1)
        
        dash_layout.addLayout(charts_row)
        
        # Table Section
        table_frame = QFrame()
        table_frame.setObjectName("Card")
        table_layout = QVBoxLayout(table_frame)
        table_layout.addWidget(QLabel("Live Data Grid"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Pressure", "Temp", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        table_layout.addWidget(self.table)
        
        dash_layout.addWidget(table_frame)
        
        content_layout.addWidget(dashboard)
        main_layout.addLayout(content_layout)

        # Trigger initial fetch
        self.fetch_initial_data()

    def fetch_initial_data(self):
        # Attempt to fetch history/latest data on login
        # This assumes your Django view supports GET, or we rely on the user to upload
        try:
            response = requests.get(f"{API_BASE}/upload/")
            if response.status_code == 200:
                data = response.json()
                self.update_ui(data)
            else:
                self.history_list.setText("No history found.\nUpload a file to start.")
        except:
            self.history_list.setText("Could not fetch history.\nUpload a file to start.")

    def create_kpi_card(self, title, value):
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")
        lbl_val = QLabel(value)
        lbl_val.setObjectName("CardValue")
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return frame

    def logout(self):
        self.close()
        # Restart App essentially by showing login again
        self.login_window = LoginWindow()
        self.login_window.success_signal.connect(start_dashboard)
        self.login_window.show()

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        
        try:
            with open(file_path, 'rb') as f:
                # Include token if your API needs it, though we set permission to AllowAny in views currently
                response = requests.post(
                    f"{API_BASE}/upload/", 
                    files={'file': f}
                )
            
            if response.status_code == 200:
                data = response.json()
                self.update_ui(data)
            else:
                QMessageBox.warning(self, "Upload Failed", f"Server Error: {response.status_code}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")

    def update_ui(self, data):
        stats = data.get('stats', {})
        records = data.get('data', [])
        history = data.get('history', [])
        
        # 1. Update KPIs
        if stats:
            self.card_total.findChild(QLabel, "CardValue").setText(str(stats.get('total_count', 0)))
            self.card_pressure.findChild(QLabel, "CardValue").setText(f"{stats.get('avg_pressure', 0)} psi")
            self.card_temp.findChild(QLabel, "CardValue").setText(f"{stats.get('avg_temp', 0)} °C")
        
        # 2. Update History
        if history:
            hist_text = ""
            for h in history:
                hist_text += f"• {h.get('file_name', 'Unknown')}\n"
            self.history_list.setText(hist_text)
        else:
            self.history_list.setText("No uploads yet")
        
        # 3. Update Table
        self.table.setRowCount(len(records))
        for i, row in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('Equipment Name', row.get('name', '')))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('Type', row.get('type', '')))))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get('Pressure', row.get('pressure', 0)))))
            self.table.setItem(i, 3, QTableWidgetItem(str(row.get('Temperature', row.get('temp', 0)))))
            
            status = row.get('Status', 'OK')
            item = QTableWidgetItem(status)
            item.setTextAlignment(Qt.AlignCenter)
            if status == 'CRITICAL':
                item.setBackground(QColor("#fadbd8")) # Light red
                item.setForeground(QColor("#c0392b")) # Dark red text
            elif status == 'WARNING':
                item.setBackground(QColor("#fdebd0"))
                item.setForeground(QColor("#d35400"))
            else:
                item.setBackground(QColor("#d4efdf"))
                item.setForeground(QColor("#27ae60"))
            self.table.setItem(i, 4, item)
            
        # 4. Update Charts
        self.update_charts(records, stats)

    def update_charts(self, records, stats):
        df = pd.DataFrame(records)
        
        # Bar Chart
        self.canvas_bar.axes.cla()
        if not df.empty:
            names = [r.get('Equipment Name', r.get('name')) for r in records]
            pressures = [r.get('Pressure', r.get('pressure', 0)) for r in records]
            temps = [r.get('Temperature', r.get('temp', 0)) for r in records]
            
            x = range(len(names))
            width = 0.35
            self.canvas_bar.axes.bar([i - width/2 for i in x], pressures, width, label='Pressure', color='#36A2EB', alpha=0.7)
            self.canvas_bar.axes.bar([i + width/2 for i in x], temps, width, label='Temp', color='#FF6384', alpha=0.7)
            
            self.canvas_bar.axes.set_xticks(x)
            self.canvas_bar.axes.set_xticklabels(names, rotation=45, ha='right')
            self.canvas_bar.axes.legend()
        self.canvas_bar.draw()

        # Pie Chart
        self.canvas_pie.axes.cla()
        dist = stats.get('type_distribution', {}) if stats else {}
        if dist:
            labels = list(dist.keys())
            values = list(dist.values())
            colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
            self.canvas_pie.axes.pie(values, labels=labels, autopct='%1.1f%%', colors=colors[:len(labels)])
        self.canvas_pie.draw()

# --- Main Bootstrapper ---
def start_dashboard(token, username):
    global window
    window = DashboardWindow(token, username)
    window.showMaximized() # Launch maximized for similar feel to web app
    login.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    login = LoginWindow()
    login.success_signal.connect(start_dashboard)
    login.show()
    
    sys.exit(app.exec_())