Учебный REST-сервис на FastAPI для управления списком задач.
Данные хранятся в JSON-файле.

---

## Развёртывание

### Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
или c uv

```bash
uv sync
```
### Запуск

```bash
uv run uvicorn main:app --reload
```

### Docker

```bash
docker build -t tasks-api:latest .
docker run -d -p 8000:80 tasks-api:latest
```

---

## Схемы (Pydantic)

### `STaskAdd` — создание задачи

| Поле          | Тип   | Описание            |
|---------------|-------|---------------------|
| `name`        | `str` | Название задачи     |
| `description` | `str` | Описание задачи     |

### `STaskUpdate` — обновление задачи

| Поле          | Тип   | Описание            |
|---------------|-------|---------------------|
| `name`        | `str` | Название задачи     |
| `description` | `str` | Описание задачи     |

### `STaskGet` — ответ сервера

| Поле          | Тип   |
|---------------|-------|
| `id`          | `int` |
| `name`        | `str` |
| `description` | `str` |

---

## Формат хранения данных

В качестве хранилища используется JSON-файл.

### Массив объектов:

| Поле          | Тип   | Описание             |
|---------------|-------|----------------------|
| `id`          | `int` | Идентификатор задачи |
| `name`        | `str` | Название задачи      |
| `description` | `str` | Описание задачи      |
---

## Методы `TaskTepository`

| Метод | Параметры | Возвращает | Ошибки |
|---|---|---|---|
| `add_one(new_task)` | `new_task: STaskAdd` — новая задача | `int` — присвоенный ID (или `None` при сбое хранилища) | `None` — файл недоступен |
| `find_all()` | — | `list[STaskGet]` — все записи (или `None` при сбое хранилища) | `None` — файл недоступен |
| `update_task(task_id, task_update)` | `task_id: int` — идентификатор задачи<br>`task_update: STaskUpdate` — новые значения полей | `STaskUpdate` — состояние после обновления (или `None`) | `None` — файл недоступен или ID не найден |
| `delete_task(task_id)` | `task_id: int` — уникальный идентификатор задачи | `bool` — `True`, если удалено; `False`, если не найдено или сбой хранилища | `False` — файл недоступен или ID не найден |

> *Репозиторий не выбрасывает исключений, а возвращает `None`/`False`. Эндпоинты интерпретируют эти значения как ошибки и возвращают HTTP-коды.*

---

## Эндпоинты

| Метод | Путь | Прототип функции | Ответ |
|---|---|---|---|
| `POST` | `/tasks` | `add_task(task: STaskAdd) -> int` | `int` — id созданной задачи |
| `GET` | `/tasks` | `get_tasks() -> list[STaskGet]` | `list[STaskGet]` — список задач |
| `DELETE` | `/tasks` | `delete_task(task_id: int) -> int` | `int` — id удалённой задачи |
| `PATCH` | `/tasks/{task_id}` | `edit_task(task_id: int, task_data: STaskUpdate) -> STaskUpdate` | `STaskUpdate` — обновлённая запись |

`task_id` — целое число `> 0`. При нарушении — `422`.

---

## Коды ошибок

| Код | Причина |
|---|---|
| `404` | Задача с указанным `id` не найдена (при `DELETE` и `PATCH`) |
| `422` | Невалидное тело запроса или `task_id <= 0` |
| `500` | Не удалось прочитать данные из хранилища (`POST`, `GET`) |
