"""
Модели предметной области «Управление проектами».
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from exceptions import (
    EmptyTitleError,
    InvalidPriorityError,
    InvalidStatusError,
    PermissionDeniedError,
)

VALID_STATUSES = ("new", "in_progress", "review", "done", "closed")
VALID_PRIORITIES = ("low", "medium", "high", "critical")


class Role:
    """Роль пользователя с набором прав."""

    def __init__(self, name: str, permissions: list[str]) -> None:
        if not name or not name.strip():
            raise EmptyTitleError("Название роли не может быть пустым")
        self.name = name.strip()
        self.permissions = list(permissions)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "permissions": self.permissions}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Role":
        return cls(name=data["name"], permissions=data.get("permissions", []))

    def __repr__(self) -> str:
        return f"Role({self.name!r})"


class User(ABC):
    """Абстрактный пользователь системы."""

    _next_id = 1

    def __init__(self, username: str, email: str, role: Role) -> None:
        if not username or not username.strip():
            raise EmptyTitleError("Имя пользователя не может быть пустым")
        self.id = User._next_id
        User._next_id += 1
        self.username = username.strip()
        self.email = email
        self.role = role

    def get_info(self) -> str:
        return f"[{self.id}] {self.username} <{self.email}> — {self.role.name}"

    @abstractmethod
    def get_dashboard(self) -> str:
        ...

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": type(self).__name__,
            "username": self.username,
            "email": self.email,
            "role": self.role.to_dict(),
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, username={self.username!r})"


class Manager(User):
    """Менеджер проектов."""

    def __init__(self, username: str, email: str, role: Role) -> None:
        super().__init__(username, email, role)
        self.managed_projects: list[Project] = []

    def create_project(self, name: str, description: str = "") -> "Project":
        project = Project(name=name, description=description)
        self.managed_projects.append(project)
        return project

    def assign_task(self, task: "Task", developer: "Developer") -> None:
        if not self.role.has_permission("assign_task"):
            raise PermissionDeniedError(
                f"Роль {self.role.name!r} не может назначать задачи"
            )
        task.assignee = developer
        developer.assigned_tasks.append(task)

    def get_dashboard(self) -> str:
        return f"Панель менеджера: {len(self.managed_projects)} проектов"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["managed_projects"] = [p.name for p in self.managed_projects]
        return data


class Developer(User):
    """Разработчик."""

    def __init__(self, username: str, email: str, role: Role,
                 skills: list[str] | None = None) -> None:
        super().__init__(username, email, role)
        self.skills = list(skills) if skills else []
        self.assigned_tasks: list[Task] = []

    def take_task(self, task: "Task") -> None:
        task.assignee = self
        task.change_status("in_progress")
        if task not in self.assigned_tasks:
            self.assigned_tasks.append(task)

    def log_time(self, task: "Task", hours: float, note: str = "") -> "TimeLog":
        # Часы должны быть положительными, иначе лог теряет смысл
        if hours <= 0:
            raise ValueError(f"hours должно быть > 0, получено {hours}")
        log = TimeLog(user=self, hours=hours, note=note)
        task.time_logs.append(log)
        return log

    def get_dashboard(self) -> str:
        return f"Панель разработчика: {len(self.assigned_tasks)} задач"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["skills"] = self.skills
        data["assigned_tasks"] = [t.id for t in self.assigned_tasks]
        return data


class Team:
    """Команда проекта."""

    def __init__(self, name: str, team_id: int) -> None:
        if not name or not name.strip():
            raise EmptyTitleError("Название команды не может быть пустым")
        self.id = team_id
        self.name = name.strip()
        self.members: list[User] = []

    def add_member(self, user: User) -> None:
        if user not in self.members:
            self.members.append(user)

    def remove_member(self, user: User) -> None:
        if user in self.members:
            self.members.remove(user)

    def list_members(self) -> list[User]:
        return list(self.members)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "members": [u.username for u in self.members],
        }

    def __repr__(self) -> str:
        return f"Team(id={self.id}, name={self.name!r})"


class Project:
    """Проект."""

    def __init__(self, name: str, description: str = "",
                 project_id: int = 0) -> None:
        if not name or not name.strip():
            raise EmptyTitleError("Название проекта не может быть пустым")
        self.id = project_id
        self.name = name.strip()
        self.description = description
        self.team: Team | None = None
        self.sprints: list[Sprint] = []

    def add_sprint(self, sprint: "Sprint") -> None:
        sprint.project = self
        self.sprints.append(sprint)

    def get_progress(self) -> float:
        tasks = [t for s in self.sprints for t in s.tasks]
        if not tasks:
            return 0.0
        done = sum(1 for t in tasks if t.status in ("done", "closed"))
        return round(done / len(tasks) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "team": self.team.name if self.team else None,
            "sprints": [s.to_dict() for s in self.sprints],
        }

    def __repr__(self) -> str:
        return f"Project(id={self.id}, name={self.name!r})"


class Sprint:
    """Спринт — итерация проекта."""

    def __init__(self, name: str, start_date: date, end_date: date,
                 sprint_id: int = 0) -> None:
        if not name or not name.strip():
            raise EmptyTitleError("Название спринта не может быть пустым")
        if end_date < start_date:
            raise ValueError("Дата окончания спринта раньше даты начала")
        self.id = sprint_id
        self.name = name.strip()
        self.start_date = start_date
        self.end_date = end_date
        self.tasks: list[Task] = []
        self.project: Project | None = None

    def add_task(self, task: "Task") -> None:
        task.sprint = self
        self.tasks.append(task)

    def get_burndown(self) -> float:
        # Считаем только незакрытые задачи
        remaining = sum(
            getattr(t, "story_points", 0)
            for t in self.tasks if t.status not in ("done", "closed")
        )
        return float(remaining)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def __repr__(self) -> str:
        return f"Sprint(id={self.id}, name={self.name!r})"


class Task(ABC):
    """Абстрактная задача."""

    _next_id = 1

    def __init__(self, title: str, description: str = "",
                 priority: str = "medium") -> None:
        if not title or not title.strip():
            raise EmptyTitleError("Название задачи не может быть пустым")
        if priority not in VALID_PRIORITIES:
            raise InvalidPriorityError(
                f"Недопустимый приоритет {priority!r}"
            )
        self.id = Task._next_id
        Task._next_id += 1
        self.title = title.strip()
        self.description = description
        self.status = "new"
        self.priority = priority
        self.assignee: User | None = None
        self.sprint: Sprint | None = None
        self.tags: list[Tag] = []
        self.comments: list[Comment] = []
        self.time_logs: list[TimeLog] = []

    def change_status(self, new_status: str) -> None:
        if new_status not in VALID_STATUSES:
            raise InvalidStatusError(
                f"Недопустимый статус {new_status!r}"
            )
        self.status = new_status

    def add_comment(self, comment: "Comment") -> None:
        self.comments.append(comment)

    def total_hours(self) -> float:
        return round(sum(log.hours for log in self.time_logs), 2)

    @abstractmethod
    def get_type(self) -> str:
        ...

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.get_type(),
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assignee": self.assignee.username if self.assignee else None,
            "tags": [t.name for t in self.tags],
            "comments": [c.to_dict() for c in self.comments],
            "time_logs": [t.to_dict() for t in self.time_logs],
            "total_hours": self.total_hours(),
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, title={self.title!r})"


class Bug(Task):
    """Баг."""

    def __init__(self, title: str, description: str = "",
                 priority: str = "high", severity: str = "major",
                 steps_to_reproduce: str = "") -> None:
        super().__init__(title, description, priority)
        self.severity = severity
        self.steps_to_reproduce = steps_to_reproduce

    def get_type(self) -> str:
        return "bug"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["severity"] = self.severity
        data["steps_to_reproduce"] = self.steps_to_reproduce
        return data


class Feature(Task):
    """Фича."""

    def __init__(self, title: str, description: str = "",
                 priority: str = "medium", acceptance_criteria: str = "",
                 story_points: int = 1) -> None:
        super().__init__(title, description, priority)
        # story_points используется в burndown, отрицательным быть не может
        if story_points < 0:
            raise ValueError(f"story_points < 0: {story_points}")
        self.acceptance_criteria = acceptance_criteria
        self.story_points = story_points

    def get_type(self) -> str:
        return "feature"

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["acceptance_criteria"] = self.acceptance_criteria
        data["story_points"] = self.story_points
        return data


class Comment:
    """Комментарий к задаче."""

    _next_id = 1

    def __init__(self, author: User, text: str) -> None:
        if not text or not text.strip():
            raise EmptyTitleError("Текст комментария не может быть пустым")
        self.id = Comment._next_id
        Comment._next_id += 1
        self.author = author
        self.text = text.strip()
        self.created_at = datetime.now()

    def edit(self, new_text: str) -> None:
        if not new_text or not new_text.strip():
            raise EmptyTitleError("Новый текст комментария пуст")
        self.text = new_text.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "author": self.author.username,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"Comment(id={self.id}, author={self.author.username!r})"


class Tag:
    """Тег задачи."""

    def __init__(self, name: str, color: str = "#cccccc") -> None:
        if not name or not name.strip():
            raise EmptyTitleError("Название тега не может быть пустым")
        self.name = name.strip()
        self.color = color

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "color": self.color}

    def __repr__(self) -> str:
        return f"Tag({self.name!r})"


class TimeLog:
    """Запись о затраченном времени."""

    _next_id = 1

    def __init__(self, user: User, hours: float, note: str = "") -> None:
        if hours <= 0:
            raise ValueError(f"hours должно быть > 0: {hours}")
        self.id = TimeLog._next_id
        TimeLog._next_id += 1
        self.user = user
        self.hours = float(hours)
        self.date = date.today()
        self.note = note

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user": self.user.username,
            "hours": self.hours,
            "date": self.date.isoformat(),
            "note": self.note,
        }

    def __repr__(self) -> str:
        return f"TimeLog(id={self.id}, user={self.user.username!r}, hours={self.hours})"


class Report:
    """Отчёт по проекту."""

    _next_id = 1

    def __init__(self, project: Project, period: str) -> None:
        if not period or not period.strip():
            raise EmptyTitleError("Период отчёта не может быть пустым")
        self.id = Report._next_id
        Report._next_id += 1
        self.project = project
        self.period = period.strip()
        self.data: dict[str, Any] = {}

    def generate(self) -> dict[str, Any]:
        tasks = [t for s in self.project.sprints for t in s.tasks]
        by_status: dict[str, int] = {}
        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
        self.data = {
            "project": self.project.name,
            "period": self.period,
            "total_tasks": len(tasks),
            "progress_percent": self.project.get_progress(),
            "by_status": by_status,
            "total_hours": round(sum(t.total_hours() for t in tasks), 2),
        }
        return self.data

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project": self.project.name,
            "period": self.period,
            "data": self.data,
        }

    def __repr__(self) -> str:
        return f"Report(id={self.id}, project={self.project.name!r})"