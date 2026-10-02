"""
Собственные исключения предметной области «Управление проектами».
"""


class ProjectError(Exception):
    """Базовое исключение для всех ошибок предметной области."""


class ValidationError(ProjectError):
    """Некорректные данные объекта."""


class InvalidStatusError(ValidationError):
    """Недопустимый статус задачи."""


class InvalidPriorityError(ValidationError):
    """Недопустимый приоритет задачи."""


class EmptyTitleError(ValidationError):
    """Пустое название проекта/задачи/команды."""


class NotFoundError(ProjectError):
    """Объект не найден в хранилище."""


class TaskNotFoundError(NotFoundError):
    """Задача с указанным id не найдена."""


class UserNotFoundError(NotFoundError):
    """Пользователь с указанным id не найден."""


class ProjectNotFoundError(NotFoundError):
    """Проект с указанным id не найден."""


class PermissionDeniedError(ProjectError):
    """Недостаточно прав для выполнения операции."""


class DataFormatError(ProjectError):
    """Ошибка чтения или записи файла данных."""