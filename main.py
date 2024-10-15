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

    async def search_videos(self, query: str, count: int = 50, filters: Dict[str, Any] = None, sort_by: str = 'popularity') -> List[Dict]:
        """Поиск коротких видео по ключевым словам или хэштегам."""
        url = f'{VK_API_URL}video.search'
        params = {
            'access_token': self.token,
            'v': API_VERSION,
            'q': query,
            'count': count,
            'short': 1,  # Ищем только короткие видео
            'sort': 2 if sort_by == 'popularity' else 0,  # 2 - сортировка по популярности, 0 - по дате
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

        async with aiohttp.ClientSession() as session:
            result = await self.fetch(session, url, params)

            if 'response' not in result:
                raise ValueError(f"Ошибка получения видео: {result.get('error')}")

            videos = result['response']['items']
            return self.remove_duplicates(videos)

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
    token = 'ваш_токен'  # Укажите свой токен API ВКонтакте
    vk_search = VKVideoSearch(token)

    # Выполняем поиск по ключевым словам
    try:
        videos = await vk_search.search_videos(query='путешествия', count=10, filters={
            'min_likes': 100,
            'date_from': '2023-01-01',
        }, sort_by='popularity')

        # Сортируем видео по количеству лайков
        sorted_videos = vk_search.sort_videos(videos, sort_by='likes')
        for video in sorted_videos:
            print(f"Название: {video['title']}, Лайков: {video['likes']['count']}, Просмотров: {video['views']}")
    except Exception as e:
        print(f"Ошибка: {e}")

# Запускаем асинхронный процесс
if __name__ == '__main__':
    asyncio.run(main())