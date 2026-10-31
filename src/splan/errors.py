"""Fehlerklassen mit dem Exit-Code aus INTERFACE.md."""

from __future__ import annotations


class SplanError(Exception):
    code = 3

    def __init__(self, message: str, next_step: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.next_step = next_step


class UsageError(SplanError):
    code = 2


class NotFoundError(SplanError):
    code = 1


class SourceError(SplanError):
    code = 3


class AccessDeniedError(SplanError):
    code = 4


class ConfigError(SplanError):
    code = 2
