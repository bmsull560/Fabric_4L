"""Plugin loader for gate plugins."""

import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Type

from sdk.plugin import GatePlugin


class PluginLoader:
    """Loads gate plugins from filesystem paths."""
    
    def __init__(self, search_paths: list[str]):
        self.search_paths = search_paths
        self.logger = logging.getLogger("gated.loader")
    
    def discover_plugins(self) -> list[Type[GatePlugin]]:
        """Discover all plugin classes in search paths."""
        plugins = []
        
        for search_path in self.search_paths:
            # Expand wildcards
            if "*" in search_path:
                base_path = Path(search_path.split("*")[0])
                pattern = search_path.split("*")[-1] if "*" in search_path else "*.py"
                paths = list(base_path.glob(f"**/{pattern}"))
            else:
                paths = list(Path(search_path).glob("*.py"))
            
            for path in paths:
                if path.name.startswith("_"):
                    continue
                
                try:
                    plugin_classes = self._load_plugin_from_file(path)
                    plugins.extend(plugin_classes)
                except Exception as e:
                    self.logger.warning(f"Failed to load plugin from {path}: {e}")
        
        return plugins
    
    def _load_plugin_from_file(self, path: Path) -> list[Type[GatePlugin]]:
        """Load plugin classes from a Python file."""
        plugins = []
        
        # Create module spec
        spec = importlib.util.spec_from_file_location(
            f"_plugin_{path.stem}",
            path
        )
        if not spec or not spec.loader:
            return plugins
        
        # Load module
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        
        # Find GatePlugin subclasses
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, GatePlugin) and 
                obj is not GatePlugin and
                not getattr(obj, "__abstractmethods__", None)):
                plugins.append(obj)
                self.logger.debug(f"Found plugin class: {name} in {path}")
        
        return plugins
    
    def load_all(self) -> list[GatePlugin]:
        """Load and instantiate all plugins."""
        classes = self.discover_plugins()
        instances = []
        
        for cls in classes:
            try:
                instance = cls()
                instances.append(instance)
                self.logger.info(f"Loaded plugin: {instance.gate_id}")
            except Exception as e:
                self.logger.error(f"Failed to instantiate {cls.__name__}: {e}")
        
        return instances
