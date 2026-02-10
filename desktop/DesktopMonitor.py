import sys
import requests
import pandas as pd
import tempfile
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QLineEdit, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# PDF Library
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Configuration
API_BASE = "http://127.0.0.1:8000/api"

# --- Styles ---
STYLES = """
    QMainWindow { background-color: #f0f2f5; }
    
    QFrame#LoginBox { background-color: white; border-radius: 8px; border: 1px solid #ddd; }
    QLineEdit { padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
    
    QFrame#Header { background-color: #2c3e50; }
    QLabel#HeaderTitle { color: white; font-size: 20px; font-weight: bold; }
    QPushButton#LogoutBtn { background-color: transparent; border: 1px solid white; color: white; padding: 5px 15px; border-radius: 4px; }
    QPushButton#LogoutBtn:hover { background-color: rgba(255,255,255,0.1); }

    QFrame#Card { background-color: white; border-radius: 8px; border: 1px solid #e1e4e8; }
    QLabel#CardTitle { color: #7f8c8d; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    QLabel#CardValue { color: #2c3e50; font-size: 24px; font-weight: bold; }
    
    QPushButton#PrimaryBtn { background-color: #3498db; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold; }
    QPushButton#PrimaryBtn:hover { background-color: #2980b9; }
    
    QPushButton#SuccessBtn { background-color: #27ae60; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold; }
    QPushButton#SuccessBtn:hover { background-color: #219150; }
    
    QTableWidget { border: 1px solid #ddd; background-color: white; gridline-color: #eee; }
    QHeaderView::section { background-color: #f8f9fa; padding: 8px; border: none; font-weight: bold; color: #555; }
    
    /* History Button Style */
    QPushButton#HistoryBtn {
        text-align: left;
        padding: 8px;
        background-color: white;
        border: 1px solid #eee;
        border-radius: 4px;
        color: #555;
        margin-bottom: 4px;
    }
    QPushButton#HistoryBtn:hover {
        background-color: #e3f2fd;
        border-color: #3498db;
        color: #3498db;
    }
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
        
        self.btn_action.style().unpolish(self.btn_action)
        self.btn_action.style().polish(self.btn_action)

    def handle_auth(self):
        username = self.txt_user.text()
        password = self.txt_pass.text()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both credentials")
            return
        endpoint = "register/" if self.is_registering else "login/"
        try:
            response = requests.post(f"{API_BASE}/{endpoint}", json={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                self.success_signal.emit(data['token'], data['username'])
            else:
                err = response.json().get('error', 'Auth failed')
                if isinstance(err, dict): err = str(err)
                QMessageBox.warning(self, "Error", err)
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))

class DashboardWindow(QMainWindow):
    def __init__(self, token, username):
        super().__init__()
        self.token = token
        self.username = username
        self.current_data = [] # Store data for PDF generation
        
        self.setWindowTitle("ChemVis Pro - Desktop Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(STYLES)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        h_layout.addWidget(QLabel("⚗️ ChemVis Pro", objectName="HeaderTitle"))
        h_layout.addStretch()
        h_layout.addWidget(QLabel(f"Welcome, {self.username}", styleSheet="color:white; font-weight:bold; margin-right:15px;"))
        btn_logout = QPushButton("Logout", objectName="LogoutBtn")
        btn_logout.clicked.connect(self.logout)
        h_layout.addWidget(btn_logout)
        layout.addWidget(header)
        
        # Content
        content = QHBoxLayout()
        content.setContentsMargins(20, 20, 20, 20)
        content.setSpacing(20)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        s_layout = QVBoxLayout(sidebar)
        
        # Upload
        up_card = QFrame(objectName="Card")
        up_layout = QVBoxLayout(up_card)
        up_layout.addWidget(QLabel("📂 Upload CSV", styleSheet="font-weight:bold; font-size:16px;"))
        btn_up = QPushButton("Select & Upload", objectName="SuccessBtn")
        btn_up.clicked.connect(self.upload_file)
        up_layout.addWidget(btn_up)
        s_layout.addWidget(up_card)
        
        # Download PDF Button
        pdf_card = QFrame(objectName="Card")
        pdf_layout = QVBoxLayout(pdf_card)
        pdf_layout.addWidget(QLabel("📄 Reports", styleSheet="font-weight:bold; font-size:16px;"))
        self.btn_pdf = QPushButton("Download PDF", objectName="PrimaryBtn")
        self.btn_pdf.clicked.connect(self.generate_pdf)
        self.btn_pdf.setEnabled(False) # Disabled until data loads
        pdf_layout.addWidget(self.btn_pdf)
        s_layout.addWidget(pdf_card)
        
        # History
        hist_card = QFrame(objectName="Card")
        h_layout = QVBoxLayout(hist_card)
        h_layout.addWidget(QLabel("📜 History", styleSheet="font-weight:bold; font-size:16px;"))
        
        # Container for clickable history items
        self.hist_container = QWidget()
        self.hist_layout = QVBoxLayout(self.hist_container)
        self.hist_layout.setContentsMargins(0, 5, 0, 0)
        self.hist_layout.setAlignment(Qt.AlignTop)
        
        # Scroll Area for history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.hist_container)
        scroll.setFrameShape(QFrame.NoFrame)
        h_layout.addWidget(scroll)
        
        s_layout.addWidget(hist_card)
        
        s_layout.addStretch()
        content.addWidget(sidebar)
        
        # Main Dash
        dash = QWidget()
        d_layout = QVBoxLayout(dash)
        
        # KPIs
        kpi_row = QHBoxLayout()
        self.kpi_total = self.make_kpi("Total Equipment", "-")
        self.kpi_press = self.make_kpi("Avg Pressure", "-")
        self.kpi_temp = self.make_kpi("Avg Temp", "-")
        kpi_row.addWidget(self.kpi_total)
        kpi_row.addWidget(self.kpi_press)
        kpi_row.addWidget(self.kpi_temp)
        d_layout.addLayout(kpi_row)
        
        # Charts
        chart_row = QHBoxLayout()
        # Bar
        bar_f = QFrame(objectName="Card")
        bl = QVBoxLayout(bar_f)
        bl.addWidget(QLabel("Pressure vs Temp"))
        self.cv_bar = MplCanvas(self)
        bl.addWidget(self.cv_bar)
        chart_row.addWidget(bar_f, 2)
        # Pie
        pie_f = QFrame(objectName="Card")
        pl = QVBoxLayout(pie_f)
        pl.addWidget(QLabel("Type Distribution"))
        self.cv_pie = MplCanvas(self)
        pl.addWidget(self.cv_pie)
        chart_row.addWidget(pie_f, 1)
        d_layout.addLayout(chart_row)
        
        # Table
        tbl_f = QFrame(objectName="Card")
        tl = QVBoxLayout(tbl_f)
        tl.addWidget(QLabel("Live Data Grid"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Pressure", "Temp", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tl.addWidget(self.table)
        d_layout.addWidget(tbl_f)
        
        content.addWidget(dash)
        layout.addLayout(content)
        
        # Initial Load: Refresh history on start
        self.refresh_history()

    def make_kpi(self, title, val):
        f = QFrame(objectName="Card")
        l = QVBoxLayout(f)
        l.setAlignment(Qt.AlignCenter)
        l.addWidget(QLabel(title, objectName="CardTitle"))
        l.addWidget(QLabel(val, objectName="CardValue"))
        return f

    def refresh_history(self):
        # Fetch history specific to logged-in user
        headers = {'Authorization': f'Token {self.token}'}
        
        # Clear existing buttons
        while self.hist_layout.count():
            item = self.hist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            res = requests.get(f"{API_BASE}/upload/", headers=headers)
            if res.status_code == 200:
                history = res.json().get('history', [])
                if history:
                    for h in history:
                        raw_date = h.get('uploaded_at', '').split('T')[0]
                        btn_text = f"{h.get('file_name')}\n{raw_date}"
                        
                        btn = QPushButton(btn_text)
                        btn.setObjectName("HistoryBtn")
                        # Use lambda to capture the ID
                        btn.clicked.connect(lambda checked, pk=h['id']: self.load_history_item(pk))
                        self.hist_layout.addWidget(btn)
                else:
                    self.hist_layout.addWidget(QLabel("No uploads yet."))
            else:
                self.hist_layout.addWidget(QLabel("Failed to load history."))
        except Exception as e:
            self.hist_layout.addWidget(QLabel(f"Connection error: {e}"))

    def load_history_item(self, pk):
        headers = {'Authorization': f'Token {self.token}'}
        try:
            res = requests.get(f"{API_BASE}/history/{pk}/", headers=headers)
            if res.status_code == 200:
                data = res.json()
                self.current_data = data.get('data', [])
                self.update_ui(data)
                self.btn_pdf.setEnabled(True)
            else:
                QMessageBox.warning(self, "Error", "Could not load history item")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path: return
        
        headers = {'Authorization': f'Token {self.token}'}
        try:
            with open(path, 'rb') as f:
                res = requests.post(f"{API_BASE}/upload/", files={'file': f}, headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                self.current_data = data.get('data', [])
                self.update_ui(data)
                self.btn_pdf.setEnabled(True)
                self.refresh_history() # Refresh list after upload
            else:
                QMessageBox.warning(self, "Error", f"Upload failed: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_ui(self, data):
        stats = data.get('stats', {})
        records = data.get('data', [])
        
        # KPIs
        self.kpi_total.findChild(QLabel, "CardValue").setText(str(stats.get('total_count', 0)))
        self.kpi_press.findChild(QLabel, "CardValue").setText(f"{stats.get('avg_pressure', 0)}")
        self.kpi_temp.findChild(QLabel, "CardValue").setText(f"{stats.get('avg_temp', 0)}")
        
        # Table
        self.table.setRowCount(len(records))
        for i, row in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('Equipment Name', row.get('name')))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('Type', row.get('type')))))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get('Pressure', row.get('pressure')))))
            self.table.setItem(i, 3, QTableWidgetItem(str(row.get('Temperature', row.get('temp')))))
            
            status = row.get('Status', 'UNKNOWN')
            item = QTableWidgetItem(status)
            item.setTextAlignment(Qt.AlignCenter)
            if status == 'CRITICAL':
                item.setBackground(QColor("#fadbd8"))
                item.setForeground(QColor("#c0392b"))
            elif status == 'WARNING':
                item.setBackground(QColor("#fdebd0"))
                item.setForeground(QColor("#d35400"))
            else:
                item.setBackground(QColor("#d4efdf"))
                item.setForeground(QColor("#27ae60"))
            self.table.setItem(i, 4, item)
            
        # Charts
        df = pd.DataFrame(records)
        self.cv_bar.axes.cla()
        if not df.empty:
            names = [r.get('Equipment Name', r.get('name')) for r in records]
            p = [r.get('Pressure', r.get('pressure', 0)) for r in records]
            t = [r.get('Temperature', r.get('temp', 0)) for r in records]
            x = range(len(names))
            w = 0.35
            self.cv_bar.axes.bar([i-w/2 for i in x], p, w, label='Press', color='#36A2EB')
            self.cv_bar.axes.bar([i+w/2 for i in x], t, w, label='Temp', color='#FF6384')
            self.cv_bar.axes.set_xticks(x)
            self.cv_bar.axes.set_xticklabels(names, rotation=45, ha='right')
            self.cv_bar.axes.legend()
        self.cv_bar.draw()
        
        self.cv_pie.axes.cla()
        dist = stats.get('type_distribution', {})
        if dist:
            self.cv_pie.axes.pie(dist.values(), labels=dist.keys(), autopct='%1.1f%%')
        self.cv_pie.draw()

    def generate_pdf(self):
        if not self.current_data:
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "equipment_report.pdf", "PDF Files (*.pdf)")
        if not save_path: return
        
        try:
            doc = SimpleDocTemplate(save_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            elements.append(Paragraph("Chemical Equipment Report", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Generated by: {self.username} on {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # --- 1. Save Charts as Images ---
            # Create temp files to store chart images
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_bar:
                self.cv_bar.figure.savefig(tmp_bar.name, bbox_inches='tight')
                bar_img_path = tmp_bar.name
                
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_pie:
                self.cv_pie.figure.savefig(tmp_pie.name, bbox_inches='tight')
                pie_img_path = tmp_pie.name

            # Add Images to PDF (Side by side using a Table)
            # Create Image objects from reportlab
            img_bar = Image(bar_img_path, width=250, height=200)
            img_pie = Image(pie_img_path, width=250, height=200)
            
            # Put images in a table to align them
            chart_table = Table([[img_bar, img_pie]])
            elements.append(chart_table)
            elements.append(Spacer(1, 20))

            # --- 2. Data Table ---
            data = [["Name", "Type", "Pressure", "Temp", "Status"]]
            for row in self.current_data:
                data.append([
                    str(row.get('Equipment Name', row.get('name'))),
                    str(row.get('Type', row.get('type'))),
                    str(row.get('Pressure', row.get('pressure'))),
                    str(row.get('Temperature', row.get('temp'))),
                    str(row.get('Status', 'UNKNOWN'))
                ])
                
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            # Cleanup temp files
            try:
                os.remove(bar_img_path)
                os.remove(pie_img_path)
            except:
                pass
                
            QMessageBox.information(self, "Success", f"PDF saved to {save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"PDF Generation failed: {str(e)}")

    def logout(self):
        self.close()
        self.login = LoginWindow()
        self.login.success_signal.connect(start_dashboard)
        self.login.show()

def start_dashboard(token, username):
    global window
    window = DashboardWindow(token, username)
    window.showMaximized()
    login.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    login = LoginWindow()
    login.success_signal.connect(start_dashboard)
    login.show()
    sys.exit(app.exec_())