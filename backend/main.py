from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from agent_service import AgentService

app = FastAPI(title="EduAgent API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局AgentService实例
agent_service = AgentService()

# 请求模型
class StartConversationRequest(BaseModel):
    pass  # 不需要参数

class ProcessRequestModel(BaseModel):
    user_input: str

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