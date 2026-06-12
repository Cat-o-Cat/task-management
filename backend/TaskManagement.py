from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskCreate(BaseModel):
    title: str
    description: str = ""

class TaskUpdate(BaseModel):
    title: str
    description: str = ""
    completed: bool

class AssistantQuery(BaseModel):
    query: str

tasks_db = []

client = OpenAI(
    api_key="sk-bf7d4b800b484b8f95d39010228d3cb5",
    base_url="https://api.deepseek.com/beta",
)

def generate_new_id(): #该部分由AI辅助生成，在项目说明里会给出说明，主要利用AI给出开发思路和代码检查
    if len(tasks_db) == 0:
        return 1
    max_id = 0
    for task in tasks_db:
        if task["id"] > max_id:
            max_id = task["id"]
    return max_id + 1

def find_task_index(task_id: int):
    for i in range(len(tasks_db)):
        if tasks_db[i]["id"] == task_id:
            return i
    return -1

@app.post("/tasks")#该部分由AI给出实现思路，自己尝试写出代码并由AI审核正确性
def create_task(task_data: TaskCreate):
    new_id = generate_new_id()
    new_task = {
        "id": new_id,
        "title": task_data.title,
        "description": task_data.description,
        "completed": False,
    }
    tasks_db.append(new_task)
    return new_task

@app.get("/tasks")
def list_tasks(page: int = 1, page_size: int = 5):
    total = len(tasks_db)
    total_pages = total // page_size
    if (total % page_size != 0):
        total_pages += 1
    offset = (page - 1) * page_size
    data = tasks_db[offset:offset + page_size]
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": data
    }

@app.post("/tasks/update/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate):
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="任务未找到")
    task = tasks_db[idx]
    task["title"] = task_data.title
    task["description"] = task_data.description
    task["completed"] = task_data.completed
    return task

@app.post("/tasks/delete/{task_id}")#该部分由AI辅助生成，在项目说明里会详细说明，主要利用AI给出开发思路和代码检查
def delete_task(task_id: int):
    idx = find_task_index(task_id)
    if idx == -1:
        raise HTTPException(status_code=404, detail="任务未找到")
    deleted = tasks_db.pop(idx)
    return {"message": "删除成功", "deleted_id": deleted["id"]}

@app.post("/tasks/{task_id}/summarize")
def summarize_task(task_id: int):
    task = None
    for t in tasks_db:
        if t["id"] == task_id:
            task = t
            break
    if task is None:
        raise HTTPException(status_code=404, detail="任务未找到")
    if task.get("description") == "":
        return {"summary": "无描述内容，无法生成摘要。"}

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "你是一个任务助手，请简洁总结任务。"},
                {"role": "user", "content": f"总结：{task['description']}"},
            ]
        )
        return {"summary": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/assistant/ask")
def assistant_ask(query_data: AssistantQuery):
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "你是个智能助手。"},
                {"role": "user", "content": query_data.query}
            ]
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")