"""
Component module for managing TSX components
"""
import os
import re
import logging
import shutil
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

logger = logging.getLogger(__name__)

@dataclass
class Component:
    """Class representing a TSX component"""
    filepath: str
    name: str = field(init=False)
    content: str = field(default=None)
    
    def __post_init__(self):
        """Initialize the component name from the filepath"""
        self.name = os.path.splitext(os.path.basename(self.filepath))[0]
        if self.content is None:
            self.load_content()
    
    @property
    def display_name(self) -> str:
        """Get the display name for the component"""
        return f"{self.name} ({os.path.basename(self.filepath)})"
    
    @property
    def extension(self) -> str:
        """Get the file extension"""
        _, ext = os.path.splitext(self.filepath)
        return ext
    
    def load_content(self) -> str:
        """Load the component content from file"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return self.content
        except Exception as e:
            logger.error(f"Error loading component {self.name}: {e}")
            raise IOError(f"Failed to load component: {e}")
    
    # Add this method to match the expected interface
    def read_content(self) -> str:
        """Read the component content from file (alias for load_content)"""
        return self.load_content() if self.content is None else self.content
    
    def save_content(self, content: Optional[str] = None) -> bool:
        """Save content to the component file"""
        if content is not None:
            self.content = content
            
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(self.content)
            return True
        except Exception as e:
            logger.error(f"Error saving component {self.name}: {e}")
            raise IOError(f"Failed to save component: {e}")
    
    def rename(self, new_name: str) -> str:
        """
        Rename the component and its references in the file
        
        Args:
            new_name: The new component name
            
        Returns:
            The old filepath (useful if you want to delete it)
        """
        # Create new file path
        dir_path = os.path.dirname(self.filepath)
        new_filename = f"{new_name}{self.extension}"
        new_filepath = os.path.join(dir_path, new_filename)
        
        # Check if file exists
        if os.path.exists(new_filepath) and os.path.realpath(new_filepath) != os.path.realpath(self.filepath):
            raise FileExistsError(f"A file named {new_filename} already exists")
        
        # Update references in content
        self.update_component_references(new_name)
        
        # Save to new path if different
        old_filepath = self.filepath
        if new_filepath != self.filepath:
            # Create new file
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(self.content)
                
            # Update component info
            self.filepath = new_filepath
        else:
            # Just save the updated content
            self.save_content()
            
        # Update name
        self.name = new_name
        
        return old_filepath
    
    def duplicate(self, new_name: str) -> 'Component':
        """
        Create a duplicate of this component with a new name
        
        Args:
            new_name: The name for the new component
            
        Returns:
            A new Component instance
        """
        # Create new file path
        dir_path = os.path.dirname(self.filepath)
        new_filename = f"{new_name}{self.extension}"
        new_filepath = os.path.join(dir_path, new_filename)
        
        # Check if file exists
        if os.path.exists(new_filepath):
            raise FileExistsError(f"A file named {new_filename} already exists")
        
        # Create a copy of the content with updated references
        content_copy = self.content
        
        # Update component name in content
        for pattern, replacement in [
            (f"const {self.name}", f"const {new_name}"),
            (f"function {self.name}", f"function {new_name}"),
            (f"class {self.name}", f"class {new_name}"),
            (f"export default {self.name}", f"export default {new_name}"),
            (f"const {self.name} = ", f"const {new_name} = "),
            (f"let {self.name} = ", f"let {new_name} = "),
            (f"var {self.name} = ", f"var {new_name} = ")
        ]:
            if re.search(r'\b' + re.escape(pattern) + r'\b', content_copy):
                content_copy = re.sub(r'\b' + re.escape(pattern) + r'\b', replacement, content_copy)
        
        # Write to new file
        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(content_copy)
        
        # Create and return a new component
        return Component(new_filepath)
    
    def update_component_references(self, new_name: str) -> None:
        """
        Update references to the component name in the content
        
        Args:
            new_name: The new component name
        """
        # Patterns for common component declarations
        for pattern, replacement in [
            (f"const {self.name}", f"const {new_name}"),
            (f"function {self.name}", f"function {new_name}"),
            (f"class {self.name}", f"class {new_name}"),
            (f"export default {self.name}", f"export default {new_name}"),
            (f"const {self.name} = ", f"const {new_name} = "),
            (f"let {self.name} = ", f"let {new_name} = "),
            (f"var {self.name} = ", f"var {new_name} = ")
        ]:
            if re.search(r'\b' + re.escape(pattern) + r'\b', self.content):
                self.content = re.sub(r'\b' + re.escape(pattern) + r'\b', replacement, self.content)
    
    def get_dependencies(self) -> Set[str]:
        """
        Extract dependencies from the component
        
        Returns:
            Set of dependency package names
        """
        # Regular expression to match import statements
        import_pattern = r"import\s+(?:{[^}]*}|\*\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)\s+from\s+['\"]([^'\"]+)['\"]"
        matches = re.findall(import_pattern, self.content)
        
        # Filter out relative imports and React core packages
        external_packages = set()
        for match in matches:
            if not match.startswith('.') and match not in ['react', 'react-dom']:
                # Extract the package name (before any slash)
                package_name = match.split('/')[0]
                external_packages.add(package_name)
        
        # Special handling for lucide-react which is used in many components
        if 'lucide-react' not in external_packages and any(icon in self.content for icon in 
                                                      ['Server', 'Database', 'Globe', 'Users', 
                                                      'Network', 'Shield', 'Activity']):
            external_packages.add('lucide-react')
        
        return external_packages
    
    def prettify(self) -> None:
        """
        Format the component code using a simple prettifier
        """
        # For production, you would use a proper formatter like prettier
        # This is a very simple placeholder implementation
        lines = self.content.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            # Trim trailing whitespace
            trimmed = line.rstrip()
            
            # Skip empty lines
            if not trimmed:
                formatted_lines.append('')
                continue
                
            # Adjust indent for closing brackets
            if any(c in trimmed for c in [')', '}', ']']):
                if not any(c in trimmed for c in ['(', '{', '[']):
                    indent_level = max(0, indent_level - 1)
            
            # Add the line with proper indentation
            formatted_lines.append('  ' * indent_level + trimmed)
            
            # Adjust indent for opening brackets
            if any(c in trimmed for c in ['(', '{', '[']):
                if not any(c in trimmed for c in [')', '}', ']']):
                    indent_level += 1
        
        self.content = '\n'.join(formatted_lines)
        

class ComponentManager:
    """Class for managing multiple components"""
    def __init__(self):
        self.components: List[Component] = []
    
    def add_component(self, filepath: str) -> Component:
        """
        Add a component from a file
        
        Args:
            filepath: Path to the component file
            
        Returns:
            The added Component instance
        """
        # Check if component is already added
        for component in self.components:
            if os.path.samefile(component.filepath, filepath):
                return component
        
        # Create new component
        component = Component(filepath)
        self.components.append(component)
        return component
    
    def remove_component(self, component: Component) -> None:
        """
        Remove a component from the manager
        
        Args:
            component: The component to remove
        """
        if component in self.components:
            self.components.remove(component)
    
    def get_component_by_index(self, index: int) -> Optional[Component]:
        """
        Get a component by its index
        
        Args:
            index: The index of the component
            
        Returns:
            The Component instance or None if not found
        """
        if 0 <= index < len(self.components):
            return self.components[index]
        return None
    
    def get_all_dependencies(self) -> Dict[str, Set[str]]:
        """
        Get all dependencies from all components
        
        Returns:
            Dictionary mapping component names to their dependencies
        """
        dependencies = {}
        for component in self.components:
            dependencies[component.name] = component.get_dependencies()
        return dependencies
    
    def clear(self) -> None:
        """Clear all components"""
        self.components = []