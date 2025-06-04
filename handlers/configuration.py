import os
import yaml
from colorama import Fore, Style
from urllib.parse import urlparse
from dotenv import load_dotenv

class Configuration:
    def __init__(self):
        print(f"{Fore.CYAN}[PSS] {Fore.YELLOW}Loading configuration...")
        
        # Load environment variables
        load_dotenv()
        
        # Load main config
        config_file = "config.yml"
        if os.path.exists("config-dev.yml"):
            print(f"{Fore.CYAN}[PSS] {Fore.YELLOW}Using development configuration...")
            config_file = "config-dev.yml"
        
        with open(config_file, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Validate configuration
        self._validate_config()
        
        print(f"{Fore.CYAN}[PSS] {Fore.YELLOW}Configuration loaded")
    
    def _validate_config(self):
        """Validate configuration settings"""
        # Validate Panel URL
        panel_url = os.getenv('PanelURL')
        if panel_url:
            try:
                parsed_url = urlparse(panel_url)
                if not parsed_url.scheme.startswith('http'):
                    raise ValueError("Invalid URL scheme")
            except Exception:
                print('Config Error | Invalid URL Format! Example Correct URL: "https://panel.example.com"')
                exit(1)
        
        # Validate config version
        if self.config.get('version') != 1:
            print('Config Error | Invalid config version! The config has been updated. Please get the new config format from: \n>> https://github.com/HirziDevs/PteroServerStats/blob/main/config.yml <<')
            exit(1)
    
    def get(self, key, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def __getattr__(self, name):
        """Allow direct attribute access to config"""
        if name in self.config:
            return self.config[name]
        raise AttributeError(f"'Configuration' object has no attribute '{name}'") 