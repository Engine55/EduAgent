from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from agent_service import AgentService
from scene_generator import create_scene_generator
from database_client import db_client

app = FastAPI(title="EduAgent API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Next.js开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
agent_service = AgentService()
scene_generator = create_scene_generator()

# 请求模型
class StartConversationRequest(BaseModel):
    pass  # 不需要参数

class ProcessRequestModel(BaseModel):
    user_input: str

class GenerateStoryboardsRequest(BaseModel):
    requirement_id: str

class GetStoryByIdRequest(BaseModel):
    story_id: str

# 响应模型
from typing import Union, List
class APIResponse(BaseModel):
    success: bool
    data: Union[Dict[str, Any], List[Any]] = {}
    message: str = ""
    error: str = ""

@app.get("/")
async def root():
    return {"message": "EduAgent API is running"}

@app.post("/start_conversation", response_model=APIResponse)
async def start_conversation(request: StartConversationRequest):
    """开始对话会话"""
    try:
        result = agent_service.start_conversation()
        return APIResponse(
            success=True,
            data=result,
            message="对话会话已开始"
        )
    except Exception as e:
        print(f"开始对话失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"开始对话失败: {str(e)}"
        )

@app.post("/process_request", response_model=APIResponse)
async def process_request(request: ProcessRequestModel):
    """处理用户请求"""
    try:
        if not request.user_input or not request.user_input.strip():
            raise HTTPException(
                status_code=400,
                detail="用户输入不能为空"
            )
        
        result = await agent_service.process_request(request.user_input.strip())
        
        return APIResponse(
            success=True,
            data=result,
            message="请求处理成功"
        )
    except Exception as e:
        print(f"处理请求失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"处理请求失败: {str(e)}"
        )

@app.post("/generate_complete_storyboards", response_model=APIResponse)
async def generate_complete_storyboards(request: GenerateStoryboardsRequest):
    """生成完整的RPG框架、关卡数据和所有故事板"""
    try:
        # 如果没有提供requirement_id，则获取最新的需求数据
        if not request.requirement_id or not request.requirement_id.strip():
            print("未提供需求ID，获取最新的需求数据...")
            latest_requirement = db_client.get_latest_requirement()

            if not latest_requirement.get("success"):
                raise HTTPException(
                    status_code=404,
                    detail=f"未找到需求数据: {latest_requirement.get('error', '未知错误')}"
                )

            requirement_id = latest_requirement["requirement_id"]
            print(f"使用最新需求数据，需求ID: {requirement_id}")
        else:
            requirement_id = request.requirement_id.strip()
            print(f"使用指定需求ID: {requirement_id}")

        print(f"开始查询故事板数据，需求ID: {requirement_id}")

        # 先尝试从数据库查询已生成的storyboard数据
        story_id = f"story_{requirement_id}"
        story_result = db_client.get_story(story_id)
        
        if story_result.get("success"):
            # 找到已生成的数据，直接返回
            story_data = story_result["data"]
            print(f"找到已生成的故事板数据，story_id: {story_id}")
            
            response_data = {
                "requirement_id": request.requirement_id,
                "story_data": story_data,
                "storyboards_data": story_data.get("storyboards_data", {}),
                "story_framework": story_data.get("story_framework", ""),
                "from_database": True
            }
        else:
            # 没找到数据，返回错误
            print(f"未找到故事板数据: {story_id}")
            raise HTTPException(
                status_code=404,
                detail=f"未找到故事板数据，需求ID: {request.requirement_id}"
            )
        
        return APIResponse(
            success=True,
            data=response_data,
            message="成功获取故事板数据"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"生成故事板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成故事板失败: {str(e)}"
        )

@app.get("/get_all_stories", response_model=APIResponse)
async def get_all_stories():
    """获取所有故事的历史记录"""
    try:
        print("获取所有故事历史记录...")
        
        # 从数据库获取所有故事
        result = db_client.get_all_stories()
        
        if result.get("success"):
            stories_data = result.get("data", [])
            print(f"找到 {len(stories_data)} 条故事记录")
            
            # 处理数据格式，提取关键信息用于列表显示
            history_list = []
            for story in stories_data:
                story_data = story.get("data", {})
                storyboards_data = story_data.get("storyboards_data", {})
                
                history_item = {
                    "story_id": story.get("id", ""),
                    "requirement_id": story_data.get("requirement_id", ""),
                    "story_title": storyboards_data.get("story_title", "未命名游戏"),
                    "subject": storyboards_data.get("subject", "未知"),
                    "grade": storyboards_data.get("grade", "未知"),
                    "created_at": story.get("created_at", ""),
                    "updated_at": story.get("updated_at", ""),
                    "storyboard_count": len(storyboards_data.get("storyboards", []))
                }
                history_list.append(history_item)
            
            # 按更新时间倒序排列
            history_list.sort(key=lambda x: x["updated_at"], reverse=True)
            
            return APIResponse(
                success=True,
                data=history_list,
                message=f"成功获取 {len(history_list)} 条故事记录"
            )
        else:
            return APIResponse(
                success=True,
                data=[],
                message="暂无故事记录"
            )
            
    except Exception as e:
        print(f"获取故事历史记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取故事历史记录失败: {str(e)}"
        )

@app.post("/get_story_by_id", response_model=APIResponse)
async def get_story_by_id(request: GetStoryByIdRequest):
    """根据story_id获取完整的故事数据"""
    try:
        if not request.story_id or not request.story_id.strip():
            raise HTTPException(
                status_code=400,
                detail="故事ID不能为空"
            )
        
        print(f"获取故事数据，story_id: {request.story_id}")
        
        # 从数据库获取故事数据
        result = db_client.get_story(request.story_id.strip())
        
        if result.get("success"):
            story_data = result["data"]
            print(f"成功获取故事数据: {request.story_id}")
            
            return APIResponse(
                success=True,
                data=story_data,
                message="成功获取故事数据"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"未找到故事数据，ID: {request.story_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取故事数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取故事数据失败: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "eduagent",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)