"""
Лабораторная работа №1. ООП в Python. Обработка исключений.
Форматы XML и JSON.

Вариант 24: управление проектами.
"""

import json
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from exceptions import (
    DataFormatError,
    EmptyTitleError,
    InvalidPriorityError,
    InvalidStatusError,
    PermissionDeniedError,
    ProjectNotFoundError,
    TaskNotFoundError,
    UserNotFoundError,
)
from models import (
    Bug,
    Comment,
    Developer,
    Feature,
    Manager,
    Project,
    Report,
    Role,
    Sprint,
    Tag,
    Team,
)

DATA_DIR = Path("data")
JSON_FILE = DATA_DIR / "project_data.json"
XML_FILE = DATA_DIR / "project_data.xml"


class ProjectService:
    """Сервис управления проектами: CRUD + сохранение/загрузка."""

    def __init__(self) -> None:
        self.users: list = []
        self.teams: list[Team] = []
        self.projects: list[Project] = []
        self._team_counter = 1
        self._project_counter = 1
        self._sprint_counter = 1

    # ---------- CREATE ----------
    def create_user(self, username: str, email: str, role: Role,
                    user_type: str = "developer",
                    skills: list[str] | None = None):
        if user_type == "manager":
            user = Manager(username, email, role)
        elif user_type == "developer":
            user = Developer(username, email, role, skills=skills)
        else:
            raise ValueError(f"Неизвестный тип пользователя: {user_type}")
        self.users.append(user)
        return user

    def create_team(self, name: str, members: list | None = None) -> Team:
        team = Team(name=name, team_id=self._team_counter)
        self._team_counter += 1
        if members:
            for m in members:
                team.add_member(m)
        self.teams.append(team)
        return team

    def create_project(self, name: str, description: str = "",
                       team: Team | None = None) -> Project:
        project = Project(name=name, description=description,
                          project_id=self._project_counter)
        self._project_counter += 1
        if team:
            project.team = team
        self.projects.append(project)
        return project

    def create_sprint(self, project: Project, name: str,
                      start: date, end: date) -> Sprint:
        sprint = Sprint(name=name, start_date=start, end_date=end,
                        sprint_id=self._sprint_counter)
        self._sprint_counter += 1
        project.add_sprint(sprint)
        return sprint

    # ---------- READ ----------
    def find_user(self, user_id: int):
        for u in self.users:
            if u.id == user_id:
                return u
        raise UserNotFoundError(f"Пользователь id={user_id} не найден")

    def find_project(self, project_id: int) -> Project:
        for p in self.projects:
            if p.id == project_id:
                return p
        raise ProjectNotFoundError(f"Проект id={project_id} не найден")

    def find_task(self, project: Project, task_id: int):
        for s in project.sprints:
            for t in s.tasks:
                if t.id == task_id:
                    return t
        raise TaskNotFoundError(f"Задача id={task_id} не найдена в проекте")

    # ---------- UPDATE ----------
    def update_project(self, project_id: int, new_name: str = None,
                       new_description: str = None) -> Project:
        project = self.find_project(project_id)
        if new_name is not None:
            if not new_name.strip():
                raise EmptyTitleError("Новое имя проекта пустое")
            project.name = new_name.strip()
        if new_description is not None:
            project.description = new_description
        return project

    # ---------- DELETE ----------
    def delete_project(self, project_id: int) -> None:
        project = self.find_project(project_id)
        self.projects.remove(project)

    def delete_user(self, user_id: int) -> None:
        user = self.find_user(user_id)
        self.users.remove(user)

    # ---------- JSON ----------
    def save_json(self, path: Path = JSON_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "users": [u.to_dict() for u in self.users],
            "teams": [t.to_dict() for t in self.teams],
            "projects": [p.to_dict() for p in self.projects],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError as exc:
            raise DataFormatError(f"Не удалось записать {path}: {exc}") from exc

    def load_json(self, path: Path = JSON_FILE) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as exc:
            raise DataFormatError(f"Файл {path} не найден") from exc
        except json.JSONDecodeError as exc:
            raise DataFormatError(f"Некорректный JSON в {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise DataFormatError("Ожидался объект с ключами users/teams/projects")
        print(f"Загружено из JSON: пользователей — {len(data.get('users', []))}, "
              f"команд — {len(data.get('teams', []))}, "
              f"проектов — {len(data.get('projects', []))}")

    # ---------- XML ----------
    def save_xml(self, path: Path = XML_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        root = ET.Element("project_service")

        users_el = ET.SubElement(root, "users")
        for u in self.users:
            u_el = ET.SubElement(users_el, "user", type=type(u).__name__)
            ET.SubElement(u_el, "id").text = str(u.id)
            ET.SubElement(u_el, "username").text = u.username
            ET.SubElement(u_el, "email").text = u.email
            ET.SubElement(u_el, "role").text = u.role.name

        teams_el = ET.SubElement(root, "teams")
        for t in self.teams:
            t_el = ET.SubElement(teams_el, "team")
            ET.SubElement(t_el, "id").text = str(t.id)
            ET.SubElement(t_el, "name").text = t.name
            members_el = ET.SubElement(t_el, "members")
            for m in t.members:
                ET.SubElement(members_el, "member").text = m.username

        projects_el = ET.SubElement(root, "projects")
        for p in self.projects:
            p_el = ET.SubElement(projects_el, "project")
            ET.SubElement(p_el, "id").text = str(p.id)
            ET.SubElement(p_el, "name").text = p.name
            ET.SubElement(p_el, "description").text = p.description
            if p.team:
                ET.SubElement(p_el, "team").text = p.team.name
            sprints_el = ET.SubElement(p_el, "sprints")
            for s in p.sprints:
                s_el = ET.SubElement(sprints_el, "sprint")
                ET.SubElement(s_el, "id").text = str(s.id)
                ET.SubElement(s_el, "name").text = s.name
                ET.SubElement(s_el, "start_date").text = s.start_date.isoformat()
                ET.SubElement(s_el, "end_date").text = s.end_date.isoformat()
                tasks_el = ET.SubElement(s_el, "tasks")
                for t in s.tasks:
                    task_el = ET.SubElement(tasks_el, "task", type=t.get_type())
                    ET.SubElement(task_el, "id").text = str(t.id)
                    ET.SubElement(task_el, "title").text = t.title
                    ET.SubElement(task_el, "status").text = t.status
                    ET.SubElement(task_el, "priority").text = t.priority
                    if t.assignee:
                        ET.SubElement(task_el, "assignee").text = t.assignee.username

        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="  ")
            tree.write(path, encoding="utf-8", xml_declaration=True)
        except OSError as exc:
            raise DataFormatError(f"Не удалось записать {path}: {exc}") from exc

    def load_xml(self, path: Path = XML_FILE) -> None:
        try:
            tree = ET.parse(path)
        except FileNotFoundError as exc:
            raise DataFormatError(f"Файл {path} не найден") from exc
        except ET.ParseError as exc:
            raise DataFormatError(f"Ошибка разбора XML {path}: {exc}") from exc

        root = tree.getroot()
        if root.tag != "project_service":
            raise DataFormatError(
                f"Корневой тег должен быть <project_service>, найден <{root.tag}>"
            )
        users_count = len(root.findall("./users/user"))
        teams_count = len(root.findall("./teams/team"))
        projects_count = len(root.findall("./projects/project"))
        print(f"Загружено из XML: пользователей — {users_count}, "
              f"команд — {teams_count}, проектов — {projects_count}")


def reset_counters() -> None:
    """Сбросить счётчики id, чтобы демо начиналось с 1."""
    from models import Comment, Report, Task, TimeLog, User
    Comment._next_id = 1
    Task._next_id = 1
    TimeLog._next_id = 1
    User._next_id = 1
    Report._next_id = 1


def demo_exceptions() -> None:
    """Демонстрация собственных и встроенных исключений."""
    print("\n--- Демонстрация исключений ---")

    # Собственное: пустое имя роли
    try:
        Role("", ["read"])
    except EmptyTitleError as exc:
        print(f"EmptyTitleError: {exc}")

    # Собственное: недопустимый приоритет
    try:
        Feature("Тест", priority="super-high")
    except InvalidPriorityError as exc:
        print(f"InvalidPriorityError: {exc}")

    # Собственное: недопустимый статус
    try:
        bug = Bug("Падение при старте")
        bug.change_status("flying")
    except InvalidStatusError as exc:
        print(f"InvalidStatusError: {exc}")

    # Собственное: нет прав на назначение
    try:
        manager_role = Role("viewer", ["read"])
        manager = Manager("Гость", "guest@example.com", manager_role)
        dev_role = Role("dev", ["read", "write"])
        dev = Developer("Разраб", "dev@example.com", dev_role)
        task = Feature("Что-то")
        manager.assign_task(task, dev)
    except PermissionDeniedError as exc:
        print(f"PermissionDeniedError: {exc}")

    # Встроенное: деление на ноль
    try:
        _ = 100 / 0
    except ZeroDivisionError as exc:
        print(f"ZeroDivisionError: {exc}")

    # Встроенное: отрицательные часы в TimeLog
    try:
        role = Role("dev", ["read"])
        user = Developer("X", "x@example.com", role)
        user.log_time(Feature("F"), hours=-3)
    except ValueError as exc:
        print(f"ValueError: {exc}")

    # Собственное: задача не найдена
    try:
        service = ProjectService()
        project = service.create_project("П")
        service.find_task(project, task_id=9999)
    except TaskNotFoundError as exc:
        print(f"TaskNotFoundError: {exc}")

    # Собственное: файл не найден (с перехватом DataFormatError)
    try:
        service = ProjectService()
        service.load_json(Path("no_such_file.json"))
    except DataFormatError as exc:
        print(f"DataFormatError: {exc}")

    # try/else/finally
    try:
        x = int("42")
    except ValueError:
        print("Это не число")
    else:
        print(f"else: успешное преобразование, x = {x}")
    finally:
        print("finally: выполняется всегда")


def build_demo_service() -> ProjectService:
    """Собрать демонстрационный набор данных."""
    service = ProjectService()

    admin_role = Role("admin", ["read", "write", "assign_task", "delete"])
    manager_role = Role("manager", ["read", "write", "assign_task"])
    dev_role = Role("developer", ["read", "write"])

    manager = service.create_user("ivanov", "ivanov@corp.ru", manager_role,
                                  user_type="manager")
    dev1 = service.create_user("petrov", "petrov@corp.ru", dev_role,
                               user_type="developer",
                               skills=["Python", "Django"])
    dev2 = service.create_user("sidorova", "sidorova@corp.ru", dev_role,
                               user_type="developer",
                               skills=["JS", "React"])

    team = service.create_team("Backend", members=[manager, dev1, dev2])
    project = service.create_project("Интернет-магазин",
                                     description="Новый маркетплейс",
                                     team=team)

    sprint = service.create_sprint(
        project, "Sprint #1",
        start=date(2024, 10, 1), end=date(2024, 10, 14)
    )

    f1 = Feature("Корзина покупателя",
                 description="Добавление и удаление товаров",
                 priority="high",
                 acceptance_criteria="Товар добавляется и удаляется",
                 story_points=5)
    f2 = Feature("Личный кабинет", priority="medium", story_points=3)
    b1 = Bug("Падение при пустом поиске", priority="critical",
             severity="blocker", steps_to_reproduce="Открыть поиск → Enter")

    sprint.add_task(f1)
    sprint.add_task(f2)
    sprint.add_task(b1)

    dev1.take_task(f1)
    dev1.log_time(f1, 4.5, "Вёрстка корзины")
    dev1.log_time(f1, 2.0, "Правки по UX")
    f1.change_status("review")

    dev2.take_task(b1)
    dev2.log_time(b1, 1.5)
    b1.change_status("done")

    f1.add_comment(Comment(manager, "Заменить иконку корзины"))
    f1.add_comment(Comment(dev1, "Готово, залил в ветку feature/cart"))

    f1.tags.append(Tag("frontend", "#3498db"))
    f1.tags.append(Tag("ux", "#9b59b6"))

    report = Report(project, period="2024-10")
    report.generate()

    print("=" * 60)
    print("ДЕМОНСТРАЦИОННЫЙ НАБОР ДАННЫХ")
    print("=" * 60)
    for u in service.users:
        print(f"  {u.get_info()}")
        print(f"    {u.get_dashboard()}")
    print(f"  Команда: {team}")
    print(f"  Проект: {project}, прогресс: {project.get_progress()}%")
    print(f"  Sprint burndown: {sprint.get_burndown()}")
    print(f"  Отчёт: {report.data}")
    print("=" * 60)

    return service


def demo_crud(service: ProjectService) -> None:
    """Показать Create / Read / Update / Delete."""
    print("\n--- CRUD ---")

    print(f"CREATE: проектов стало {len(service.projects)}")
    p = service.create_project("Тестовый проект", "Временный")
    print(f"  создан: {p}")

    print("READ:", service.find_project(p.id))

    service.update_project(p.id, new_name="Тестовый проект v2")
    print(f"UPDATE: {service.find_project(p.id).name}")

    service.delete_project(p.id)
    print(f"DELETE: проектов стало {len(service.projects)}")


def main() -> None:
    demo_exceptions()
    reset_counters()

    service = build_demo_service()
    demo_crud(service)

    print("\n--- Сохранение в JSON и XML ---")
    service.save_json()
    service.save_xml()
    print(f"Записано: {JSON_FILE}, {XML_FILE}")

    print("\n--- Чтение из файлов ---")
    service2 = ProjectService()
    service2.load_json()
    service2.load_xml()


if __name__ == "__main__":
    main()
