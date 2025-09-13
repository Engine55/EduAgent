from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from agent_service import AgentService
from scene_generator import create_scene_generator

app = FastAPI(title="EduAgent API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js开发服务器
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

# 响应模型
class APIResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
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
        if not request.requirement_id or not request.requirement_id.strip():
            raise HTTPException(
                status_code=400,
                detail="需求ID不能为空"
            )
        
        print(f"🎬 开始生成完整故事板，需求ID: {request.requirement_id}")
        
        # 调用场景生成器生成完整内容
        rpg_framework, stages_list, storyboards_list = scene_generator.generate_complete_storyboards(
            request.requirement_id.strip()
        )
        
        if not rpg_framework or not stages_list:
            raise HTTPException(
                status_code=500,
                detail="RPG框架生成失败，请检查需求ID是否正确"
            )
        
        # 构建响应数据
        response_data = {
            "rpg_framework": rpg_framework,
            "stages_list": stages_list,
            "storyboards_list": storyboards_list,
            "total_stages": len(stages_list),
            "successful_storyboards": len(storyboards_list) if storyboards_list else 0,
            "requirement_id": request.requirement_id.strip()
        }
        
        success_message = f"成功生成RPG框架和{len(stages_list)}个关卡"
        if storyboards_list:
            success_message += f"，以及{len(storyboards_list)}个关卡的故事板"
        
        return APIResponse(
            success=True,
            data=response_data,
            message=success_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"生成故事板失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成故事板失败: {str(e)}"
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