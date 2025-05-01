"""
Component list module for managing TSX components
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import List, Optional, Tuple, Callable
import logging

from core.component import Component, ComponentManager

logger = logging.getLogger(__name__)

class ComponentListFrame(ttk.LabelFrame):
    """Frame containing the list of loaded components"""
    
    def __init__(self, parent, app, **kwargs):
        """Initialize the component list frame"""
        super().__init__(parent, text="Components", **kwargs)
        self.app = app
        self.component_manager = ComponentManager()
        
        self.pack(fill=tk.X, pady=(0, 10))
        
        # Create main layout
        self.create_list_view()
        self.create_button_bar()
        
        # Right-click menu
        self.create_context_menu()
    
    def create_list_view(self):
        """Create the component list view with scrollbars"""
        # Create a frame for the list and scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Create the listbox
        self.listbox = tk.Listbox(
            list_frame, 
            height=6, 
            font=("Helvetica", 10),
            selectmode=tk.SINGLE,
            activestyle='dotbox'
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.listbox.bind("<<ListboxSelect>>", self.on_component_selected)
        self.listbox.bind("<Double-1>", self.on_component_double_click)
        self.listbox.bind("<Button-3>", self.show_context_menu)  # Right-click
    
    def create_button_bar(self):
        """Create the button bar for component operations"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add button
        ttk.Button(
            button_frame, text="Add", command=self.add_component, width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # Remove button
        ttk.Button(
            button_frame, text="Remove", command=self.remove_component, width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # Edit button
        ttk.Button(
            button_frame, text="Edit", command=self.edit_component, width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # Rename button
        ttk.Button(
            button_frame, text="Rename", command=self.rename_component, width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # Duplicate button
        ttk.Button(
            button_frame, text="Duplicate", command=self.duplicate_component, width=8
        ).pack(side=tk.LEFT, padx=2)
        
        # Clear all button
        ttk.Button(
            button_frame, text="Clear All", command=self.clear_components, width=8
        ).pack(side=tk.LEFT, padx=2)
    
    def create_context_menu(self):
        """Create the right-click context menu"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_component)
        self.context_menu.add_command(label="Rename", command=self.rename_component)
        self.context_menu.add_command(label="Duplicate", command=self.duplicate_component)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove", command=self.remove_component)
    
    def show_context_menu(self, event):
        """Show the context menu on right-click"""
        try:
            # Select the item under the mouse
            index = self.listbox.nearest(event.y)
            if index >= 0:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                self.listbox.activate(index)
                # Show the menu
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure to release the grab
            self.context_menu.grab_release()
    
    def add_component(self):
        """Add a new component from file"""
        filetypes = [
            ("TypeScript React Files", "*.tsx"),
            ("JavaScript React Files", "*.jsx"),
            ("All Files", "*.*")
        ]
        
        filepaths = filedialog.askopenfilenames(
            title="Select Component Files",
            filetypes=filetypes
        )
        
        if not filepaths:
            return
        
        added_count = 0
        for filepath in filepaths:
            try:
                # Check if file already added
                for component in self.component_manager.components:
                    if os.path.samefile(component.filepath, filepath):
                        self.app.log(f"Component {component.name} is already in the list")
                        continue
                
                # Add the component
                component = self.component_manager.add_component(filepath)
                self.listbox.insert(tk.END, component.display_name)
                added_count += 1
                
                self.app.log(f"Added component: {component.name}")
            except Exception as e:
                logger.error(f"Error adding component {filepath}: {e}")
                self.app.log(f"Error adding component: {str(e)}")
        
        if added_count > 0:
            self.app.set_status(f"Added {added_count} component(s)")
    
    def remove_component(self):
        """Remove the selected component"""
        selected_idx = self.get_selected_index()
        if selected_idx < 0:
            messagebox.showinfo("Information", "Please select a component to remove")
            return
        
        component = self.component_manager.get_component_by_index(selected_idx)
        if component:
            if messagebox.askyesno("Confirm Remove", 
                               f"Remove component {component.name} from the list?"):
                self.component_manager.remove_component(component)
                self.listbox.delete(selected_idx)
                self.app.log(f"Removed component: {component.name}")
                self.app.set_status(f"Removed: {component.name}")
    
    def edit_component(self):
        """Edit the selected component"""
        selected_idx = self.get_selected_index()
        if selected_idx < 0:
            messagebox.showinfo("Information", "Please select a component to edit")
            return
        
        component = self.component_manager.get_component_by_index(selected_idx)
        if component:
            # Make sure component content is loaded before sending to editor
            try:
                if not hasattr(component, 'content') or component.content is None:
                    if hasattr(component, 'load_content'):
                        component.load_content()
                    elif hasattr(component, 'read_content'):
                        component.read_content()
            except Exception as e:
                self.app.log(f"Error loading component content: {str(e)}", "error")
                messagebox.showerror("Error", f"Failed to load component: {e}")
                return
                
            # Send component to code editor
            if hasattr(self.app, 'code_editor'):
                self.app.code_editor.load_component(component)
            self.app.set_status(f"Editing: {component.name}")
    
    def rename_component(self):
        """Rename the selected component"""
        selected_idx = self.get_selected_index()
        if selected_idx < 0:
            messagebox.showinfo("Information", "Please select a component to rename")
            return
        
        component = self.component_manager.get_component_by_index(selected_idx)
        if not component:
            return
        
        # Ask for a new name
        new_name = simpledialog.askstring(
            "Rename Component", 
            f"Enter new name for {component.name}:",
            initialvalue=component.name
        )
        
        if not new_name or new_name == component.name:
            return  # No change or cancelled
        
        try:
            # Rename the component (this updates both file and internal name)
            old_filepath = component.rename(new_name)
            
            # Update the listbox
            self.listbox.delete(selected_idx)
            self.listbox.insert(selected_idx, component.display_name)
            
            # If component is being edited, reload it
            if hasattr(self.app, 'code_editor') and self.app.code_editor.current_component == component:
                self.app.code_editor.load_component(component)
            
            self.app.log(f"Renamed component from {os.path.basename(old_filepath)} to {component.name}")
            self.app.set_status(f"Renamed: {component.name}")
            
            # Ask if user wants to delete the old file if it's different
            if old_filepath != component.filepath:
                if messagebox.askyesno("Delete Old File", 
                                   f"Delete the original file {os.path.basename(old_filepath)}?"):
                    try:
                        os.remove(old_filepath)
                        self.app.log(f"Deleted original file: {os.path.basename(old_filepath)}")
                    except Exception as e:
                        self.app.log(f"Error deleting original file: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error renaming component: {e}")
            messagebox.showerror("Error", f"Failed to rename component: {e}")
    
    def duplicate_component(self):
        """Duplicate the selected component"""
        selected_idx = self.get_selected_index()
        if selected_idx < 0:
            messagebox.showinfo("Information", "Please select a component to duplicate")
            return
        
        component = self.component_manager.get_component_by_index(selected_idx)
        if not component:
            return
        
        # Ask for a new name
        new_name = simpledialog.askstring(
            "Duplicate Component", 
            f"Enter name for the copy of {component.name}:",
            initialvalue=f"{component.name}_copy"
        )
        
        if not new_name:
            return  # Cancelled
        
        try:
            # Create a duplicate
            new_component = component.duplicate(new_name)
            
            # Add to component manager
            self.component_manager.components.append(new_component)
            
            # Add to listbox
            self.listbox.insert(tk.END, new_component.display_name)
            
            self.app.log(f"Duplicated component {component.name} to {new_component.name}")
            self.app.set_status(f"Duplicated: {new_component.name}")
            
        except Exception as e:
            logger.error(f"Error duplicating component: {e}")
            messagebox.showerror("Error", f"Failed to duplicate component: {e}")
    
    def clear_components(self):
        """Clear all components from the list"""
        if not self.component_manager.components:
            return
            
        if messagebox.askyesno("Clear All", 
                           "Remove all components from the list?"):
            self.component_manager.clear()
            self.listbox.delete(0, tk.END)
            self.app.log("Cleared all components")
            self.app.set_status("Cleared all components")
    
    def on_component_selected(self, event):
        """Handle component selection in the listbox"""
        selected_idx = self.get_selected_index()
        if selected_idx < 0:
            return
            
        component = self.component_manager.get_component_by_index(selected_idx)
        if component:
            # Make sure component content is loaded
            try:
                if not hasattr(component, 'content') or component.content is None:
                    if hasattr(component, 'load_content'):
                        component.load_content()
                    elif hasattr(component, 'read_content'):
                        component.read_content()
            except Exception as e:
                self.app.log(f"Error loading component content: {str(e)}", "error")
            
            self.app.set_status(f"Selected: {component.name}")
            
    def on_component_double_click(self, event):
        """Handle double-click on a component"""
        self.edit_component()
    
    def get_selected_index(self) -> int:
        """Get the index of the selected component"""
        selection = self.listbox.curselection()
        if not selection:
            return -1
        return selection[0]
    
    def get_selected_component(self) -> Optional[Component]:
        """Get the currently selected component"""
        selected_idx = self.get_selected_index()
        if selected_idx < 0:
            return None
        return self.component_manager.get_component_by_index(selected_idx)
    
    def get_components(self) -> List[Component]:
        """Get all components in the list"""
        return self.component_manager.components