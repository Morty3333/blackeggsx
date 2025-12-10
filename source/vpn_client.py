"""
Основной CLI скрипт для VPN клиента VLESS/Xray
"""
import argparse
import sys
import os
import signal
import atexit
from pathlib import Path

# Проверка импортов модулей
try:
    from vless_parser import VLESSURLParser
    from xray_config import XrayConfigGenerator
    from xray_runner import XrayRunner
    from proxy_manager import WindowsProxyManager
    from menu import Menu
    from connection_checker import ConnectionChecker
except ImportError as e:
    print(f"Ошибка импорта модулей: {e}")
    print("Убедитесь, что все файлы проекта находятся в одной директории.")
    sys.exit(1)


class VPNClient:
    """Основной класс VPN клиента"""
    
    def __init__(self):
        self.parser = VLESSURLParser()
        self.config_generator = XrayConfigGenerator()
        self.xray_runner = XrayRunner()
        self.proxy_manager = WindowsProxyManager()
        self.config_file = 'config.json'
    
    def connect(self, vless_url: str, local_port: int = 10808, socks_port: int = 10809):
        """
        Подключается к VPN используя VLESS URL
        
        Args:
            vless_url: VLESS URL (vless://...)
            local_port: Локальный порт для HTTP прокси
            socks_port: Локальный порт для SOCKS5 прокси
        """
        print("=" * 60)
        print("VPN Клиент для VLESS/Xray")
        print("=" * 60)
        
        # Парсим URL
        print("\n[1/5] Парсинг VLESS URL...")
        try:
            vless_params = self.parser.parse(vless_url)
            print(f"✓ UUID: {vless_params['uuid'][:8]}...")
            print(f"✓ Сервер: {vless_params['host']}:{vless_params['port']}")
            print(f"✓ Тип: {vless_params['type']}")
            print(f"✓ Безопасность: {vless_params.get('security', 'none')}")
            
            # Для Reality показываем дополнительные параметры
            if vless_params.get('security') == 'reality':
                pbk = vless_params.get('pbk') or vless_params.get('params', {}).get('pbk')
                sid = vless_params.get('sid') or vless_params.get('params', {}).get('sid')
                if pbk:
                    print(f"✓ PublicKey: {pbk[:20]}...")
                else:
                    print(f"⚠ PublicKey не найден в URL")
                if sid:
                    print(f"✓ ShortID: {sid}")
                else:
                    print(f"⚠ ShortID не найден в URL")
        except Exception as e:
            print(f"✗ Ошибка парсинга URL: {e}")
            return False
        
        # Проверяем соединение
        print(f"\n[2/5] Проверка соединения с сервером...")
        print(f"  Сервер: {vless_params['host']}:{vless_params['port']}")
        try:
            conn_ok, conn_msg = ConnectionChecker.check_connection(
                vless_params['host'], 
                vless_params['port'],
                check_ping=True
            )
            if conn_ok:
                print(f"✓ {conn_msg}")
            else:
                print(f"⚠ {conn_msg}")
                response = input("\nПродолжить подключение несмотря на проблемы? (y/n): ").strip().lower()
                if response != 'y' and response != 'yes' and response != 'да':
                    print("Подключение отменено")
                    return False
        except Exception as e:
            print(f"⚠ Ошибка проверки соединения: {e}")
            response = input("\nПродолжить подключение? (y/n): ").strip().lower()
            if response != 'y' and response != 'yes' and response != 'да':
                print("Подключение отменено")
                return False
        
        # Генерируем конфигурацию
        print(f"\n[3/5] Генерация конфигурации Xray...")
        try:
            # Для отладки показываем параметры перед генерацией
            if vless_params.get('security') == 'reality':
                pbk_val = vless_params.get('pbk') or vless_params.get('params', {}).get('pbk')
                sid_val = vless_params.get('sid') or vless_params.get('params', {}).get('sid')
                print(f"  Параметры Reality:")
                print(f"    pbk: {'есть (' + str(pbk_val)[:20] + '...)' if pbk_val else 'нет'}")
                print(f"    sid: {'есть (' + str(sid_val) + ')' if sid_val else 'нет'}")
            
            config = self.config_generator.generate(
                vless_params, 
                local_port=local_port,
                socks_port=socks_port
            )
            self.config_generator.save_config(config, self.config_file)
            print(f"✓ Конфигурация сохранена: {self.config_file}")
        except ValueError as e:
            print(f"✗ Ошибка генерации конфигурации: {e}")
            print("\nПроверьте, что в VLESS URL присутствуют все необходимые параметры:")
            print("  - pbk (publicKey) для Reality")
            print("  - sid (shortId) для Reality")
            return False
        except Exception as e:
            print(f"✗ Ошибка генерации конфигурации: {e}")
            import traceback
            print("\nДетали ошибки:")
            traceback.print_exc()
            return False
        
        # Запускаем Xray
        print(f"\n[4/5] Запуск Xray...")
        if not self.xray_runner.start(self.config_file):
            return False
        
        # Устанавливаем системный прокси
        print(f"\n[5/5] Установка системного прокси...")
        if not self.proxy_manager.set_proxy('127.0.0.1', local_port):
            print("⚠ Предупреждение: Не удалось установить системный прокси автоматически")
            print(f"  Вы можете настроить прокси вручную: 127.0.0.1:{local_port}")
        
        print("\n" + "=" * 60)
        print("✓ VPN подключен успешно!")
        print(f"  HTTP прокси: 127.0.0.1:{local_port}")
        print(f"  SOCKS5 прокси: 127.0.0.1:{socks_port}")
        print("=" * 60)
        print("\n" + "=" * 60)
        print("VPN АКТИВЕН")
        print("=" * 60)
        print("Ваш IP адрес теперь изменен через VPN")
        print("VPN будет работать до тех пор, пока окно открыто")
        print("\nДля отключения VPN закройте это окно (крестик)")
        print("=" * 60)
        
        return True
    
    def disconnect(self):
        """Отключается от VPN"""
        print("\n\nОтключение VPN...")
        
        # Удаляем системный прокси
        self.proxy_manager.remove_proxy()
        
        # Останавливаем Xray
        self.xray_runner.stop()
        
        # Удаляем конфигурационный файл
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
            except:
                pass
        
        print("✓ VPN отключен")
    
    def status(self):
        """Показывает статус подключения"""
        xray_status = self.xray_runner.get_status()
        proxy_info = self.proxy_manager.get_current_proxy()
        
        print("=" * 60)
        print("Статус VPN")
        print("=" * 60)
        print(f"Xray: {'✓ Запущен' if xray_status['running'] else '✗ Остановлен'}")
        if xray_status['pid']:
            print(f"  PID: {xray_status['pid']}")
        print(f"  Путь: {xray_status['xray_path']}")
        print(f"\nСистемный прокси:")
        if proxy_info:
            print(f"  {proxy_info}")
        else:
            print("  Не установлен")
        print("=" * 60)


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='VPN клиент для VLESS/Xray/V2Ray',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python vpn_client.py connect "vless://uuid@example.com:443?security=tls&sni=example.com#MyServer"
  python vpn_client.py connect "vless://..." --port 10808
  python vpn_client.py disconnect
  python vpn_client.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда connect
    connect_parser = subparsers.add_parser('connect', help='Подключиться к VPN')
    connect_parser.add_argument('url', nargs='?', help='VLESS URL (vless://...). Если не указан, откроется меню выбора')
    connect_parser.add_argument('--port', type=int, default=10808, 
                                help='Локальный порт для HTTP прокси (по умолчанию: 10808)')
    connect_parser.add_argument('--socks-port', type=int, default=10809,
                                help='Локальный порт для SOCKS5 прокси (по умолчанию: 10809)')
    
    # Команда menu
    subparsers.add_parser('menu', help='Открыть меню выбора сервера')
    
    # Команда disconnect
    subparsers.add_parser('disconnect', help='Отключиться от VPN')
    
    # Команда status
    subparsers.add_parser('status', help='Показать статус подключения')
    
    args = parser.parse_args()
    
    if not args.command:
        # Если команда не указана, показываем меню
        args.command = 'menu'
    
    client = VPNClient()
    
    # Регистрируем обработчик для корректного завершения
    def cleanup():
        try:
            client.disconnect()
        except:
            pass
    
    # Регистрируем cleanup для всех способов завершения
    atexit.register(cleanup)
    
    # Обработка сигналов для Windows
    if sys.platform == 'win32':
        def signal_handler(sig, frame):
            cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Обработка закрытия окна через крестик (Windows)
        try:
            import ctypes
            
            # Устанавливаем обработчик для закрытия консоли
            kernel32 = ctypes.windll.kernel32
            
            # Определяем тип функции обработчика
            HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint32)
            
            def console_handler(dwCtrlType):
                """Обработчик событий консоли Windows"""
                # CTRL_C_EVENT (0) - Ctrl+C
                # CTRL_CLOSE_EVENT (2) - Закрытие окна через крестик
                if dwCtrlType in [0, 2]:
                    cleanup()
                    return True
                return False
            
            # Регистрируем обработчик
            handler = HandlerRoutine(console_handler)
            kernel32.SetConsoleCtrlHandler(handler, True)
        except Exception:
            # Если не удалось установить обработчик, используем стандартный
            pass
    
    # Выполняем команду
    if args.command == 'connect':
        # Если URL не указан, показываем меню
        if not args.url:
            selected_url = Menu.select_key()
            if not selected_url:
                print("\nПодключение отменено. Закройте окно для выхода.")
                try:
                    # Ожидаем закрытия окна
                    import time
                    while True:
                        time.sleep(1)
                except:
                    pass
                return
            args.url = selected_url
        
        if client.connect(args.url, local_port=args.port, socks_port=args.socks_port):
            try:
                # Ожидаем закрытия окна (бесконечный цикл)
                # VPN работает постоянно, пока окно открыто
                import time
                print("\nОжидание... (VPN активен)")
                while True:
                    time.sleep(1)
                    # Проверяем, что Xray все еще работает
                    if not client.xray_runner.is_running():
                        print("\n⚠ Xray процесс завершился неожиданно")
                        break
            except (KeyboardInterrupt, SystemExit):
                # Ctrl+C или системное завершение
                pass
            except Exception as e:
                # Любое другое исключение (включая закрытие окна через крестик)
                pass
            finally:
                # Всегда отключаем VPN при выходе
                print("\n\nОтключение VPN...")
                client.disconnect()
        else:
            print("\nПодключение не удалось. Закройте окно для выхода.")
            try:
                # Ожидаем закрытия окна
                import time
                while True:
                    time.sleep(1)
            except:
                pass
    
    elif args.command == 'menu':
        selected_url = Menu.select_key()
        if selected_url and selected_url != "RETURN_TO_MAIN_MENU":
            if client.connect(selected_url):
                try:
                    # Ожидаем закрытия окна (бесконечный цикл)
                    # VPN работает постоянно, пока окно открыто
                    import time
                    print("\nОжидание... (VPN активен)")
                    while True:
                        time.sleep(1)
                        # Проверяем, что Xray все еще работает
                        if not client.xray_runner.is_running():
                            print("\n⚠ Xray процесс завершился неожиданно")
                            print("Попытка переподключения...")
                            # Можно добавить логику переподключения здесь
                            break
                except (KeyboardInterrupt, SystemExit):
                    # Ctrl+C или системное завершение
                    pass
                except Exception as e:
                    # Любое другое исключение (включая закрытие окна через крестик)
                    pass
                finally:
                    # Всегда отключаем VPN при выходе
                    print("\n\nОтключение VPN...")
                    client.disconnect()
            else:
                print("\nПодключение не удалось. Закройте окно для выхода.")
                try:
                    # Ожидаем закрытия окна
                    import time
                    while True:
                        time.sleep(1)
                except:
                    pass
        else:
            print("\nВыбор отменен. Закройте окно для выхода.")
            try:
                # Ожидаем закрытия окна
                import time
                while True:
                    time.sleep(1)
            except:
                pass
    
    elif args.command == 'disconnect':
        client.disconnect()
    
    elif args.command == 'status':
        client.status()


if __name__ == '__main__':
    main()

