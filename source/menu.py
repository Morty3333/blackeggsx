"""
Модуль интерактивного меню для выбора VLESS ключей
"""
import sys
from typing import List, Dict, Optional

from key_loader import KeyLoader


class Menu:
    """Интерактивное меню выбора ключей"""
    
    @staticmethod
    def show_menu(keys: List[Dict[str, str]]) -> Optional[str]:
        """
        Показывает меню выбора ключей
        
        Args:
            keys: Список ключей для выбора
            
        Returns:
            Выбранный VLESS URL или None
        """
        if not keys:
            print("\n⚠ Ключи не найдены")
            print("Вы можете ввести свой ключ вручную")
            print()
            return Menu._input_custom_key()
        
        print("\n" + "=" * 60)
        print("Выберите сервер для подключения:")
        print("=" * 60)
        
        # Показываем список ключей
        for i, key in enumerate(keys, 1):
            # Обрезаем длинные имена
            name = key['name'][:50] if len(key['name']) > 50 else key['name']
            # Показываем краткую информацию об URL
            url_preview = key['url'][:60] + "..." if len(key['url']) > 60 else key['url']
            print(f"  [{i}] {name}")
            print(f"      {url_preview}")
        
        print(f"\n  [{len(keys) + 1}] Ввести свой ключ вручную")
        print(f"  [0]  Вернуться в главное меню")
        print("=" * 60)
        
        while True:
            try:
                choice = input("\nВаш выбор: ").strip()
                
                if choice == '0':
                    print("Возврат в главное меню...")
                    return "RETURN_TO_MAIN_MENU"
                
                if choice == str(len(keys) + 1):
                    # Ввод своего ключа
                    custom_key = Menu._input_custom_key()
                    if custom_key == "RETURN_TO_MAIN_MENU":
                        return "RETURN_TO_MAIN_MENU"
                    if custom_key:
                        return custom_key
                    # Если вернулись из ввода ключа, возвращаемся в главное меню
                    return "RETURN_TO_MAIN_MENU"
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(keys):
                    selected_key = keys[choice_num - 1]
                    print(f"\n✓ Выбран: {selected_key['name']}")
                    return selected_key['url']
                else:
                    print(f"✗ Неверный выбор. Введите число от 0 до {len(keys) + 1}")
                    
            except ValueError:
                print("✗ Введите число")
            except KeyboardInterrupt:
                print("\n\nВозврат в главное меню...")
                return "RETURN_TO_MAIN_MENU"
            except Exception as e:
                print(f"✗ Ошибка: {e}")
    
    @staticmethod
    def _input_custom_key() -> Optional[str]:
        """Запрашивает ввод пользовательского ключа"""
        while True:
            print("\n" + "=" * 60)
            print("Ввод своего VLESS ключа")
            print("=" * 60)
            print("Введите VLESS URL (vless://...)")
            print("Или нажмите Enter для возврата в главное меню")
            print("=" * 60)
            
            try:
                custom_key = input("\nVLESS URL: ").strip()
                
                if not custom_key:
                    print("Возврат в главное меню...")
                    return "RETURN_TO_MAIN_MENU"
                
                if not custom_key.startswith('vless://'):
                    print("✗ URL должен начинаться с 'vless://'")
                    print("Попробуйте еще раз или нажмите Enter для возврата в меню")
                    continue
                
                print("✓ Ключ принят")
                return custom_key
                
            except KeyboardInterrupt:
                print("\n\nВозврат в главное меню...")
                return "RETURN_TO_MAIN_MENU"
            except Exception as e:
                print(f"✗ Ошибка: {e}")
                print("Попробуйте еще раз или нажмите Enter для возврата в меню")
    
    @staticmethod
    def select_key() -> Optional[str]:
        """
        Главная функция выбора ключа
        Показывает главное меню выбора источника ключа
        
        Returns:
            Выбранный VLESS URL или None
        """
        print("=" * 60)
        print("VPN Клиент - Выбор сервера")
        print("=" * 60)
        
        while True:
            print("\n" + "=" * 60)
            print("Выберите источник ключа:")
            print("=" * 60)
            print("  [1] Ввести свой ключ вручную")
            print("  [2] Выбрать ключ с GitHub")
            print("  [0] Выход")
            print("=" * 60)
            
            try:
                choice = input("\nВаш выбор: ").strip()
                
                if choice == '0':
                    print("Выход...")
                    return None
                
                elif choice == '1':
                    # Ввод своего ключа
                    result = Menu._input_custom_key()
                    if result == "RETURN_TO_MAIN_MENU":
                        continue  # Возвращаемся в главное меню
                    return result
                
                elif choice == '2':
                    # Загрузка ключей с GitHub
                    result = Menu._select_from_github()
                    if result == "RETURN_TO_MAIN_MENU":
                        continue  # Возвращаемся в главное меню
                    return result
                
                else:
                    print("✗ Неверный выбор. Введите 1, 2 или 0")
                    
            except ValueError:
                print("✗ Введите число")
            except KeyboardInterrupt:
                print("\n\nВыход...")
                return None
            except Exception as e:
                print(f"✗ Ошибка: {e}")
    
    @staticmethod
    def _select_from_github() -> Optional[str]:
        """
        Загружает ключи с GitHub и показывает меню выбора
        
        Returns:
            Выбранный VLESS URL или None
        """
        print("\n" + "=" * 60)
        print("Загрузка ключей с GitHub...")
        print("=" * 60)
        
        # Загружаем ключи с GitHub (с автоматической проверкой обновлений)
        keys = KeyLoader.load_keys_from_github(force_refresh=False)
        
        # Если не удалось загрузить с GitHub
        if not keys:
            print("\n⚠ Не удалось загрузить ключи с GitHub")
            print("  Возможные причины:")
            print("  - Нет подключения к интернету")
            print("  - Проблемы с доступом к GitHub")
            print("  - Файл на GitHub пуст или не содержит ключей")
            print()
            
            while True:
                response = input("Вернуться в главное меню? (y/n): ").strip().lower()
                if response == 'y' or response == 'yes' or response == 'да':
                    # Возвращаем специальное значение для возврата в главное меню
                    return "RETURN_TO_MAIN_MENU"
                elif response == 'n' or response == 'no' or response == 'нет':
                    # Предлагаем ввести ключ вручную
                    return Menu._input_custom_key()
                else:
                    print("✗ Введите 'y' для возврата в меню или 'n' для ввода ключа")
        
        # Показываем меню выбора из загруженных ключей
        return Menu.show_menu(keys)

