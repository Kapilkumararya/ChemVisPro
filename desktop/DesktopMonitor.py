import sys
import requests
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Configuration
API_URL = "http://127.0.0.1:8000/api/upload/" 

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.axes = plt.subplots(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)

class EquipmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Monitor (Desktop)")
        self.setGeometry(100, 100, 1000, 700)
        
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # Controls
        btn_upload = QPushButton("Upload CSV to Backend")
        btn_upload.clicked.connect(self.upload_file)
        btn_upload.setStyleSheet("padding: 10px; background: #007bff; color: white; font-weight: bold;")
        layout.addWidget(btn_upload)
        
        self.lbl_status = QLabel("Status: Ready")
        layout.addWidget(self.lbl_status)

        # Chart
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Pressure", "Temperature", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not file_path: return
        
        self.lbl_status.setText(f"Uploading {file_path}...")
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(API_URL, files={'file': f})
            
            if response.status_code == 200:
                data = response.json()
                self.update_ui(data['data'])
                self.lbl_status.setText("Status: Success")
            else:
                self.lbl_status.setText(f"Error: {response.status_code}")
                # Fallback for demo if server is down
                self.local_fallback(file_path)

        except Exception as e:
            self.lbl_status.setText(f"Connection Error. Using Local Fallback.")
            self.local_fallback(file_path)

    def local_fallback(self, file_path):
        df = pd.read_csv(file_path)
        if 'Pressure' in df and 'Temperature' in df:
            df['Status'] = df.apply(lambda r: 'CRITICAL' if r['Pressure'] > 800 and r['Temperature'] > 300 else 'OK', axis=1)
        self.update_ui(df.to_dict(orient='records'))

    def update_ui(self, records):
        self.table.setRowCount(len(records))
        for i, row in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('Equipment Name', row.get('name', '')))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('Type', row.get('type', '')))))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get('Pressure', row.get('pressure', 0)))))
            self.table.setItem(i, 3, QTableWidgetItem(str(row.get('Temperature', row.get('temp', 0)))))
            
            status = row.get('Status', 'OK')
            item = QTableWidgetItem(status)
            if status == 'CRITICAL':
                item.setBackground(QColor("#ffcccc"))
            self.table.setItem(i, 4, item)
            
        # Update Chart (Pressure vs Temp)
        df = pd.DataFrame(records)
        self.canvas.axes.cla()
        if not df.empty and 'Pressure' in df and 'Temperature' in df:
            self.canvas.axes.scatter(df['Pressure'], df['Temperature'])
            self.canvas.axes.set_xlabel('Pressure')
            self.canvas.axes.set_ylabel('Temperature')
            self.canvas.axes.set_title('Pressure vs Temperature')
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EquipmentApp()
    window.show()
    sys.exit(app.exec_())