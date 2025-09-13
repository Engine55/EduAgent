#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库客户端 - 直接使用 PostgreSQL
替代 Redis 操作
"""

import json
import os
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional
from psycopg2.extras import RealDictCursor

class DatabaseClient:
    """数据库客户端，直接操作 PostgreSQL"""
    
    def __init__(self):
        self.connection_string = os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable is required")
    
    def get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(self.connection_string)
    
    def save_requirement(self, requirement_id: str, user_id: str, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存需求数据"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO edu_data (id, data_type, user_id, data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = EXCLUDED.updated_at
                    """, [
                        requirement_id,
                        'requirement',
                        user_id,
                        json.dumps(requirement_data, ensure_ascii=False),
                        datetime.now(),
                        datetime.now()
                    ])
                    conn.commit()
            
            return {
                'success': True,
                'requirement_id': requirement_id,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_requirement(self, requirement_id: str) -> Dict[str, Any]:
        """获取需求数据"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT data FROM edu_data 
                        WHERE id = %s AND data_type = 'requirement'
                    """, [requirement_id])
                    
                    result = cursor.fetchone()
                    if result:
                        return {
                            'success': True,
                            'data': result['data']
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Requirement not found'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_latest_requirement(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取最新需求数据"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if user_id:
                        cursor.execute("""
                            SELECT id, data FROM edu_data 
                            WHERE data_type = 'requirement' AND user_id = %s
                            ORDER BY created_at DESC LIMIT 1
                        """, [user_id])
                    else:
                        cursor.execute("""
                            SELECT id, data FROM edu_data 
                            WHERE data_type = 'requirement'
                            ORDER BY created_at DESC LIMIT 1
                        """)
                    
                    result = cursor.fetchone()
                    if result:
                        return {
                            'success': True,
                            'data': result['data'],
                            'requirement_id': result['id']
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'No requirements found'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_story(self, story_id: str, requirement_id: str, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存故事数据"""
        try:
            # 添加关联信息
            story_data['requirement_id'] = requirement_id
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO edu_data (id, data_type, user_id, data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = EXCLUDED.updated_at
                    """, [
                        story_id,
                        'story',
                        None,
                        json.dumps(story_data, ensure_ascii=False),
                        datetime.now(),
                        datetime.now()
                    ])
                    conn.commit()
            
            return {
                'success': True,
                'story_id': story_id,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_storyboard(self, storyboard_id: str, story_id: str, storyboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存分镜数据"""
        try:
            # 添加关联信息
            storyboard_data['story_id'] = story_id
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO edu_data (id, data_type, user_id, data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        data = EXCLUDED.data,
                        updated_at = EXCLUDED.updated_at
                    """, [
                        storyboard_id,
                        'storyboard',
                        None,
                        json.dumps(storyboard_data, ensure_ascii=False),
                        datetime.now(),
                        datetime.now()
                    ])
                    conn.commit()
            
            return {
                'success': True,
                'storyboard_id': storyboard_id,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# 全局客户端实例
db_client = DatabaseClient()