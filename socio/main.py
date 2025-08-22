import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QGraphicsView, QGraphicsScene,
                             QGraphicsRectItem, QGraphicsTextItem, QTreeWidget, QTreeWidgetItem,
                             QGroupBox, QScrollArea, QProgressBar, QSplitter, QMessageBox, 
                             QComboBox, QMenu, QSizePolicy, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QAction, QTransform

# Importar tu implementación del Buddy System
from utils.buddy_system import BuddySystem, Node

class MemoryBlockItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, text, status, size):
        super().__init__(x, y, width, height)
        
        # Configurar colores según el estado
        if status == "allocated":
            brush = QBrush(QColor(255, 100, 100))  # Rojo
            text_color = QColor(255, 255, 255)     # Blanco
        elif status == "split":
            brush = QBrush(QColor(100, 100, 255))  # Azul
            text_color = QColor(255, 255, 255)     # Blanco
        else:
            brush = QBrush(QColor(100, 255, 100))  # Verde
            text_color = QColor(0, 0, 0)           # Negro
            
        self.setBrush(brush)
        self.setPen(QPen(QColor(0, 0, 0), 1))
        
        # Añadir texto centrado
        self.text_item = QGraphicsTextItem(text)
        self.text_item.setDefaultTextColor(text_color)
        
        # Ajustar tamaño de fuente según el tamaño del bloque
        font_size = 10 if size >= 128 else 8
        self.text_item.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        text_rect = self.text_item.boundingRect()
        text_x = x + (width - text_rect.width()) / 2
        text_y = y + (height - text_rect.height()) / 2
        self.text_item.setPos(text_x, text_y)

class BuddySystemVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.buddy_system = None
        self.node_positions = {}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Buddy System Memory Management - Tree Visualizer")
        self.setGeometry(50, 50, 1600, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter con proporción 25%-75%
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Controles (25%)
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # Grupo de configuración del sistema
        config_group = QGroupBox("Configuración del Sistema")
        config_layout = QFormLayout(config_group)
        
        # Entrada para tamaño máximo de memoria (potencias de 2)
        max_size_layout = QHBoxLayout()
        max_size_layout.addWidget(QLabel("Tamaño máximo:"))
        self.max_size_combo = QComboBox()
        # Agregar opciones de potencias de 2
        sizes = [64, 128, 256, 512, 1024, 2048, 4096, 8192]
        for size in sizes:
            self.max_size_combo.addItem(f"{size} KB", size)
        self.max_size_combo.setCurrentIndex(4)  # 1024 KB por defecto
        max_size_layout.addWidget(self.max_size_combo)
        config_layout.addRow(max_size_layout)

        # Entrada para tamaño mínimo de bloque (potencias de 2)
        min_size_layout = QHBoxLayout()
        min_size_layout.addWidget(QLabel("Tamaño mínimo:"))
        self.min_size_combo = QComboBox()
        # Agregar opciones de potencias de 2 (más pequeñas)
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
        self.memory_used_bar.setFormat("%v bytes (%p%)")
        self.memory_used_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff6464; }")
        used_layout.addWidget(self.memory_used_bar)
        memory_info_layout.addLayout(used_layout)
        
        # Barra de memoria libre
        free_layout = QHBoxLayout()
        free_layout.addWidget(QLabel("Memoria Libre:"))
        self.memory_free_bar = QProgressBar()
        self.memory_free_bar.setFormat("%v bytes (%p%)")
        self.memory_free_bar.setStyleSheet("QProgressBar::chunk { background-color: #5F7689; }")
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
        self.release_selected_btn = QPushButton("Liberar Proceso")
        self.release_selected_btn.clicked.connect(self.release_selected_memory)
        self.release_selected_btn.setEnabled(False)
        processes_layout.addWidget(self.release_selected_btn)
        
        left_layout.addWidget(processes_group)
        left_layout.addStretch()
        
        # Panel derecho: Visualización (75%)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        visualization_group = QGroupBox("Visualización del Árbol Buddy System")
        visualization_layout = QVBoxLayout(visualization_group)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        splitter.setSizes([400, 1200])
        
        main_layout.addWidget(splitter)
        
        # Menú contextual para el árbol
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.triggered.connect(self.reset_zoom)
        self.addAction(zoom_in_action)
        self.addAction(zoom_out_action)
        self.addAction(reset_zoom_action)
        
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
    
    def release_memory(self):
        if not self.buddy_system:
            QMessageBox.warning(self, "Error", "Primero debe inicializar el sistema")
            return
            
        try:
            pid = int(self.pid_input.text())
            success = self.buddy_system.release(pid)
            if success:
                self.update_interface()
                self.pid_input.clear()
            else:
                QMessageBox.warning(self, "Error", "PID no encontrado")
        except ValueError:
            QMessageBox.warning(self, "Error", "Por favor ingrese un PID numérico válido")
    
    def release_selected_memory(self):
        if not self.buddy_system:
            QMessageBox.warning(self, "Error", "Primero debe inicializar el sistema")
            return
            
        if self.process_combo.currentIndex() > 0:
            pid_text = self.process_combo.currentText().split(":")[0]
            try:
                pid = int(pid_text)
                self.pid_input.setText(str(pid))
                self.release_memory()
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
        
        # Recorrer todos los nodos para encontrar los asignados
        allocated_processes = []
        for node in self.buddy_system:
            if node.is_allocated and node.pid != -1:
                allocated_processes.append((node.pid, node.size))
        
        # Ordenar procesos por PID y añadir al combo box
        allocated_processes.sort()
        for pid, size in allocated_processes:
            self.process_combo.addItem(f"{pid}: {size} bytes")
        
        # Actualizar visualización del árbol
        self.scene.clear()
        self.node_positions.clear()
        
        # Calcular dimensiones para la visualización
        tree_depth = self.calculate_tree_depth(self.buddy_system.root)
        
        # Calcular el ancho total necesario basado en la profundidad
        # Cada nivel duplica la cantidad de nodos, así que necesitamos más espacio
        total_width = 100 * (2 ** tree_depth)  # Espacio exponencial para niveles profundos
        initial_width = min(total_width, 2000)  # Limitar el ancho máximo
        
        # Dibujar el árbol con mejor espaciado
        self.draw_tree(self.buddy_system.root, initial_width/2, 50, initial_width/2, 0, tree_depth)
        
        # Ajustar la vista para que se vea todo el árbol
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def calculate_tree_depth(self, node):
        """Calcula la profundidad máxima del árbol"""
        if node is None:
            return 0
        if not node.is_split:
            return 1
        return 1 + max(self.calculate_tree_depth(node.left), self.calculate_tree_depth(node.right))
    
    def calculate_tree_layout(self, node, level=0, pos=0, max_depth=0):
        """
        Calcula las posiciones de todos los nodos usando un algoritmo de layout
        que evita solapamientos
        """
        if node is None:
            return pos
        
        # Almacenar información de layout para este nodo
        node._x = pos
        node._y = level * 120  # Espaciado vertical fijo
        
        if node.is_split and node.left and node.right:
            # Calcular posiciones para hijos
            left_pos = self.calculate_tree_layout(node.left, level + 1, pos, max_depth)
            right_pos = self.calculate_tree_layout(node.right, level + 1, left_pos + 1, max_depth)
            
            # Centrar el nodo padre sobre sus hijos
            node._x = (node.left._x + node.right._x) / 2
            return max(left_pos, right_pos)
        else:
            # Nodo hoja
            return pos + 1
    
    def draw_tree(self, node, x, y, horizontal_spacing, level, max_depth):
        if node is None:
            return
        
        # Ajustar dimensiones según la profundidad del árbol
        base_width = 100
        base_height = 40
        width = max(base_width - (level * 5), 60)  # Reducir tamaño en niveles profundos
        height = max(base_height - (level * 3), 25)
        
        # Ajustar espaciado vertical
        vertical_spacing = 80
        
        # Determinar estado y texto
        if node.is_allocated:
            status = "allocated"
            text = f"PID {node.pid}\n{node.size}B"
        elif node.is_split:
            status = "split"
            text = f"DIV\n{node.size}B"
        else:
            status = "free"
            text = f"LIBRE\n{node.size}B"
        
        # Dibujar rectángulo
        rect = MemoryBlockItem(x - width/2, y, width, height, text, status, node.size)
        self.scene.addItem(rect)
        self.scene.addItem(rect.text_item)
        
        # Guardar posición para las conexiones
        self.node_positions[node] = (x, y + height/2)
        
        # Dibujar hijos si existen
        if node.left and node.right:
            # Calcular nuevas posiciones
            new_y = y + vertical_spacing
            
            # Mantener un espaciado mínimo entre nodos hijos
            min_spacing = 80  # Espaciado mínimo entre nodos hijos
            new_horizontal_spacing = max(horizontal_spacing * 0.5, min_spacing)
            
            left_x = x - new_horizontal_spacing
            right_x = x + new_horizontal_spacing
            
            # Dibujar líneas conectivas con ángulo
            self.scene.addLine(x, y + height, left_x, new_y, QPen(Qt.GlobalColor.gray, 1.5))
            self.scene.addLine(x, y + height, right_x, new_y, QPen(Qt.GlobalColor.gray, 1.5))
            
            # Dibujar hijos recursivamente
            self.draw_tree(node.left, left_x, new_y, new_horizontal_spacing, level + 1, max_depth)
            self.draw_tree(node.right, right_x, new_y, new_horizontal_spacing, level + 1, max_depth)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BuddySystemVisualizer()
    window.show()
    sys.exit(app.exec())