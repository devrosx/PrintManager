import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QWidget, QMessageBox
from PyQt6.QtCore import QSettings

class SettingsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nastavení aplikace")

        # Vytvoření tabulky
        self.table = QTableWidget(5, 2)  # 5 řádků, 2 sloupce
        self.table.setHorizontalHeaderLabels(["Nastavení", "Hodnota"])

        # Předvolby (můžete přidat další)
        default_settings = [
            ["Nastavení 1", "Hodnota 1"],
            ["Nastavení 2", "Hodnota 2"],
            ["Nastavení 3", "Hodnota 3"],
            ["Nastavení 4", "Hodnota 4"],
            ["Nastavení 5", "Hodnota 5"],
        ]

        for row, (setting, value) in enumerate(default_settings):
            self.table.setItem(row, 0, QTableWidgetItem(setting))
            self.table.setItem(row, 1, QTableWidgetItem(value))

        # Tlačítka
        self.save_button = QPushButton("Uložit nastavení")
        self.save_button.clicked.connect(self.save_settings)

        self.load_button = QPushButton("Načíst nastavení")
        self.load_button.clicked.connect(self.load_settings)

        # Rozložení
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.save_button)
        layout.addWidget(self.load_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Načtení nastavení při spuštění
        self.load_settings()

    def save_settings(self):
        settings = QSettings("MyCompany", "MyApp")  # Název společnosti a aplikace
        for row in range(self.table.rowCount()):
            setting = self.table.item(row, 0).text()
            value = self.table.item(row, 1).text()
            settings.setValue(setting, value)
        
        QMessageBox.information(self, "Uložení", "Nastavení byla uložena.")

    def load_settings(self):
        settings = QSettings("MyCompany", "MyApp")  # Název společnosti a aplikace
        for row in range(self.table.rowCount()):
            setting = self.table.item(row, 0).text()
            value = settings.value(setting, "Není nastaveno")  # Výchozí hodnota
            self.table.item(row, 1).setText(value)
        
        QMessageBox.information(self, "Načtení", "Nastavení byla načtena.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsApp()
    window.show()
    sys.exit(app.exec())
