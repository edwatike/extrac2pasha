import os
from typing import Optional
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Загружаем переменные окружения из .env файла
        load_dotenv()
        
        # Прокси
        self.use_proxy = self._get_bool('USE_PROXY', False)
        self.proxy_type = os.getenv('PROXY_TYPE', 'http')
        self.proxy_host = os.getenv('PROXY_HOST')
        self.proxy_port = os.getenv('PROXY_PORT')
        self.proxy_username = os.getenv('PROXY_USERNAME')
        self.proxy_password = os.getenv('PROXY_PASSWORD')
        
        # Tor
        self.use_tor = self._get_bool('USE_TOR', False)
        self.tor_control_port = int(os.getenv('TOR_CONTROL_PORT', '9051'))
        self.tor_password = os.getenv('TOR_PASSWORD')
        
        # Браузер
        self.browser_type = os.getenv('BROWSER_TYPE', 'chrome')
        self.headless = self._get_bool('HEADLESS', True)
        self.user_agent = os.getenv('USER_AGENT')
        
        # Таймауты и задержки
        self.page_load_timeout = int(os.getenv('PAGE_LOAD_TIMEOUT', '30'))
        self.javascript_timeout = int(os.getenv('JAVASCRIPT_TIMEOUT', '10'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        # Пути к драйверам
        self.chrome_driver_path = os.getenv('CHROME_DRIVER_PATH', '/usr/bin/chromedriver')
        self.chrome_binary_path = os.getenv('CHROME_BINARY_PATH', '/usr/bin/chromium-browser')
        
        # Логирование
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/parser.log')
        self.save_html = self._get_bool('SAVE_HTML', True)
        self.html_storage = os.getenv('HTML_STORAGE', 'logs/html')
        
        # Создаем директории для логов и HTML
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if self.save_html:
            os.makedirs(self.html_storage, exist_ok=True)
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Получает булево значение из переменной окружения"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'y', 'on')
    
    def get_proxy_url(self) -> Optional[str]:
        """Возвращает URL прокси в формате protocol://user:pass@host:port"""
        if not self.use_proxy or not self.proxy_host or not self.proxy_port:
            return None
            
        auth = ''
        if self.proxy_username and self.proxy_password:
            auth = f'{self.proxy_username}:{self.proxy_password}@'
            
        return f'{self.proxy_type}://{auth}{self.proxy_host}:{self.proxy_port}'

# Создаем глобальный экземпляр конфигурации
config = Config() 