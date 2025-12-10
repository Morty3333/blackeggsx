"""
Модуль для запуска и управления процессом Xray
"""
import subprocess
import os
import sys
import platform
import shutil
from pathlib import Path
import json


class XrayRunner:
    """Управление процессом Xray"""
    
    def __init__(self, xray_path: str = None):
        """
        Инициализация XrayRunner
        
        Args:
            xray_path: Путь к исполняемому файлу Xray. Если None, будет искаться автоматически
        """
        self.xray_path = xray_path or self._find_xray()
        self.process = None
        self.config_path = 'config.json'
    
    def _find_xray(self) -> str:
        """Ищет исполняемый файл Xray"""
        current_dir = Path.cwd()
        possible_names = ['xray.exe', 'xray', 'v2ray.exe', 'v2ray']
        
        # Сначала проверяем папку bit/ (приоритет)
        bit_dir = current_dir / 'bit'
        if bit_dir.exists() and bit_dir.is_dir():
            for name in possible_names:
                path = bit_dir / name
                if path.exists() and path.is_file():
                    return str(path)
        
        # Затем проверяем текущую директорию
        for name in possible_names:
            path = current_dir / name
            if path.exists() and path.is_file():
                return str(path)
        
        # Проверяем PATH
        xray_exe = shutil.which('xray') or shutil.which('xray.exe') or \
                   shutil.which('v2ray') or shutil.which('v2ray.exe')
        
        if xray_exe and os.path.exists(xray_exe):
            return xray_exe
        
        # Если не найден, возвращаем стандартное имя (в папке bit)
        # Это будет использовано для показа сообщения об ошибке
        if platform.system() == 'Windows':
            if bit_dir.exists():
                return str(bit_dir / 'xray.exe')
            else:
                return 'bit/xray.exe'
        else:
            if bit_dir.exists():
                return str(bit_dir / 'xray')
            else:
                return 'bit/xray'
    
    def start(self, config_path: str = 'config.json') -> bool:
        """
        Запускает Xray с указанной конфигурацией
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            True если процесс запущен успешно
        """
        if not os.path.exists(config_path):
            print(f"✗ Файл конфигурации не найден: {config_path}")
            return False
        
        # Проверяем существование xray.exe
        xray_path_obj = Path(self.xray_path)
        bit_dir = Path.cwd() / 'bit'
        
        if not xray_path_obj.exists() or not xray_path_obj.is_file():
            print(f"✗ Xray не найден: {self.xray_path}")
            
            # Дополнительная диагностика
            print("\nДиагностика:")
            if not bit_dir.exists():
                print(f"  ✗ Папка 'bit' не существует: {os.path.abspath('bit')}")
            elif not bit_dir.is_dir():
                print(f"  ✗ 'bit' существует, но это не папка")
            else:
                print(f"  ✓ Папка 'bit' существует: {os.path.abspath('bit')}")
                # Проверяем содержимое папки
                files_in_bit = list(bit_dir.iterdir())
                if files_in_bit:
                    print(f"  Файлы в папке bit:")
                    for f in files_in_bit[:5]:  # Показываем первые 5 файлов
                        print(f"    - {f.name}")
                    if len(files_in_bit) > 5:
                        print(f"    ... и еще {len(files_in_bit) - 5} файлов")
                else:
                    print(f"  ✗ Папка 'bit' пуста")
            
            print("\n" + "=" * 60)
            print("Инструкция по установке Xray:")
            print("=" * 60)
            print("1. Перейдите на: https://github.com/XTLS/Xray-core/releases")
            print("2. Скачайте последнюю версию для Windows (xray-windows-64.zip)")
            print("3. Распакуйте архив")
            if not bit_dir.exists():
                print("4. Создайте папку 'bit' в директории проекта")
            bit_path = os.path.abspath('bit')
            print(f"5. Скопируйте xray.exe и ВСЕ файлы из архива в папку:")
            print(f"   {bit_path}")
            print("\nВажно: Нужны ВСЕ файлы из архива, не только xray.exe!")
            print("       Обычно в архиве есть: xray.exe, geoip.dat, geosite.dat и другие")
            print("=" * 60)
            return False
        
        try:
            # Сначала проверяем конфигурацию
            config_path_abs = os.path.abspath(config_path)
            try:
                with open(config_path_abs, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"✗ Ошибка в конфигурации JSON: {e}")
                return False
            except FileNotFoundError:
                print(f"✗ Файл конфигурации не найден: {config_path_abs}")
                return False
            except Exception as e:
                print(f"✗ Ошибка чтения конфигурации: {e}")
                return False
            
            # Получаем абсолютный путь к xray.exe
            xray_path_abs = os.path.abspath(self.xray_path)
            xray_dir = os.path.dirname(xray_path_abs)
            
            # Запускаем процесс в фоне
            # Используем абсолютный путь к config.json, чтобы Xray мог его найти
            self.process = subprocess.Popen(
                [xray_path_abs, '-config', config_path_abs],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=xray_dir,  # Запускаем из папки bit для доступа к geoip.dat и geosite.dat
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            # Проверяем, что процесс запустился
            import time
            time.sleep(1.0)  # Увеличиваем время ожидания
            
            if self.process.poll() is None:
                print(f"✓ Xray запущен (PID: {self.process.pid})")
                print(f"  Конфигурация: {config_path}")
                return True
            else:
                # Процесс завершился, получаем вывод ошибок
                stdout, stderr = self.process.communicate()
                print(f"✗ Xray завершился с ошибкой (код: {self.process.returncode})")
                
                # Показываем ошибки
                error_output = ""
                if stderr:
                    error_output = stderr.decode('utf-8', errors='ignore').strip()
                if stdout:
                    stdout_text = stdout.decode('utf-8', errors='ignore').strip()
                    if stdout_text:
                        error_output += "\n" + stdout_text if error_output else stdout_text
                
                if error_output:
                    print("\nДетали ошибки:")
                    print("=" * 60)
                    # Показываем только первые строки ошибки
                    error_lines = error_output.split('\n')[:10]
                    for line in error_lines:
                        print(f"  {line}")
                    if len(error_output.split('\n')) > 10:
                        print(f"  ... (еще {len(error_output.split('\n')) - 10} строк)")
                    print("=" * 60)
                    
                    # Проверяем типичные ошибки
                    error_lower = error_output.lower()
                    if 'geoip' in error_lower or 'geosite' in error_lower:
                        print("\n⚠ Возможная проблема: отсутствуют файлы geoip.dat или geosite.dat")
                        print("  Убедитесь, что ВСЕ файлы из архива Xray скопированы в папку bit/")
                    elif 'config' in error_lower or 'json' in error_lower:
                        print("\n⚠ Возможная проблема: ошибка в конфигурации")
                        print(f"  Проверьте файл: {os.path.abspath(config_path)}")
                    elif 'permission' in error_lower or 'доступ' in error_lower:
                        print("\n⚠ Возможная проблема: недостаточно прав")
                        print("  Попробуйте запустить от имени администратора")
                else:
                    print("  (Детали ошибки недоступны)")
                
                return False
                
        except FileNotFoundError:
            print(f"✗ Xray не найден: {self.xray_path}")
            print("  Убедитесь, что файл существует и доступен для запуска")
            return False
        except PermissionError:
            print(f"✗ Нет прав для запуска Xray")
            print("  Попробуйте запустить программу от имени администратора")
            return False
        except Exception as e:
            print(f"✗ Ошибка запуска Xray: {e}")
            print(f"  Тип ошибки: {type(e).__name__}")
            return False
    
    def stop(self) -> bool:
        """Останавливает процесс Xray"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("✓ Xray остановлен")
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("✓ Xray принудительно остановлен")
                return True
            except Exception as e:
                print(f"✗ Ошибка остановки Xray: {e}")
                return False
        return True
    
    def is_running(self) -> bool:
        """Проверяет, запущен ли процесс Xray"""
        if self.process:
            return self.process.poll() is None
        return False
    
    def get_status(self) -> dict:
        """Возвращает статус процесса"""
        return {
            'running': self.is_running(),
            'pid': self.process.pid if self.process and self.is_running() else None,
            'xray_path': self.xray_path,
            'config_path': self.config_path
        }

