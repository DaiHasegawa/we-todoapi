from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from tortoise.contrib.pydantic import pydantic_model_creator
from model import TodoItem

app = FastAPI(title="TODO API", description="TODOリスト管理API", version="1.0.0")

# TortoiseモデルからPydanticモデルを自動生成: include=は必須、exclude=は除外
TodoItem_Pydantic = pydantic_model_creator(TodoItem, name="TodoItem")
TodoItemCreate_Pydantic = pydantic_model_creator(TodoItem, optional=("description",), exclude=("id", "completed"))
TodoItemUpdate_Pydantic = pydantic_model_creator(TodoItem, optional=("title", "description", "completed"), exclude=("id",))


# # POSTリクエスト検証用のモデル
# class TodoItemCreateScheme(BaseModel):
#     title: str
#     description: Optional[str] = None

# # PUTリクエスト検証用のモデル
# class TodoItemUpdateScheme(BaseModel):
#     title: Optional[str] = None
#     description: Optional[str] = None
#     completed: Optional[bool] = None


@app.get("/")
def read_root():
    return {"message": "TODO APIへようこそ！"}

# すべてのTODOを取得
@app.get("/todos", response_model=List[TodoItem_Pydantic])
def get_all_todos():
    return todos


# 特定のTODOを取得
@app.get("/todos/{todo_id}", response_model=TodoItem_Pydantic)
def get_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="TODOが見つからない")


@app.post("/todos", response_model=TodoItem_Pydantic)
async def create_todo(res: TodoItemCreate_Pydantic): # <--リクエストボディのデータを受け取る
    new_todo = await TodoItem.create(title=res.title, description=res.description)
    return new_todo # 追加したTODOアイテムを返す

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    todo = await TodoItem.get(id=todo_id)
    if todo:
        await todo.delete()
        return {"message": f"TODO '{todo.title}' を削除しました"}
    raise HTTPException(status_code=404, detail=f"ID {todo_id} のTODOが見つかりません")

@app.put("/todos/{todo_id}", response_model=TodoItem_Pydantic)
async def update_todo(todo_id: int, req: TodoItemUpdate_Pydantic):
    todo = await TodoItem.get(id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"ID {todo_id} のTODOが見つかりません")

    todo.title = req.title if req.title is not None else todo.title
    todo.description = req.description if req.description is not None else todo.description
    todo.completed = req.completed if req.completed is not None else todo.completed
    await todo.save()
    return todo


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["model"]},
    generate_schemas=True,
    add_exception_handlers=True,
)