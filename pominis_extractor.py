#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PominisExtractor:
    """Pominis.com prompt提取器"""
    
    def __init__(self):
        self.base_url = "https://pominis.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://pominis.com/en'
        })
        self.stories = []
        
    def discover_api_endpoints(self) -> List[str]:
        """发现可能的API端点"""
        potential_endpoints = [
            "/api/stories",
            "/api/stories/public",
            "/api/content/stories", 
            "/api/v1/stories",
            "/stories",
            "/content/stories",
            "/en/api/stories",
            "/_next/static/chunks/pages/",
            "/api/prompts",
            "/api/templates"
        ]
        
        working_endpoints = []
        for endpoint in potential_endpoints:
            url = urljoin(self.base_url, endpoint)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"发现工作的端点: {url}")
                    working_endpoints.append(url)
                elif response.status_code in [401, 403]:
                    logger.info(f"需要认证的端点: {url}")
                    working_endpoints.append(url)
            except Exception as e:
                logger.debug(f"端点 {url} 不可用: {e}")
                
        return working_endpoints
    
    def extract_from_html(self, url: str = None) -> Dict[str, Any]:
        """从HTML页面提取故事数据"""
        if not url:
            url = f"{self.base_url}/en"
            
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # 查找Next.js数据
            patterns = [
                r'__NEXT_DATA__"[^>]*>([^<]+)',
                r'window\.__NEXT_DATA__\s*=\s*([^;]+)',
                r'"props":\s*({[^}]+})',
                r'"stories":\s*(\[[^\]]+\])',
                r'"pageProps":\s*({.+?})'
            ]
            
            extracted_data = {}
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                if matches:
                    for match in matches:
                        try:
                            data = json.loads(match)
                            extracted_data[f"pattern_{pattern[:20]}"] = data
                            logger.info(f"找到数据: {pattern[:20]}")
                        except json.JSONDecodeError:
                            continue
                            
            return extracted_data
            
        except Exception as e:
            logger.error(f"HTML提取失败: {e}")
            return {}
    
    def check_network_requests(self) -> List[str]:
        """检查可能的网络请求模式"""
        # 分析网站可能发送的请求
        common_patterns = [
            "/api/stories?page=1&limit=20",
            "/api/stories?sort=latest",
            "/api/stories?sort=popular", 
            "/api/stories?genre=Fantasy",
            "/api/content/public",
            "/api/stories/featured",
            "/_next/data/build-id/en.json",
            "/_next/data/build-id/en/stories.json"
        ]
        
        results = []
        for pattern in common_patterns:
            url = urljoin(self.base_url, pattern)
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"有效请求: {url}")
                    results.append(url)
                    
                    # 尝试解析JSON
                    try:
                        data = response.json()
                        if isinstance(data, dict) and ('stories' in data or 'data' in data):
                            logger.info(f"找到故事数据: {len(data.get('stories', data.get('data', [])))}")
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"请求失败 {url}: {e}")
                
        return results
    
    def extract_story_details(self, story_id: str) -> Dict[str, Any]:
        """提取单个故事的详细信息"""
        story_urls = [
            f"/api/stories/{story_id}",
            f"/en/story/{story_id}",
            f"/story/{story_id}",
            f"/api/content/{story_id}"
        ]
        
        for story_url in story_urls:
            url = urljoin(self.base_url, story_url)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    if 'application/json' in response.headers.get('content-type', ''):
                        return response.json()
                    else:
                        # 从HTML提取
                        html = response.text
                        # 查找故事内容的pattern
                        story_patterns = [
                            r'"story":\s*({[^}]+})',
                            r'"content":\s*"([^"]+)"',
                            r'"prompt":\s*"([^"]+)"',
                            r'"description":\s*"([^"]+)"'
                        ]
                        
                        story_data = {}
                        for pattern in story_patterns:
                            matches = re.findall(pattern, html)
                            if matches:
                                story_data[pattern[:10]] = matches
                                
                        return story_data
                        
            except Exception as e:
                logger.debug(f"故事详情提取失败 {url}: {e}")
                
        return {}
    
    def search_stories_by_genre(self, genre: str = "Fantasy") -> List[Dict]:
        """按类型搜索故事"""
        search_urls = [
            f"/api/stories?genre={genre}",
            f"/api/search?q={genre}",
            f"/en/genre/{genre}",
            f"/stories?filter={genre}"
        ]
        
        all_stories = []
        for search_url in search_urls:
            url = urljoin(self.base_url, search_url)
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    if 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        if isinstance(data, dict):
                            stories = data.get('stories', data.get('data', []))
                            all_stories.extend(stories)
                        elif isinstance(data, list):
                            all_stories.extend(data)
                            
                        logger.info(f"从 {url} 找到 {len(stories if 'stories' in locals() else data)} 个故事")
                        
            except Exception as e:
                logger.debug(f"搜索失败 {url}: {e}")
                
        return all_stories
    
    def extract_all_prompts(self) -> Dict[str, Any]:
        """提取所有可用的prompt"""
        logger.info("开始提取Pominis所有prompt...")
        
        results = {
            'stories': [],
            'prompts': [],
            'api_endpoints': [],
            'extraction_methods': []
        }
        
        # 1. 发现API端点
        logger.info("步骤1: 发现API端点...")
        endpoints = self.discover_api_endpoints()
        results['api_endpoints'] = endpoints
        
        # 2. 从HTML页面提取
        logger.info("步骤2: 从HTML提取数据...")
        html_data = self.extract_from_html()
        if html_data:
            results['html_extraction'] = html_data
            results['extraction_methods'].append('html_parsing')
        
        # 3. 检查网络请求
        logger.info("步骤3: 检查网络请求...")
        network_requests = self.check_network_requests() 
        results['network_requests'] = network_requests
        
        # 4. 按类型搜索
        logger.info("步骤4: 按类型搜索故事...")
        genres = ['Fantasy', 'Horror', 'Science Fiction', 'Mystery', 'Romance', 'Drama']
        for genre in genres:
            stories = self.search_stories_by_genre(genre)
            if stories:
                results['stories'].extend(stories)
                results['extraction_methods'].append(f'genre_search_{genre}')
        
        # 5. 提取故事详情
        logger.info("步骤5: 提取故事详情...")
        story_ids = self._extract_story_ids_from_results(results)
        for story_id in story_ids[:10]:  # 限制为前10个
            details = self.extract_story_details(story_id)
            if details:
                results['story_details'] = results.get('story_details', [])
                results['story_details'].append({'id': story_id, 'details': details})
        
        # 6. 汇总统计
        results['summary'] = {
            'total_stories_found': len(results['stories']),
            'working_endpoints': len(results['api_endpoints']),
            'extraction_methods_used': len(results['extraction_methods']),
            'story_details_extracted': len(results.get('story_details', []))
        }
        
        logger.info(f"提取完成! 找到 {results['summary']['total_stories_found']} 个故事")
        return results
    
    def _extract_story_ids_from_results(self, results: Dict) -> List[str]:
        """从结果中提取故事ID"""
        story_ids = []
        
        # 从stories中提取ID
        for story in results.get('stories', []):
            if isinstance(story, dict):
                story_id = story.get('id') or story.get('_id') or story.get('storyId')
                if story_id:
                    story_ids.append(str(story_id))
        
        # 从HTML数据中提取ID
        html_data = results.get('html_extraction', {})
        for key, data in html_data.items():
            if isinstance(data, dict):
                if 'stories' in data and isinstance(data['stories'], list):
                    for story in data['stories']:
                        if isinstance(story, dict):
                            story_id = story.get('id') or story.get('_id')
                            if story_id:
                                story_ids.append(str(story_id))
        
        return list(set(story_ids))  # 去重
    
    def save_results(self, results: Dict[str, Any], filename: str = "pominis_extraction_results.json"):
        """保存提取结果"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存失败: {e}")

def main():
    """主函数"""
    extractor = PominisExtractor()
    
    print("🔍 Pominis Prompt 提取器")
    print("=" * 50)
    
    # 提取所有prompt
    results = extractor.extract_all_prompts()
    
    # 显示摘要
    summary = results['summary']
    print(f"\n📊 提取摘要:")
    print(f"  找到故事数量: {summary['total_stories_found']}")
    print(f"  可用API端点: {summary['working_endpoints']}")
    print(f"  使用的提取方法: {summary['extraction_methods_used']}")
    print(f"  提取的故事详情: {summary['story_details_extracted']}")
    
    # 保存结果
    extractor.save_results(results)
    
    # 显示部分提取的内容
    if results['stories']:
        print(f"\n📚 找到的故事示例:")
        for i, story in enumerate(results['stories'][:3]):
            print(f"  {i+1}. {story.get('title', 'Unknown Title')}")
            if story.get('description'):
                print(f"     描述: {story['description'][:100]}...")
    
    if results['api_endpoints']:
        print(f"\n🔗 发现的API端点:")
        for endpoint in results['api_endpoints'][:5]:
            print(f"  - {endpoint}")
    
    print(f"\n✅ 完成! 详细结果已保存到 pominis_extraction_results.json")

if __name__ == "__main__":
    main()