"""
Modern component list module with card-based view
"""
import os
import sys
from typing import List, Optional, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QMessageBox, 
    QInputDialog, QFileDialog, QApplication, QMainWindow, 
    QStackedWidget, QScrollArea, QGridLayout
)
from PyQt6.QtGui import QFont, QIcon, QFontMetrics
from PyQt6.QtCore import Qt, QSize

from core.component import Component, ComponentManager

class ComponentCard(QFrame):
    """Card widget for displaying a component"""
    
    def __init__(
        self, 
        component: Component, 
        on_edit: Optional[Callable] = None, 
        on_remove: Optional[Callable] = None,
        on_rename: Optional[Callable] = None,
        on_duplicate: Optional[Callable] = None,
        parent=None
    ):
        """
        Initialize the component card
        
        Args:
            component: The component to display
            on_edit: Callback for edit action
            on_remove: Callback for remove action
            on_rename: Callback for rename action
            on_duplicate: Callback for duplicate action
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Card style
        self.setStyleSheet("""
            QFrame {
                background-color: #F0F4F8;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
                padding: 12px;
                margin: 5px;
            }
            QFrame:hover {
                background-color: #E6EDF3;
                border: 1px solid #CBD5E0;
            }
        """)
        
        # Store the component
        self.component = component
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Component name
        name_label = QLabel(component.name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # File info
        file_label = QLabel(f"File: {os.path.basename(component.filepath)}")
        file_label.setStyleSheet("color: #4A5568; font-size: 10px;")
        layout.addWidget(file_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Edit button
        if on_edit:
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #4299E1; color: white;")
            edit_btn.clicked.connect(lambda: on_edit(component))
            button_layout.addWidget(edit_btn)
        
        # Remove button
        if on_remove:
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("background-color: #F56565; color: white;")
            remove_btn.clicked.connect(lambda: on_remove(component))
            button_layout.addWidget(remove_btn)
        
        # Rename button
        if on_rename:
            rename_btn = QPushButton("Rename")
            rename_btn.clicked.connect(lambda: on_rename(component))
            button_layout.addWidget(rename_btn)
        
        # Duplicate button
        if on_duplicate:
            duplicate_btn = QPushButton("Duplicate")
            duplicate_btn.clicked.connect(lambda: on_duplicate(component))
            button_layout.addWidget(duplicate_btn)
        
        layout.addLayout(button_layout)
                         
class ComponentListWidget(QWidget):
    """Modern component list widget"""
        
    def __init__(self, parent=None):
        """Initialize the component list widget"""
        super().__init__(parent)
        
        # Component manager
        self.component_manager = ComponentManager()
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)
        
        # Add component button
        add_btn = QPushButton("Add Component")
        add_btn.clicked.connect(self.add_component)
        toolbar_layout.addWidget(add_btn)
        
        # Grid view - using QScrollArea and QGridLayout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(self.grid_container)
        
        layout.addWidget(scroll_area)
    
    def add_component(self):
        """Add a new component from file"""
        filetypes = "TypeScript React Files (*.tsx);;JavaScript React Files (*.jsx);;All Files (*.*)"
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Component Files", 
            "", 
            filetypes
        )
        
        if filepath:
            try:
                component = self.add_component_from_path(filepath)
                if component:
                    self.update_component_view(component)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def add_component_from_path(self, filepath: str) -> Optional[Component]:
        """Add a component from the specified file path"""
        try:
            # Check if file already added
            for component in self.component_manager.components:
                if os.path.samefile(component.filepath, filepath):
                    QMessageBox.warning(
                        self, 
                        "Duplicate Component", 
                        f"Component {component.name} is already in the list"
                    )
                    return None
            
            # Add the component
            component = self.component_manager.add_component(filepath)
            return component
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error adding component: {str(e)}")
            return None
    
    def update_component_view(self, component):
        """Update the grid view with the new component"""
        # Create component card
        card = ComponentCard(
            component, 
            on_edit=self.edit_component,
            on_remove=self.remove_component,
            on_rename=self.rename_component,
            on_duplicate=self.duplicate_component
        )
        
        # Calculate position in grid (4 columns)
        count = self.grid_layout.count()
        row = count // 4
        col = count % 4
        
        # Add to grid
        self.grid_layout.addWidget(card, row, col)
    
    def edit_component(self, component):
        """Edit a component"""
        # Look for a parent window that might have an edit method
        parent = self.parent()
        while parent:
            if hasattr(parent, 'edit_component'):
                parent.edit_component(component)
                return
            parent = parent.parent()
        
        # Fallback if no parent has edit_component
        QMessageBox.information(self, "Edit", f"Editing {component.name}")
    
    def remove_component(self, component):
        """Remove a component"""
        reply = QMessageBox.question(
            self, 
            'Remove Component', 
            f'Are you sure you want to remove {component.name}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.component_manager.remove_component(component)
            # Refresh view after removal
            self.refresh_components()
    
    def rename_component(self, component):
        """Rename a component"""
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Component", 
            f"Enter new name for {component.name}:",
            text=component.name
        )
        
        if ok and new_name and new_name != component.name:
            try:
                # Use component's rename method
                old_filepath = component.rename(new_name)
                
                # Refresh view
                self.refresh_components()
                
                # Optional: Ask to delete old file
                reply = QMessageBox.question(
                    self, 
                    "Delete Old File", 
                    f"Delete the original file {os.path.basename(old_filepath)}?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        os.remove(old_filepath)
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Could not delete file: {e}")
            
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not rename component: {e}")
    
    def duplicate_component(self, component):
        """Duplicate a component"""
        new_name, ok = QInputDialog.getText(
            self, 
            "Duplicate Component", 
            f"Enter name for the copy of {component.name}:",
            text=f"{component.name}_copy"
        )
        
        if ok and new_name:
            try:
                # Create a duplicate
                new_component = component.duplicate(new_name)
                
                # Add to component manager
                self.component_manager.components.append(new_component)
                
                # Update view
                self.update_component_view(new_component)
            
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not duplicate component: {e}")
    
    def refresh_components(self):
        """Refresh grid view"""
        # Clear existing views
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Repopulate views
        for component in self.component_manager.components:
            self.update_component_view(component)

# Standalone application for testing
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Component Manager")
        
        # Create central widget and component list
        central_widget = ComponentListWidget()
        self.setCentralWidget(central_widget)
    
    def edit_component(self, component):
        """Example edit method for testing"""
        QMessageBox.information(self, "Edit", f"Editing {component.name}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())