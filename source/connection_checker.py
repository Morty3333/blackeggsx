"""
Модуль для проверки соединения и пинга до сервера
"""
import socket
import subprocess
import platform
import time
from typing import Tuple, Optional


class ConnectionChecker:
    """Проверка соединения с сервером"""
    
    @staticmethod
    def check_port(host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Проверяет доступность порта на сервере
        
        Args:
            host: Адрес сервера
            port: Порт для проверки
            timeout: Таймаут в секундах
            
        Returns:
            Tuple[bool, Optional[str]]: (успешно, сообщение об ошибке)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return True, None
            else:
                return False, f"Порт {port} недоступен"
        except socket.gaierror:
            return False, f"Не удалось разрешить адрес {host}"
        except socket.timeout:
            return False, f"Таймаут подключения к {host}:{port}"
        except Exception as e:
            return False, f"Ошибка подключения: {e}"
    
    @staticmethod
    def ping_host(host: str, count: int = 4, timeout: int = 3) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Проверяет пинг до сервера
        
        Args:
            host: Адрес сервера
            count: Количество пакетов
            timeout: Таймаут в секундах
            
        Returns:
            Tuple[bool, Optional[str], Optional[float]]: (успешно, сообщение, средний пинг в мс)
        """
        try:
            # Определяем команду ping в зависимости от ОС
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
            else:
                cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout * count + 2
            )
            
            if result.returncode == 0:
                # Пытаемся извлечь средний пинг из вывода
                output = result.stdout
                avg_ping = ConnectionChecker._extract_avg_ping(output, platform.system().lower() == 'windows')
                return True, None, avg_ping
            else:
                return False, f"Сервер {host} недоступен (ping failed)", None
                
        except subprocess.TimeoutExpired:
            return False, f"Таймаут проверки пинга к {host}", None
        except Exception as e:
            return False, f"Ошибка проверки пинга: {e}", None
    
    @staticmethod
    def _extract_avg_ping(output: str, is_windows: bool) -> Optional[float]:
        """Извлекает средний пинг из вывода команды ping"""
        try:
            if is_windows:
                # Windows формат: "Среднее = 45мс"
                import re
                match = re.search(r'Среднее\s*=\s*(\d+)', output, re.IGNORECASE)
                if not match:
                    match = re.search(r'Average\s*=\s*(\d+)', output, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            else:
                # Linux/Mac формат: "min/avg/max/mdev = 10.123/45.678/90.234/20.123 ms"
                import re
                match = re.search(r'min/avg/max.*?=\s*[\d.]+/([\d.]+)/', output)
                if match:
                    return float(match.group(1))
        except:
            pass
        return None
    
    @staticmethod
    def check_connection(host: str, port: int, check_ping: bool = True) -> Tuple[bool, str]:
        """
        Полная проверка соединения: порт + пинг
        
        Args:
            host: Адрес сервера
            port: Порт для проверки
            check_ping: Проверять ли пинг
            
        Returns:
            Tuple[bool, str]: (успешно, сообщение)
        """
        messages = []
        all_ok = True
        
        # Проверка порта
        print(f"  Проверка порта {port}...", end=' ', flush=True)
        try:
            port_ok, port_error = ConnectionChecker.check_port(host, port, timeout=5)
            if port_ok:
                print("✓")
                messages.append(f"Порт {port}: доступен")
            else:
                print("✗")
                messages.append(f"Порт {port}: {port_error}")
                all_ok = False
        except Exception as e:
            print("✗")
            messages.append(f"Порт {port}: ошибка проверки ({e})")
            all_ok = False
        
        # Проверка пинга
        if check_ping:
            print(f"  Проверка пинга до {host}...", end=' ', flush=True)
            try:
                ping_ok, ping_error, avg_ping = ConnectionChecker.ping_host(host, count=3, timeout=2)
                if ping_ok:
                    ping_msg = f"Пинг: доступен"
                    if avg_ping:
                        ping_msg += f" (средний: {avg_ping:.0f} мс)"
                    print("✓")
                    messages.append(ping_msg)
                else:
                    print("✗")
                    messages.append(f"Пинг: {ping_error}")
                    # Пинг не критичен, не делаем all_ok = False
            except Exception as e:
                print("✗")
                messages.append(f"Пинг: ошибка проверки ({e})")
                # Пинг не критичен
        
        status_msg = " | ".join(messages)
        
        if all_ok:
            return True, f"Соединение успешно: {status_msg}"
        else:
            return False, f"Проблемы с соединением: {status_msg}"

