"""
Модуль для загрузки VLESS ключей с GitHub
"""
import urllib.request
import urllib.error
from typing import List, Dict, Optional
import re
import os
import json
from pathlib import Path


class KeyLoader:
    """Загрузчик ключей с GitHub"""
    
    GITHUB_URL = "https://raw.githubusercontent.com/Morty3333/blackeggsx/main/vless_OpenRay_ru.txt"
    CACHE_FILE = 'keys_cache.json'
    CACHE_DURATION = 60  # Кэш на 60 секунд для частой проверки обновлений
    
    @staticmethod
    def _get_cache_path() -> Path:
        """Возвращает путь к файлу кэша"""
        return Path(KeyLoader.CACHE_FILE)
    
    @staticmethod
    def _load_cache() -> Optional[Dict]:
        """Загружает кэш из файла"""
        cache_path = KeyLoader._get_cache_path()
        if not cache_path.exists():
            return None
        
        try:
            import time
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            # Проверяем, не устарел ли кэш
            current_time = time.time()
            cache_time = cache.get('timestamp', 0)
            
            if current_time - cache_time > KeyLoader.CACHE_DURATION:
                return None  # Кэш устарел
            
            return cache
        except:
            return None
    
    @staticmethod
    def _save_cache(keys: List[Dict[str, str]], etag: Optional[str] = None) -> None:
        """Сохраняет кэш в файл"""
        try:
            import time
            cache = {
                'timestamp': time.time(),
                'keys': keys,
                'etag': etag
            }
            cache_path = KeyLoader._get_cache_path()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    @staticmethod
    def load_keys_from_github(force_refresh: bool = False) -> List[Dict[str, str]]:
        """
        Загружает ключи с GitHub с автоматической проверкой обновлений
        
        Args:
            force_refresh: Принудительно обновить ключи, игнорируя кэш
        
        Returns:
            Список словарей с ключами: [{'name': '...', 'url': 'vless://...'}, ...]
        """
        # Проверяем кэш, если не требуется принудительное обновление
        if not force_refresh:
            cache = KeyLoader._load_cache()
            if cache:
                keys = cache.get('keys', [])
                if keys:
                    print(f"✓ Загружено ключей из кэша: {len(keys)}")
                    # Проверяем обновления в фоне
                    KeyLoader._check_updates_async()
                    return keys
        
        keys = []
        etag = None
        
        try:
            print("Загрузка ключей с GitHub...")
            
            # Создаем запрос с проверкой ETag для определения обновлений
            request = urllib.request.Request(KeyLoader.GITHUB_URL)
            
            # Добавляем ETag из кэша, если есть
            cache = KeyLoader._load_cache()
            if cache and cache.get('etag'):
                request.add_header('If-None-Match', cache['etag'])
            
            with urllib.request.urlopen(request, timeout=10) as response:
                # Получаем ETag для кэширования
                etag = response.headers.get('ETag')
                
                # Если статус 304 (Not Modified), используем кэш
                if response.status == 304:
                    cache = KeyLoader._load_cache()
                    if cache:
                        keys = cache.get('keys', [])
                        print(f"✓ Ключи актуальны (из кэша): {len(keys)}")
                        return keys
                
                content = response.read().decode('utf-8', errors='ignore')
            
            # Парсим содержимое файла
            # Ожидаем формат: каждая строка может быть VLESS URL или содержать его
            lines = content.strip().split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Ищем VLESS URL в строке
                vless_match = re.search(r'vless://[^\s]+', line)
                if vless_match:
                    vless_url = vless_match.group(0)
                    
                    # Пытаемся извлечь имя из комментария или используем номер
                    name_match = re.search(r'#([^#\n]+)', line)
                    if name_match:
                        name = name_match.group(1).strip()
                    else:
                        name = f"Сервер {i}"
                    
                    keys.append({
                        'name': name,
                        'url': vless_url
                    })
                elif line.startswith('vless://'):
                    # Если вся строка - это VLESS URL
                    name = f"Сервер {i}"
                    keys.append({
                        'name': name,
                        'url': line
                    })
            
            print(f"✓ Загружено ключей: {len(keys)}")
            
            # Сохраняем в кэш
            if keys:
                KeyLoader._save_cache(keys, etag)
            
            return keys
            
        except urllib.error.HTTPError as e:
            # Если 304 (Not Modified), используем кэш
            if e.code == 304:
                cache = KeyLoader._load_cache()
                if cache:
                    keys = cache.get('keys', [])
                    print(f"✓ Ключи актуальны (из кэша): {len(keys)}")
                    return keys
            
            print(f"✗ Ошибка загрузки с GitHub: {e}")
            print(f"  URL: {KeyLoader.GITHUB_URL}")
            
            # Пытаемся использовать кэш при ошибке
            cache = KeyLoader._load_cache()
            if cache:
                keys = cache.get('keys', [])
                if keys:
                    print(f"⚠ Используются ключи из кэша: {len(keys)}")
                    return keys
            
            return []
        except urllib.error.URLError as e:
            print(f"✗ Ошибка загрузки с GitHub: {e}")
            print(f"  URL: {KeyLoader.GITHUB_URL}")
            
            # Пытаемся использовать кэш при ошибке
            cache = KeyLoader._load_cache()
            if cache:
                keys = cache.get('keys', [])
                if keys:
                    print(f"⚠ Используются ключи из кэша: {len(keys)}")
                    return keys
            
            return []
        except Exception as e:
            print(f"✗ Ошибка обработки ключей: {e}")
            
            # Пытаемся использовать кэш при ошибке
            cache = KeyLoader._load_cache()
            if cache:
                keys = cache.get('keys', [])
                if keys:
                    print(f"⚠ Используются ключи из кэша: {len(keys)}")
                    return keys
            
            return []
    
    @staticmethod
    def _check_updates_async() -> None:
        """Проверяет обновления в фоновом режиме (не блокирует UI)"""
        try:
            # Создаем запрос с ETag
            request = urllib.request.Request(KeyLoader.GITHUB_URL)
            cache = KeyLoader._load_cache()
            if cache and cache.get('etag'):
                request.add_header('If-None-Match', cache['etag'])
            
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status != 304:
                    # Есть обновления, загружаем их
                    content = response.read().decode('utf-8', errors='ignore')
                    etag = response.headers.get('ETag')
                    keys = KeyLoader._parse_keys(content)
                    if keys:
                        KeyLoader._save_cache(keys, etag)
                        print(f"  (Обновление: найдено {len(keys)} ключей)")
        except:
            pass  # Игнорируем ошибки фоновой проверки
    
    @staticmethod
    def _parse_keys(content: str) -> List[Dict[str, str]]:
        """Парсит ключи из содержимого файла"""
        keys = []
        lines = content.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            vless_match = re.search(r'vless://[^\s]+', line)
            if vless_match:
                vless_url = vless_match.group(0)
                
                name_match = re.search(r'#([^#\n]+)', line)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    name = f"Сервер {i}"
                
                keys.append({
                    'name': name,
                    'url': vless_url
                })
            elif line.startswith('vless://'):
                name = f"Сервер {i}"
                keys.append({
                    'name': name,
                    'url': line
                })
        
        return keys
    
    @staticmethod
    def load_keys_from_file(filepath: str = 'keys.txt') -> List[Dict[str, str]]:
        """
        Загружает ключи из локального файла
        
        Args:
            filepath: Путь к файлу с ключами
            
        Returns:
            Список словарей с ключами
        """
        keys = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                vless_match = re.search(r'vless://[^\s]+', line)
                if vless_match:
                    vless_url = vless_match.group(0)
                    
                    name_match = re.search(r'#([^#\n]+)', line)
                    if name_match:
                        name = name_match.group(1).strip()
                    else:
                        name = f"Сервер {i}"
                    
                    keys.append({
                        'name': name,
                        'url': vless_url
                    })
            
            return keys
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"✗ Ошибка чтения файла {filepath}: {e}")
            return []

