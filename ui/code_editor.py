"""
Modern code editor module with enhanced styling and features
"""
import re
import sys
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QLabel, QPushButton, QCheckBox, QFrame, QApplication, 
    QMainWindow, QScrollBar, QMessageBox
)
from PyQt6.QtGui import (
    QFont, QSyntaxHighlighter, QTextCharFormat, 
    QColor, QTextCursor, QPalette, QTextDocument, QIcon, QShortcut, QKeySequence
)
from PyQt6.QtCore import Qt, QRegularExpression, QTimer

class ModernSyntaxHighlighter(QSyntaxHighlighter):
    """Enhanced syntax highlighter for the code editor"""
    
    def __init__(self, document: QTextDocument, is_dark_mode: bool = True):
        super().__init__(document)
        
        self.is_dark_mode = is_dark_mode
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Define syntax highlighting rules"""
        # Color schemes
        colors = {
            'dark': {
                'comment': QColor('#6A9955'),     # Green
                'string': QColor('#CE9178'),      # Light orange
                'keyword': QColor('#569CD6'),     # Blue
                'number': QColor('#B5CEA8'),      # Light green
                'jsx_tag': QColor('#DCDCAA'),     # Yellow
                'prop': QColor('#9CDCFE'),        # Light blue
                'react_hook': QColor('#C586C0')   # Purple
            },
            'light': {
                'comment': QColor('#008000'),     # Green
                'string': QColor('#A31515'),      # Red
                'keyword': QColor('#0000FF'),     # Blue
                'number': QColor('#098658'),      # Green
                'jsx_tag': QColor('#800000'),     # Maroon
                'prop': QColor('#0070C1'),        # Blue
                'react_hook': QColor('#AF00DB')   # Purple
            }
        }
        
        theme = colors['dark'] if self.is_dark_mode else colors['light']
        
        # Highlighting rules
        self.highlighting_rules = []
        
        # Keywords
        keywords = ['import', 'from', 'export', 'default', 'const', 'let', 'var', 
                    'function', 'class', 'extends', 'return', 'if', 'else', 
                    'switch', 'case', 'for', 'while', 'do', 'try', 'catch', 
                    'throw', 'new', 'this', 'super', 'async', 'await', 
                    'static', 'get', 'set']
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(theme['keyword'])
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.highlighting_rules.append((QRegularExpression(pattern), keyword_format))
        
        # React hooks
        hooks = ['useState', 'useEffect', 'useContext', 'useReducer', 
                 'useCallback', 'useMemo', 'useRef', 
                 'useImperativeHandle', 'useLayoutEffect', 'useDebugValue']
        
        hook_format = QTextCharFormat()
        hook_format.setForeground(theme['react_hook'])
        hook_format.setFontWeight(QFont.Weight.Bold)
        
        for hook in hooks:
            pattern = f'\\b{hook}\\b'
            self.highlighting_rules.append((QRegularExpression(pattern), hook_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(theme['string'])
        self.highlighting_rules.append((QRegularExpression('".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression("'.*?'"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(theme['comment'])
        self.highlighting_rules.append((QRegularExpression('//.*'), comment_format))
        self.highlighting_rules.append((QRegularExpression('/\\*.*?\\*/'), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(theme['number'])
        self.highlighting_rules.append((QRegularExpression('\\b\\d+\\b'), number_format))
    
    def highlightBlock(self, text: str):
        """Apply highlighting rules to text block"""
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)

class CodeEditorWidget(QWidget):
    """Modern code editor widget with enhanced features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Find parent window for logging
        self.parent_window = parent
        while self.parent_window and not hasattr(self.parent_window, 'log'):
            self.parent_window = self.parent_window.parent()
        
        # Track the active component being edited
        self.active_component = None
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Text editor
        self.text_editor = QTextEdit()
        layout.addWidget(self.text_editor)
        
        # Setup search panel
        self.setup_search_panel(layout)
        
        # Setup syntax highlighting
        self.highlighter = ModernSyntaxHighlighter(
            self.text_editor.document(), 
            is_dark_mode=True
        )
        
        # Enable text modifications and undo/redo
        self.text_editor.setUndoRedoEnabled(True)
        
        # Add additional editor features
        self.enhance_code_editor()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the editor"""
        # Find shortcut (Ctrl+F)
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.toggle_search_panel)
        
        # Save shortcut (Ctrl+S)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_content)
    
    def setup_search_panel(self, layout):
        """Create improved search panel for find and replace with case sensitivity toggle"""
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #F5F7FA;
                border-radius: 4px;
                border: 1px solid #E2E8F0;
                padding: 8px;
                margin-top: 5px;
            }
        """)
        search_layout = QHBoxLayout()
        search_frame.setLayout(search_layout)
        
        # Search input with label
        search_label = QLabel("Find:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Text to find...")
        # Connect Return/Enter key to find_text
        self.search_input.returnPressed.connect(self.find_text)
        search_layout.addWidget(self.search_input)
        
        # Find buttons
        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self.find_text)
        search_layout.addWidget(find_btn)
        
        find_prev_btn = QPushButton("Find Previous")
        find_prev_btn.clicked.connect(lambda: self.find_text(backward=True))
        search_layout.addWidget(find_prev_btn)
        
        # Case sensitive checkbox
        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        self.case_sensitive_cb.setChecked(True)  # Default to case sensitive
        search_layout.addWidget(self.case_sensitive_cb)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        search_layout.addWidget(separator)
        
        # Replace input with label
        replace_label = QLabel("Replace:")
        search_layout.addWidget(replace_label)
        
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        search_layout.addWidget(self.replace_input)
        
        # Replace buttons
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace_text)
        search_layout.addWidget(replace_btn)
        
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all_text)
        search_layout.addWidget(replace_all_btn)
        
        # Add to layout
        layout.addWidget(search_frame)
        
        # Keep track of the last found position
        self.last_found_position = None
        
        # Initially hide the search panel
        search_frame.setVisible(False)
        self.search_frame = search_frame
    def toggle_search_panel(self):
        """Toggle the search panel visibility"""
        if hasattr(self, 'search_frame'):
            self.search_frame.setVisible(not self.search_frame.isVisible())
            if self.search_frame.isVisible():
                self.search_input.setFocus()
        
    def find_text(self, backward=False):
        """Find text in the editor with case sensitivity option"""
        search_text = self.search_input.text()
        if not search_text:
            return
        
        cursor = self.text_editor.textCursor()
        document = self.text_editor.document()
        
        # Start from the last position or current cursor
        if self.last_found_position is not None:
            cursor.setPosition(self.last_found_position)
        
        # Options for find - start with empty flags (0)
        flags = QTextDocument.FindFlag(0)  # Initialize with 0 for no flags
        
        # Add case sensitivity if checkbox is checked
        if self.case_sensitive_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        
        # Search for the text
        found_cursor = document.find(search_text, cursor, flags)
        
        # If not found from current position, try from start/end
        if found_cursor.isNull():
            # Start from beginning or end depending on direction
            cursor = QTextCursor(document)
            if backward:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            found_cursor = document.find(search_text, cursor, flags)
            
            # If still not found, inform the user
            if found_cursor.isNull():
                QMessageBox.information(self, "Find", f"Cannot find '{search_text}'")
                self.last_found_position = None
                return
        
        # Select the found text
        self.text_editor.setTextCursor(found_cursor)
        self.last_found_position = found_cursor.position()
        
        # Ensure the cursor is visible
        self.text_editor.ensureCursorVisible()
        
    def replace_all_text(self):
        """Replace all occurrences of the search text with case sensitivity option"""
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        
        if not search_text:
            return
        
        document = self.text_editor.document()
        cursor = QTextCursor(document)
        
        # Count for reporting
        count = 0
        
        # Use a transaction for better performance
        cursor.beginEditBlock()
        
        # Options for find - start with empty flags (0)
        flags = QTextDocument.FindFlag(0)  # Initialize with 0 for no flags
        
        # Add case sensitivity if checkbox is checked
        if self.case_sensitive_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        # Find and replace all occurrences
        while True:
            found_cursor = document.find(search_text, cursor, flags)
            if found_cursor.isNull():
                break
                
            found_cursor.insertText(replace_text)
            cursor = found_cursor
            count += 1
        
        cursor.endEditBlock()
        
        # Reset the last found position
        self.last_found_position = None
        
        # Report to user
        if count > 0:
            QMessageBox.information(self, "Replace All", f"Replaced {count} occurrences")
        else:
            QMessageBox.information(self, "Replace All", f"No occurrences of '{search_text}' found")
            
    def replace_text(self):
        """Replace current selection with replacement text"""
        cursor = self.text_editor.textCursor()
        if not cursor.hasSelection():
            # Find the text first if nothing is selected
            self.find_text()
            cursor = self.text_editor.textCursor()
            if not cursor.hasSelection():
                return
        
        # Replace the selected text
        replace_text = self.replace_input.text()
        cursor.insertText(replace_text)
        
        # Update the last found position
        self.last_found_position = cursor.position()
          
    def enhance_code_editor(self):
        """Add line numbers, undo/redo buttons, and save functionality to the code editor"""
        # Create a toolbar for editor actions
        editor_toolbar = QHBoxLayout()
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setIcon(QIcon.fromTheme("document-save"))
        save_btn.clicked.connect(self.save_content)
        editor_toolbar.addWidget(save_btn)
        
        # Undo button
        undo_btn = QPushButton("Undo")
        undo_btn.setIcon(QIcon.fromTheme("edit-undo"))
        undo_btn.clicked.connect(self.text_editor.undo)
        editor_toolbar.addWidget(undo_btn)
        
        # Redo button
        redo_btn = QPushButton("Redo")
        redo_btn.setIcon(QIcon.fromTheme("edit-redo"))
        redo_btn.clicked.connect(self.text_editor.redo)
        editor_toolbar.addWidget(redo_btn)
        
        # Add spacer to push remaining items to the right
        editor_toolbar.addStretch()
        
        # Toggle line numbers checkbox
        line_numbers_cb = QCheckBox("Line Numbers")
        line_numbers_cb.setChecked(True)
        line_numbers_cb.stateChanged.connect(self.toggle_line_numbers)
        editor_toolbar.addWidget(line_numbers_cb)
        
        # Add the toolbar to the main layout before the text editor
        self.layout().insertLayout(0, editor_toolbar)
        
        # Set up line numbers
        self.setup_line_numbers()

    def setup_line_numbers(self):
        """Set up line numbers for the code editor"""
        # Create a line number area
        self.line_number_area = QTextEdit()
        self.line_number_area.setReadOnly(True)
        self.line_number_area.setMaximumWidth(50)
        self.line_number_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Replace the text editor with a horizontal layout containing both
        editor_layout = QHBoxLayout()
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.line_number_area)
        
        # Remove the text editor from the layout and add it to the horizontal layout
        self.layout().removeWidget(self.text_editor)
        editor_layout.addWidget(self.text_editor)
        
        # Add the horizontal layout to the main layout
        self.layout().insertLayout(1, editor_layout)
        
        # Connect text changes to update line numbers
        self.text_editor.textChanged.connect(self.update_line_numbers)
        self.text_editor.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        
        # Initial update
        self.update_line_numbers()

    def update_line_numbers(self):
        """Update line numbers based on the current text"""
        if not hasattr(self, 'line_number_area'):
            return
            
        # Get the current text
        text = self.text_editor.toPlainText()
        lines = text.count('\n') + 1
        
        # Generate line number text
        line_numbers = '\n'.join(str(i) for i in range(1, lines + 1))
        
        # Update the line number area
        self.line_number_area.setText(line_numbers)
        
        # Sync the scroll position
        self.sync_scroll()

    def sync_scroll(self):
        """Synchronize scrolling between the text editor and line number area"""
        if not hasattr(self, 'line_number_area'):
            return
            
        # Get the vertical scroll bar value of the text editor
        value = self.text_editor.verticalScrollBar().value()
        
        # Set the same value to the line number area's vertical scroll bar
        self.line_number_area.verticalScrollBar().setValue(value)

    def toggle_line_numbers(self, state):
        """Toggle line numbers visibility"""
        if hasattr(self, 'line_number_area'):
            self.line_number_area.setVisible(state == Qt.CheckState.Checked.value)
    
    def save_content(self):
        """Save the current content"""
        # Check if we have an active component to save to
        if hasattr(self, 'active_component') and self.active_component:
            try:
                # Get the current content
                content = self.get_content()
                
                # Save to the component
                self.active_component.save_content(content)
                
                # Signal success
                if hasattr(self, 'parent_window') and self.parent_window:
                    self.parent_window.log(f"Saved component: {self.active_component.name}", "success")
                return True
            except Exception as e:
                # Handle error
                if hasattr(self, 'parent_window') and self.parent_window:
                    self.parent_window.log(f"Error saving component: {str(e)}", "error")
                return False
        else:
            # No active component
            return False 
    
    def set_content(self, content: str):
        """Set editor content"""
        self.text_editor.setPlainText(content)
    
    def get_content(self) -> str:
        """Get editor content"""
        return self.text_editor.toPlainText()

# Optional: Main window for standalone testing
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Editor")
        
        # Create central widget and code editor
        central_widget = CodeEditorWidget()
        self.setCentralWidget(central_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())