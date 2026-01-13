from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Analysis:
    tldr: str
    hypotheses: list[str]
    next_steps: list[str]
    questions: list[str]


def _flatten_signals(signals: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for s in signals:
        t = s.get("type", "")
        src = s.get("source", "")
        payload = s.get("payload", {})
        parts.append(f"[{t}/{src}] {payload}")
    return "\n".join(parts).lower()


def analyze_incident(title: str, signals: list[dict[str, Any]]) -> Analysis:
    """
    MVP "AI": эвристики + готовые DevOps шаги.
    Позже заменим на реальный LLM, интерфейс не изменится.
    """
    text = (title or "").lower() + "\n" + _flatten_signals(signals)

    if "nexus" in text:
        return Analysis(
            tldr="Похоже на проблему с Nexus (недоступен/не стартует/ошибка репозитория).",
            hypotheses=[
                "Сервис Nexus упал или не стартует (systemd/crash loop).",
                "Проблема с диском/местом/permission на data-dir.",
                "Проблема с сетью/DNS/сертификатами до Nexus.",
            ],
            next_steps=[
                "systemctl status dos-nexus-ci.service --no-pager",
                "journalctl -u dos-nexus-ci.service -n 200 --no-pager",
                "df -h && du -sh /opt/nexus* /nexus-data* 2>/dev/null",
                "curl -vk https://<nexus-host>/ -o /dev/null",
            ],
            questions=[
                "Это Nexus CI или Nexus SD? На каком хосте/кластере?",
                "Что меняли перед падением (обновления/деплой/сертификаты)?",
                "Какая ошибка в последних строках лога (java exception / OOM / file not found)?",
            ],
        )

    if "docker" in text and ("failed" in text or "daemon" in text):
        return Analysis(
            tldr="Похоже на проблему с Docker daemon (конфиг/запуск/совместимость).",
            hypotheses=[
                "Ошибка в /etc/docker/daemon.json или несовместимая опция.",
                "Проблема с storage driver/overlay2/диском.",
                "Конфликт версий docker/containerd.",
            ],
            next_steps=[
                "systemctl status docker --no-pager",
                "journalctl -u docker -n 200 --no-pager",
                "cat /etc/docker/daemon.json",
                "docker info || true",
            ],
            questions=[
                "Какая ОС/версия docker?",
                "Что меняли перед ошибкой (daemon.json/ansible роль)?",
            ],
        )

    return Analysis(
        tldr="Недостаточно данных — пока общий разбор.",
        hypotheses=[
            "Сетевой сбой/таймаут до зависимости.",
            "Ошибка авторизации/секретов.",
            "Регресс после релиза/изменения.",
        ],
        next_steps=[
            "Собери логи сервиса за последние 15 минут.",
            "Проверь 4xx/5xx и таймауты до внешних зависимостей.",
            "Сопоставь время алерта с деплоями/изменениями.",
        ],
        questions=[
            "Какой сервис/окружение?",
            "Есть ли конкретная ошибка в логах?",
            "Что изменилось перед началом проблем?",
        ],
    )

