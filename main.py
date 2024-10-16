import aiohttp
import asyncio
from typing import List, Dict, Any

VK_API_URL = 'https://api.vk.com/method/'
API_VERSION = '5.131'

class VKVideoSearch:
    def __init__(self, token: str):
        self.token = token

    async def fetch(self, session: aiohttp.ClientSession, url: str, params: Dict[str, Any]) -> Dict:
        """Асинхронный запрос к API ВКонтакте."""
        async with session.get(url, params=params) as response:
            return await response.json()

    async def search_videos(self, query: str, count: int = 50, filters: Dict[str, Any] = None, sort_by: str = 'popularity', max_pages: int = 5) -> List[Dict]:
        """Поиск коротких видео по ключевым словам или хэштегам с фильтрами и пагинацией."""
        url = f'{VK_API_URL}video.search'
        params = {
            'access_token': self.token,
            'v': API_VERSION,
            'q': query,
            'count': count,
            'sort': 2 if sort_by == 'popularity' else 1,  # 2 - сортировка по популярности, 1 - по дате
            'filters': 'short',  # Ищем только короткие видео
            'extended': 1,  # Получаем расширенную информацию (лайки, просмотры, комментарии)
            'offset': 0  # Начальная позиция для пагинации
        }

        if filters:
            if 'date_from' in filters:
                params['filters'] = f"date_from={filters['date_from']}"
            if 'date_to' in filters:
                params['filters'] = f"date_to={filters['date_to']}"
            if 'min_likes' in filters:
                params['min_likes'] = filters['min_likes']
            if 'min_views' in filters:
                params['min_views'] = filters['min_views']
            if 'min_duration' in filters and 'max_duration' in filters:
                params['filters'] = f"duration={filters['min_duration']},{filters['max_duration']}"

        all_videos = []
        async with aiohttp.ClientSession() as session:
            for page in range(max_pages):
                params['offset'] = page * count  # Смещение для пагинации
                result = await self.fetch(session, url, params)

                if 'response' not in result:
                    raise ValueError(f"Ошибка получения видео: {result.get('error')}")

                videos = result['response']['items']
                all_videos.extend(videos)

                # Если вернулось меньше видео, чем запрашивали, выходим из цикла
                if len(videos) < count:
                    break

            return self.remove_duplicates(all_videos)

    def remove_duplicates(self, videos: List[Dict]) -> List[Dict]:
        """Исключение одинаковых видео по ID."""
        seen = set()
        unique_videos = []
        for video in videos:
            if video['id'] not in seen:
                unique_videos.append(video)
                seen.add(video['id'])
        return unique_videos

    def sort_videos(self, videos: List[Dict], sort_by: str) -> List[Dict]:
        """Сортировка видео по заданным метрикам."""
        if sort_by == 'date':
            return sorted(videos, key=lambda x: x['date'], reverse=True)
        elif sort_by == 'likes':
            return sorted(videos, key=lambda x: x['likes']['count'], reverse=True)
        elif sort_by == 'views':
            return sorted(videos, key=lambda x: x['views'], reverse=True)
        return videos  # Сортировка по умолчанию (без изменений)

# Пример использования модуля:
async def main():
    token = 'vk1.a.KYCHMPKEEGwczPiIWFRvJS2ZQKE6bXcJoJkwZI9OI7Z5P1mbg4m4WE0MnJd7GzjOxXF3GKfHUGFxBAgHSmy1mByw3qozl7gVmxjzxa1H0S5QW3lLpUaE5B4iKzOzA5kHj9gjeVR2DszfPEkka2_ZAL8qQ4W0ZCLu-8XkIbcO9cm-Xgg9HLciR9a2pCLovy3qy7aSxM1Vep7T1-V63WtDpA'  # Укажите свой токен API ВКонтакте
    vk_search = VKVideoSearch(token)

    # Выполняем поиск с фильтром по длительности (в секундах) и пагинацией
    try:
        videos = await vk_search.search_videos(query='путешествия', count=10, filters={
            'min_likes': 100,
            'date_from': '2023-01-01',
            'min_duration': 10,  # Минимальная длина видео 10 секунд
            'max_duration': 60   # Максимальная длина видео 60 секунд
        }, sort_by='popularity', max_pages=3)

        # Сортируем видео по количеству просмотров
        sorted_videos = vk_search.sort_videos(videos, sort_by='views')
        for video in sorted_videos:
            print(f"Название: {video['title']}, Лайков: {video['likes']['count']}, Просмотров: {video['views']}")
    except Exception as e:
        print(f"Ошибка: {e}")

# Запускаем асинхронный процесс
if __name__ == '__main__':
    asyncio.run(main())
