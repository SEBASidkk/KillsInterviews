"""
gui.py
Ventana flotante siempre visible usando PyQt6.
"""
import sys
import queue
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QTextEdit, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from config import CONFIG


class FloatingWindow(QMainWindow):
    """
    Ventana flotante semitransparente siempre on-top.
    Recibe resultados del LLM via señales Qt (thread-safe).
    """
    
    # Señal para actualizar texto desde cualquier hilo
    update_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.update_signal.connect(self._update_display)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la ventana flotante."""
        # Configuración de ventana
        self.setWindowTitle("Interview Helper")
        self.setGeometry(100, 100, CONFIG.WINDOW_WIDTH, CONFIG.WINDOW_HEIGHT)
        
        # Siempre on top y sin borde de decoración
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # No aparece en taskbar
        )
        
        # Opacidad
        self.setWindowOpacity(CONFIG.WINDOW_OPACITY)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🎤 Interview Helper")
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #00ff88;")
        header.addWidget(title)
        
        header.addStretch()
        
        # Botón cerrar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ff6666; }
        """)
        close_btn.clicked.connect(self._confirm_close)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # Separador
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #444;")
        layout.addWidget(separator)
        
        # Área de texto para bullets
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        self.text_area.setPlaceholderText("Esperando preguntas del entrevistador...")
        layout.addWidget(self.text_area)
        
        # Status bar
        self.status = QLabel("⏳ Iniciando...")
        self.status.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status)
        
        # Hacer ventana arrastrable
        self._drag_pos = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def _update_display(self, text: str):
        """Actualiza el área de texto con nuevos bullets."""
        self.text_area.setText(text)
        self.status.setText("✅ Respuesta actualizada")
    
    def update_bullets(self, text: str):
        """Método público seguro para hilos externos."""
        self.update_signal.emit(text)
    
    def set_status(self, text: str):
        """Actualiza el status bar."""
        self.status.setText(text)
    
    def _confirm_close(self):
        """Muestra confirmación antes de cerrar."""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 'Confirmar',
            '¿Detener el Asistente de Entrevistas?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()


class GUIThread(threading.Thread):
    """
    Hilo dedicado a ejecutar el loop de eventos de PyQt.
    """
    
    def __init__(self, result_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(name="GUI", daemon=True)
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.window = None
        self.app = None
    
    def run(self):
        """Inicia la aplicación Qt y el timer de polling."""
        print("[GUI] 🖥️ Iniciando interfaz gráfica...")
        
        self.app = QApplication(sys.argv)
        self.window = FloatingWindow()
        self.window.show()
        
        # Timer para verificar la queue de resultados
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_queue)
        self.timer.start(CONFIG.UPDATE_INTERVAL_MS)
        
        # Timer para verificar señal de parada
        self.stop_timer = QTimer()
        self.stop_timer.timeout.connect(self._check_stop)
        self.stop_timer.start(500)
        
        print("[GUI] ✅ Ventana lista - Arrastra para mover")
        self.app.exec()
    
    def _check_queue(self):
        """Verifica si hay nuevos resultados del LLM."""
        try:
            while True:  # Vaciar toda la queue
                result = self.result_queue.get_nowait()
                if self.window:
                    self.window.update_bullets(result)
        except queue.Empty:
            pass
    
    def _check_stop(self):
        """Verifica si debe cerrar la aplicación."""
        if self.stop_event.is_set():
            self.timer.stop()
            self.stop_timer.stop()
            self.app.quit()