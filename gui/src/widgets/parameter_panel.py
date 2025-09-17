"""
Parameter Panel Widget - Reusable parameter configuration widget.
Provides consistent parameter interface across different applications.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional


class ParameterGroup:
    """Represents a group of related parameters."""
    
    def __init__(self, name: str, parameters: Dict[str, Dict]):
        self.name = name
        self.parameters = parameters  # {param_name: {type, default, range, units, description}}
        self.widgets = {}  # {param_name: widget}
        self.variables = {}  # {param_name: StringVar}
        

class ParameterPanel:
    """Reusable parameter configuration panel."""
    
    def __init__(self, parent, title="Parameters"):
        self.parent = parent
        self.title = title
        self.groups = {}  # {group_name: ParameterGroup}
        self.send_callback = None
        self.update_callback = None
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text=title)
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Action buttons frame
        self.action_frame = ttk.Frame(self.frame)
        self.action_frame.pack(fill='x', padx=5, pady=5)
        
        # Standard action buttons
        ttk.Button(self.action_frame, text="Get All", 
                  command=self._get_all_parameters).pack(side='left', padx=2)
        ttk.Button(self.action_frame, text="Reset All", 
                  command=self._reset_all_parameters).pack(side='left', padx=2)
        ttk.Button(self.action_frame, text="Save Profile", 
                  command=self._save_profile).pack(side='right', padx=2)
        ttk.Button(self.action_frame, text="Load Profile", 
                  command=self._load_profile).pack(side='right', padx=2)
                  
    def add_parameter_group(self, group_name: str, parameters: Dict[str, Dict]):
        """Add a group of parameters to the panel."""
        group = ParameterGroup(group_name, parameters)
        self.groups[group_name] = group
        
        # Create tab for this group
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=group_name)
        
        # Create scrollable frame for parameters
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create parameter widgets
        row = 0
        for param_name, param_info in parameters.items():
            self._create_parameter_widget(scrollable_frame, group, param_name, param_info, row)
            row += 1
            
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def _create_parameter_widget(self, parent, group, param_name, param_info, row):
        """Create widget for a single parameter."""
        # Parameter label with description tooltip
        label_text = f"{param_info.get('display_name', param_name)}:"
        if 'units' in param_info:
            label_text += f" ({param_info['units']})"
            
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
        
        # Add tooltip if description exists
        if 'description' in param_info:
            self._add_tooltip(label, param_info['description'])
            
        # Create appropriate widget based on parameter type
        param_type = param_info.get('type', 'float')
        
        if param_type == 'choice':
            # Combobox for choices
            var = tk.StringVar(value=str(param_info.get('default', '')))
            widget = ttk.Combobox(parent, textvariable=var, 
                                values=param_info.get('choices', []),
                                state='readonly', width=15)
        elif param_type == 'bool':
            # Checkbox for boolean
            var = tk.BooleanVar(value=param_info.get('default', False))
            widget = ttk.Checkbutton(parent, variable=var)
        else:
            # Entry for numeric values
            var = tk.StringVar(value=str(param_info.get('default', '')))
            widget = ttk.Entry(parent, textvariable=var, width=15)
            
        widget.grid(row=row, column=1, padx=5, pady=2)
        
        # Set button
        set_btn = ttk.Button(parent, text="Set", width=5,
                           command=lambda: self._set_parameter(group.name, param_name))
        set_btn.grid(row=row, column=2, padx=5, pady=2)
        
        # Store references
        group.widgets[param_name] = widget
        group.variables[param_name] = var
        
        # Add validation if range is specified
        if 'range' in param_info:
            self._add_validation(widget, var, param_info['range'], param_type)
            
    def _add_tooltip(self, widget, text):
        """Add tooltip to widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def _add_validation(self, widget, var, range_spec, param_type):
        """Add validation to parameter entry."""
        def validate():
            try:
                value = var.get()
                if param_type == 'int':
                    num_val = int(value)
                elif param_type == 'float':
                    num_val = float(value)
                else:
                    return True
                    
                min_val, max_val = range_spec
                if min_val <= num_val <= max_val:
                    widget.config(background="white")
                    return True
                else:
                    widget.config(background="lightyellow")
                    return False
            except ValueError:
                widget.config(background="lightcoral")
                return False
                
        var.trace('w', lambda *args: validate())
        
    def _set_parameter(self, group_name, param_name):
        """Send parameter set command."""
        if not self.send_callback:
            messagebox.showwarning("No Connection", "Please connect to device first")
            return
            
        group = self.groups[group_name]
        value = group.variables[param_name].get()
        
        # Validate the value
        param_info = group.parameters[param_name]
        if not self._validate_parameter_value(value, param_info):
            messagebox.showerror("Invalid Value", 
                               f"Invalid value for {param_name}: {value}")
            return
            
        # Send command
        command = f"SET {param_name.upper()} {value}"
        self.send_callback(command)
        
    def _validate_parameter_value(self, value, param_info):
        """Validate parameter value against constraints."""
        try:
            param_type = param_info.get('type', 'float')
            
            if param_type == 'int':
                num_val = int(value)
            elif param_type == 'float':
                num_val = float(value)
            elif param_type == 'choice':
                return value in param_info.get('choices', [])
            elif param_type == 'bool':
                return isinstance(value, bool)
            else:
                return True
                
            # Check range if specified
            if 'range' in param_info:
                min_val, max_val = param_info['range']
                return min_val <= num_val <= max_val
                
            return True
        except ValueError:
            return False
            
    def update_parameter_value(self, group_name, param_name, value):
        """Update parameter value from external source."""
        if group_name in self.groups and param_name in self.groups[group_name].variables:
            self.groups[group_name].variables[param_name].set(str(value))
            if self.update_callback:
                self.update_callback(group_name, param_name, value)
                
    def get_parameter_value(self, group_name, param_name):
        """Get current parameter value."""
        if group_name in self.groups and param_name in self.groups[group_name].variables:
            return self.groups[group_name].variables[param_name].get()
        return None
        
    def _get_all_parameters(self):
        """Get all parameters from device."""
        if self.send_callback:
            self.send_callback("GET ALL")
            
    def _reset_all_parameters(self):
        """Reset all parameters to defaults."""
        if messagebox.askyesno("Reset Parameters", 
                              "Reset all parameters to factory defaults?"):
            if self.send_callback:
                self.send_callback("RESET ALL")
                
    def _save_profile(self):
        """Save current parameters as profile."""
        # TODO: Implement profile saving
        messagebox.showinfo("Save Profile", "Profile saving not yet implemented")
        
    def _load_profile(self):
        """Load parameter profile.""" 
        # TODO: Implement profile loading
        messagebox.showinfo("Load Profile", "Profile loading not yet implemented")
        
    def set_send_callback(self, callback):
        """Set callback for sending commands."""
        self.send_callback = callback
        
    def set_update_callback(self, callback):
        """Set callback for parameter updates."""
        self.update_callback = callback
        
    def pack(self, **kwargs):
        """Pack the parameter panel frame."""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the parameter panel frame."""
        self.frame.grid(**kwargs)