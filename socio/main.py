import sys
from collections import deque
from typing import Optional, Iterator
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGraphicsView, QGraphicsScene,
                             QGraphicsRectItem, QGraphicsTextItem, QTreeWidget, QTreeWidgetItem,
                             QGroupBox, QScrollArea, QProgressBar, QSplitter, QMessageBox, 
                             QComboBox, QMenu, QSizePolicy, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QAction, QTransform
from utils.process import Process
from utils.buddy_system import BuddySystem

process = {}

class MemoryBlockItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, text, status, size, pid, process_size):
        super().__init__(x, y, width, height)
        
        # Configurar colores según el estado
        if status == "allocated":
            brush = QBrush(QColor(255, 100, 100))  # Rojo
            text_color = QColor(255, 255, 255)     # Blanco
            border_color = QColor(180, 0, 0)       # Borde rojo oscuro
        elif status == "split":
            brush = QBrush(QColor(100, 100, 255))  # Azul
            text_color = QColor(255, 255, 255)     # Blanco
            border_color = QColor(0, 0, 180)       # Borde azul oscuro
        else:
            brush = QBrush(QColor(100, 255, 100))  # Verde
            text_color = QColor(0, 0, 0)           # Negro
            border_color = QColor(0, 180, 0)       # Borde verde oscuro
            
        self.setBrush(brush)
        self.setPen(QPen(border_color, 2))
        
        # Ajustar tamaño de fuente según el tamaño del bloque
        font_size = 8 if size >= 128 else 7
        
        # Crear texto principal
        self.text_item = QGraphicsTextItem(text)
        self.text_item.setDefaultTextColor(text_color)
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        self.text_item.setFont(font)
        
        # Centrar texto principal
        text_rect = self.text_item.boundingRect()
        text_x = x + (width - text_rect.width()) / 2
        text_y = y + 5  # Pequeño margen superior
        self.text_item.setPos(text_x, text_y)
        
        # Si es un bloque asignado, mostrar información del proceso
        if status == "allocated":
            # Crear texto adicional para mostrar información del proceso
            process_text = f"PID: {pid}\n{process_size} kB / {size - process_size} KB"
            self.process_text_item = QGraphicsTextItem(process_text)
            self.process_text_item.setDefaultTextColor(text_color)
            
            # Usar fuente un poco más pequeña
            process_font = QFont("Arial", font_size - 1, QFont.Weight.Bold)
            self.process_text_item.setFont(process_font)
            
            process_text_rect = self.process_text_item.boundingRect()
            process_text_x = x + (width - process_text_rect.width()) / 2
            process_text_y = y + height - process_text_rect.height() - 5  # Colocar en la parte inferior
            
            self.process_text_item.setPos(process_text_x, process_text_y)

class BuddySystemVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.buddy_system = None
        self.node_positions = {}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Buddy System Memory Management - Professional Visualizer")
        self.setGeometry(50, 50, 1800, 1000)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter con proporción 30%-70%
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Controles (30%)
        left_panel = QWidget()
        left_panel.setMaximumWidth(500)
        left_layout = QVBoxLayout(left_panel)
        
        # Grupo de configuración del sistema
        config_group = QGroupBox("Configuración del Sistema")
        config_layout = QFormLayout(config_group)
        
        # Entrada para tamaño máximo de memoria (potencias de 2)
        max_size_layout = QHBoxLayout()
        max_size_layout.addWidget(QLabel("Tamaño máximo:"))
        self.max_size_combo = QComboBox()
        sizes = [64, 128, 256, 512, 1024, 2048, 4096]
        for size in sizes:
            self.max_size_combo.addItem(f"{size} KB", size)
        self.max_size_combo.setCurrentIndex(4)  # 1024 KB por defecto
        max_size_layout.addWidget(self.max_size_combo)
        config_layout.addRow(max_size_layout)

        # Entrada para tamaño mínimo de bloque (potencias de 2)
        min_size_layout = QHBoxLayout()
        min_size_layout.addWidget(QLabel("Tamaño mínimo:"))
        self.min_size_combo = QComboBox()
        min_sizes = [8, 16, 32, 64, 128, 256]
        for size in min_sizes:
            self.min_size_combo.addItem(f"{size} KB", size)
        self.min_size_combo.setCurrentIndex(3)  # 64 KB por defecto
        min_size_layout.addWidget(self.min_size_combo)
        config_layout.addRow(min_size_layout)
        
        # Botón para inicializar el sistema
        self.init_btn = QPushButton("Inicializar Sistema")
        self.init_btn.clicked.connect(self.initialize_system)
        config_layout.addRow(self.init_btn)
        
        left_layout.addWidget(config_group)
        
        # Grupo de controles
        controls_group = QGroupBox("Controles de Memoria")
        controls_layout = QVBoxLayout(controls_group)
        
        # Entrada para PID
        pid_layout = QHBoxLayout()
        pid_layout.addWidget(QLabel("PID:"))
        self.pid_input = QLineEdit()
        self.pid_input.setPlaceholderText("ID del proceso")
        pid_layout.addWidget(self.pid_input)
        controls_layout.addLayout(pid_layout)
        
        # Entrada para tamaño
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Tamaño:"))
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("Tamaño en bytes")
        size_layout.addWidget(self.size_input)
        controls_layout.addLayout(size_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        self.allocate_btn = QPushButton("Asignar Memoria")
        self.allocate_btn.clicked.connect(self.allocate_memory)
        self.allocate_btn.setEnabled(False)
        buttons_layout.addWidget(self.allocate_btn)
        controls_layout.addLayout(buttons_layout)
        
        # Barras de progreso para memoria
        memory_info_layout = QVBoxLayout()
        
        # Barra de memoria usada
        used_layout = QHBoxLayout()
        used_layout.addWidget(QLabel("Memoria Usada:"))
        self.memory_used_bar = QProgressBar()
        self.memory_used_bar.setFormat("%v KB (%p%)")
        self.memory_used_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cc0000;
                border-radius: 5px;
                text-align: center;
                background: #ffcccc;
                color: black;
            }
            QProgressBar::chunk {
                background-color: #ff6464;
                width: 10px;
            }
        """)
        used_layout.addWidget(self.memory_used_bar)
        memory_info_layout.addLayout(used_layout)
        
        # Barra de memoria libre
        free_layout = QHBoxLayout()
        free_layout.addWidget(QLabel("Memoria Libre:"))
        self.memory_free_bar = QProgressBar()
        self.memory_free_bar.setFormat("%v KB (%p%)")
        self.memory_free_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #006600;
                border-radius: 5px;
                text-align: center;
                background: #ccffcc;
                color: black;
            }
            QProgressBar::chunk {
                background-color: #64ff64;
                width: 10px;
            }
        """)
        free_layout.addWidget(self.memory_free_bar)
        memory_info_layout.addLayout(free_layout)
        
        controls_layout.addLayout(memory_info_layout)
        left_layout.addWidget(controls_group)
        
        # Menú desplegable de procesos
        processes_group = QGroupBox("Gestión de Procesos")
        processes_layout = QVBoxLayout(processes_group)
        
        # ComboBox para seleccionar procesos
        self.process_combo = QComboBox()
        self.process_combo.setPlaceholderText("Seleccione un proceso")
        self.process_combo.currentIndexChanged.connect(self.on_process_selected)
        processes_layout.addWidget(QLabel("Seleccionar proceso:"))
        processes_layout.addWidget(self.process_combo)
        
        # Botón para liberar proceso seleccionado
        self.release_selected_btn = QPushButton("Liberar Proceso Seleccionado")
        self.release_selected_btn.clicked.connect(self.release_selected_memory)
        self.release_selected_btn.setEnabled(False)
        processes_layout.addWidget(self.release_selected_btn)
        
        left_layout.addWidget(processes_group)
        left_layout.addStretch()
        
        # Panel derecho: Visualización (70%)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        visualization_group = QGroupBox("Visualización Detallada del Árbol Buddy System")
        visualization_layout = QVBoxLayout(visualization_group)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Habilitar zoom con rueda del mouse
        self.view.wheelEvent = self.zoom_event
        
        visualization_layout.addWidget(self.view)
        right_layout.addWidget(visualization_group)
        
        # Añadir paneles al splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 1300])
        
        main_layout.addWidget(splitter)
        
        # Menú contextual para el árbol
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.triggered.connect(self.reset_zoom)
        fit_view_action = QAction("Ajustar Vista", self)
        fit_view_action.triggered.connect(self.fit_view)
        self.addAction(zoom_in_action)
        self.addAction(zoom_out_action)
        self.addAction(reset_zoom_action)
        self.addAction(fit_view_action)
        
        # Inicializar con un sistema por defecto
        self.initialize_system()
    
    def initialize_system(self):
        max_size = self.max_size_combo.currentData()
        min_size = self.min_size_combo.currentData()
        
        if min_size >= max_size:
            QMessageBox.warning(self, "Error", "El tamaño mínimo debe ser menor que el tamaño máximo")
            return
            
        if max_size % min_size != 0:
            QMessageBox.warning(self, "Error", "El tamaño máximo debe ser múltiplo del tamaño mínimo")
            return
            
        self.buddy_system = BuddySystem(MAX_SIZE=max_size, MIN_SIZE=min_size)
        self.update_interface()
        
        # Habilitar controles
        self.allocate_btn.setEnabled(True)
        self.release_selected_btn.setEnabled(True)
    
    def zoom_event(self, event):
        # Zoom con la rueda del mouse
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        self.view.scale(1.2, 1.2)
    
    def zoom_out(self):
        self.view.scale(0.8, 0.8)
    
    def reset_zoom(self):
        self.view.resetTransform()
    
    def fit_view(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def allocate_memory(self):
        if not self.buddy_system:
            QMessageBox.warning(self, "Error", "Primero debe inicializar el sistema")
            return
            
        try:
            pid = int(self.pid_input.text())
            size = int(self.size_input.text())
            
            if pid <= 0 or size <= 0:
                QMessageBox.warning(self, "Error", "Los valores deben ser positivos")
                return
                
            success = self.buddy_system.allocate(pid, size)
            if success:
                self.update_interface()
                self.pid_input.clear()
                self.size_input.clear()
            else:
                QMessageBox.warning(self, "Error", "No se pudo asignar memoria. Memoria insuficiente o PID duplicado")
        except ValueError:
            QMessageBox.warning(self, "Error", "Por favor ingrese valores numéricos válidos")
    
    def release_selected_memory(self):
        if not self.buddy_system:
            QMessageBox.warning(self, "Error", "Primero debe inicializar el sistema")
            return
            
        if self.process_combo.currentIndex() > 0:
            pid_text = self.process_combo.currentText().split(":")[0]
            try:
                pid = int(pid_text)
                success = self.buddy_system.release(pid)
                if success:
                    self.update_interface()
                else:
                    QMessageBox.warning(self, "Error", "PID no encontrado")
            except ValueError:
                QMessageBox.warning(self, "Error", "Error al obtener el PID")
    
    def on_process_selected(self, index):
        if index > 0:
            pid_text = self.process_combo.currentText().split(":")[0]
            self.pid_input.setText(pid_text)
    
    def update_interface(self):
        if not self.buddy_system:
            return
            
        # Actualizar barras de progreso
        used_memory = self.buddy_system.get_used_memory()
        free_memory = self.buddy_system.get_free_memory()
        total_memory = self.buddy_system.MAX_SIZE
        usage_percentage = (used_memory / total_memory) * 100
        
        self.memory_used_bar.setMaximum(total_memory)
        self.memory_used_bar.setValue(used_memory)
        
        self.memory_free_bar.setMaximum(total_memory)
        self.memory_free_bar.setValue(free_memory)
        
        # Actualizar combo box de procesos
        self.process_combo.clear()
        self.process_combo.addItem("Seleccione un proceso")
        
        # Recorrer todos los nodos para encontrar los asignados usando el iterador BFS
        allocated_processes = []
        for node in self.buddy_system:
            if node.is_allocated:
                allocated_processes.append((node.pid, node.process_size))
        
        # Ordenar procesos por PID y añadir al combo box
        allocated_processes.sort()
        for pid, size in allocated_processes:
            self.process_combo.addItem(f"{pid}: {size} bytes")
        
        # Actualizar visualización del árbol
        self.scene.clear()
        self.node_positions.clear()
        
        # Usar visualización profesional
        self.draw_professional_tree()
        
        # Ajustar la vista
        self.fit_view()
    
    def draw_professional_tree(self):
        """Visualización profesional del árbol usando BFS"""
        if not self.buddy_system or not self.buddy_system.root:
            return
        
        # Organizar nodos por niveles
        levels = {}
        queue = deque([(self.buddy_system.root, 0)])
        
        while queue:
            node, level = queue.popleft()
            
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
            
            if node.left:
                queue.append((node.left, level + 1))
            if node.right:
                queue.append((node.right, level + 1))
        
        # Calcular posiciones
        max_level = max(levels.keys()) if levels else 0
        base_x = 600  # Posición central inicial
        
        for level, nodes in levels.items():
            y = 50 + level * 120  # Espaciado vertical
            
            # Calcular espaciado horizontal para este nivel
            if level == 0:
                # Raíz en el centro
                x_positions = [base_x]
            else:
                # Distribuir nodos equitativamente
                level_width = min(len(nodes) * 200, 1200)
                start_x = base_x - level_width / 2
                x_positions = [start_x + i * (level_width / max(len(nodes), 1)) for i in range(len(nodes))]
            
            for i, node in enumerate(nodes):
                x = x_positions[i] if i < len(x_positions) else base_x
                self.draw_node_with_style(node, x, y, level)
        
        # Dibujar conexiones
        for level, nodes in levels.items():
            for node in nodes:
                if node.left and node.left in self.node_positions and node in self.node_positions:
                    self.draw_connection(node, node.left, "L")
                if node.right and node.right in self.node_positions and node in self.node_positions:
                    self.draw_connection(node, node.right, "R")
    
    def draw_node_with_style(self, node, x, y, level):
        """Dibuja un nodo con estilo profesional"""
        # Tamaño basado en el nivel
        width = max(120 - level * 8, 80)  # Aumentado el ancho mínimo
        height = 60 if node.is_allocated else 50  # Más alto si está asignado para mostrar info adicional
        
        # Determinar estado y texto
        if node.is_allocated:
            status = "allocated"
            text = f"Size: {node.size}KB"
        elif node.is_split:
            status = "split"
            text = f"SPLIT\nSize: {node.size}KB"
        else:
            status = "free"
            text = f"FREE\nSize: {node.size}KB"
        
        # Dibujar nodo con sombra y estilo
        rect = MemoryBlockItem(x - width/2, y, width, height, text, status, node.size, node.pid, node.process_size)
        self.scene.addItem(rect)
        self.scene.addItem(rect.text_item)
        
        # Si es un bloque asignado, añadir el texto del proceso
        if hasattr(rect, 'process_text_item'):
            self.scene.addItem(rect.process_text_item)
        
        # Guardar posición
        self.node_positions[node] = (x, y + height/2)
    
    def draw_connection(self, parent, child, label_text):
        """Dibuja una conexión con estilo profesional"""
        if parent not in self.node_positions or child not in self.node_positions:
            return
        
        parent_x, parent_y = self.node_positions[parent]
        child_x, child_y = self.node_positions[child]
        
        # Dibujar línea
        line = self.scene.addLine(parent_x, parent_y + 25, child_x, child_y - 25, 
                                QPen(QColor(100, 100, 100), 2, Qt.PenStyle.DashLine))
        
        # Agregar etiqueta
        mid_x = (parent_x + child_x) / 2
        mid_y = (parent_y + child_y) / 2
        
        label = QGraphicsTextItem(label_text)
        label.setPos(mid_x - 5, mid_y - 10)
        label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        label.setDefaultTextColor(QColor(70, 70, 70))
        
        # Fondo para la etiqueta
        label_bg = QGraphicsRectItem(mid_x - 12, mid_y - 15, 24, 20)
        label_bg.setBrush(QBrush(QColor(255, 255, 255, 200)))
        label_bg.setPen(QPen(Qt.GlobalColor.transparent))
        
        self.scene.addItem(label_bg)
        self.scene.addItem(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BuddySystemVisualizer()
    window.show()
    sys.exit(app.exec())