from contextlib import asynccontextmanager
import os
from pydantic import BaseModel, ConfigDict
from typing import Annotated
from fastapi import Depends, Path, status
from fastapi.exceptions import HTTPException
from fastapi import FastAPI

from utils import json_to_dict_list, dict_list_to_json


STORAGE = "./storage.json"


class STaskAdd(BaseModel):
    """Схема данных для создания новой задачи."""
    name: str
    description: str


class STaskUpdate(BaseModel):
    """Схема данных для частичного обновления задачи."""
    name: str
    description: str


class STaskGet(STaskAdd):
    """Схема задачи в том виде, в котором она возвращается клиенту."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str


class TaskTepository:
    """Репозиторий для работы с задачами."""

    @classmethod
    def add_one(cls, new_task: STaskAdd) -> int | None:
        """Создать новую задачу и сохранить её в хранилище.

        Args:
            new_task: Валидированные данные новой задачи.

        Returns:
            int | None: Присвоенный задаче ID или None при ошибке чтения/записи.
        """
        data = json_to_dict_list(filename=STORAGE)

        if data is None:
            return None

        new_id = max([item["id"] for item in data], default=0) + 1
        new_item = {
            "id": new_id,
            **new_task.model_dump()
        }
        data.append(new_item)
        _ = dict_list_to_json(filename=STORAGE, dict_list=data)
        return new_id

    @classmethod
    def find_all(cls) -> list[STaskGet] | None:
        """Получить список всех задач.

        Returns:
            list[STaskGet] | None: Список задач или None при ошибке чтения.
        """
        data = json_to_dict_list(filename=STORAGE)

        if data is None:
            return None

        return [STaskGet.model_validate(item) for item in data]

    @classmethod
    def delete_task(cls, task_id: int) -> bool:
        """Удалить задачу по её идентификатору.

        Args:
            task_id: Уникальный идентификатор задачи.

        Returns:
            bool: True, если задача найдена и удалена; False — если не найдена
            или произошла ошибка чтения/записи.
        """
        data = json_to_dict_list(filename=STORAGE)

        if data is None:
            return False

        for item in data:
            if item.get("id") == task_id:
                data.remove(item)
                _ = dict_list_to_json(filename=STORAGE, dict_list=data)
                return True

        return False

    @classmethod
    def update_task(cls, task_id: int, task_update: STaskUpdate) -> STaskUpdate | None:
        """Частично обновить задачу по её идентификатору.

        Args:
            task_id: Уникальный идентификатор задачи.
            task_update: Новые значения полей задачи.

        Returns:
            STaskUpdate | None: Обновлённая запись (состояние после обновления)
            или None, если задача не найдена / произошла ошибка чтения.
        """
        data = json_to_dict_list(filename=STORAGE)

        if data is None:
            return None

        for item in data:
            if item.get("id") == task_id:
                # exclude_unset=True — обновляем только явно переданные поля
                item.update(task_update.model_dump(exclude_unset=True))
                _ = dict_list_to_json(filename=STORAGE, dict_list=data)
                return STaskUpdate.model_validate(item)

        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения.

    На старте создаёт пустой JSON-файл хранилища, если его ещё нет.
    При завершении выводит сообщение в консоль.
    """
    if not os.path.exists(STORAGE):
        with open(STORAGE, 'w', encoding='utf-8') as file:
            file.write("[]")
    yield
    print("closing")


app = FastAPI(lifespan=lifespan)


@app.post("/tasks")
async def add_task(task: Annotated[STaskAdd, Depends()]) -> int:
    """Создать новую задачу.

    Args:
        task: Данные новой задачи (передаются через Depends, т.е. из query-параметров).

    Returns:
        int: ID созданной задачи.

    Raises:
        HTTPException: 500, если не удалось прочитать или записать данные в хранилище.
    """
    task_id = TaskTepository.add_one(task)
    if task_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read data from storage..."
        )
    return task_id


@app.get("/tasks")
async def get_tasks() -> list[STaskGet]:
    """Получить список всех задач.

    Returns:
        list[STaskGet]: Список задач.

    Raises:
        HTTPException: 500, если не удалось прочитать данные из хранилища.
    """
    tasks = TaskTepository.find_all()
    if tasks is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read data from storage..."
        )
    return tasks


@app.delete("/tasks")
async def delete_task(task_id: int) -> int:
    """Удалить задачу по её идентификатору.

    Args:
        task_id: Идентификатор задачи (передаётся как query-параметр).

    Returns:
        int: Идентификатор удалённой задачи.

    Raises:
        HTTPException: 404, если задача с таким ID не найдена.
    """
    deleted = TaskTepository.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return deleted


@app.patch("/tasks/{task_id}")
async def edit_task(
    task_id: Annotated[int, Path(gt=0)],
    task_data: STaskUpdate
) -> STaskUpdate:
    """Частично обновить задачу по её идентификатору.

    Args:
        task_id: Идентификатор задачи, строго больше 0 (path-параметр).
        task_data: Новые значения полей (можно передать только часть).

    Returns:
        STaskUpdate: Обновлённая запись.

    Raises:
        HTTPException: 404, если задача не найдена;
            422, если task_id <= 0 или тело запроса невалидно.
    """
    old_task = TaskTepository.update_task(task_id, task_data)
    if old_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return old_task


def main():
    pass


if __name__ == "__main__":
    main()
