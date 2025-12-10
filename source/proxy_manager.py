"""
Модуль для управления системным прокси Windows
"""
import subprocess
import ctypes
from ctypes import wintypes
import sys


class WindowsProxyManager:
    """Управление системным прокси Windows"""
    
    # Windows API константы
    INTERNET_OPTION_PROXY = 38
    INTERNET_OPEN_TYPE_PROXY = 3
    INTERNET_OPEN_TYPE_DIRECT = 1
    
    def __init__(self):
        self.wininet = ctypes.windll.wininet
        self.original_proxy_enabled = None
        self.original_proxy_server = None
    
    def set_proxy(self, host: str = '127.0.0.1', port: int = 10808):
        """
        Устанавливает системный прокси через Windows API
        
        Args:
            host: Адрес прокси сервера
            port: Порт прокси сервера
        """
        proxy_string = f"{host}:{port}"
        
        # Сохраняем текущие настройки
        self._save_current_settings()
        
        # Устанавливаем прокси через netsh (более надежный способ)
        try:
            subprocess.run(
                ['netsh', 'winhttp', 'set', 'proxy', proxy_string],
                check=True,
                capture_output=True
            )
            print(f"✓ Системный прокси установлен: {proxy_string}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка установки прокси через netsh: {e}")
            return False
    
    def remove_proxy(self):
        """Удаляет системный прокси"""
        try:
            subprocess.run(
                ['netsh', 'winhttp', 'reset', 'proxy'],
                check=True,
                capture_output=True
            )
            print("✓ Системный прокси удален")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка удаления прокси: {e}")
            return False
    
    def _save_current_settings(self):
        """Сохраняет текущие настройки прокси"""
        try:
            result = subprocess.run(
                ['netsh', 'winhttp', 'show', 'proxy'],
                capture_output=True,
                text=True
            )
            if 'Direct access' not in result.stdout:
                # Пытаемся извлечь текущие настройки
                self.original_proxy_server = result.stdout.strip()
        except:
            pass
    
    def get_current_proxy(self):
        """Получает текущие настройки прокси"""
        try:
            result = subprocess.run(
                ['netsh', 'winhttp', 'show', 'proxy'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return None
    
    @staticmethod
    def set_proxy_via_registry(host: str = '127.0.0.1', port: int = 10808, enable: bool = True):
        """
        Альтернативный метод установки прокси через реестр
        Используется как резервный вариант
        """
        import winreg
        
        proxy_string = f"{host}:{port}"
        
        try:
            # Открываем ключ реестра
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_WRITE
            )
            
            # Устанавливаем прокси сервер
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_string)
            
            # Включаем прокси
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enable else 0)
            
            # Закрываем ключ
            winreg.CloseKey(key)
            
            # Уведомляем систему об изменении
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
            
            return True
        except Exception as e:
            print(f"✗ Ошибка установки прокси через реестр: {e}")
            return False



