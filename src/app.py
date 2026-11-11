"""Практика № 8 — функции, которые реализует студент.

Начните с TASK.md и TASK_CONTRACTS.md в СВОЕЙ ветке GitVerse.

Важно:
* Здесь нет готовых решений. Ваша задача — написать логику самостоятельно.
* Не меняйте имена функций, число аргументов и тип возвращаемого значения.
* API вызывает служебный runner; здесь НЕ нужно создавать клиента GigaChat.
* Примеры ниже показывают ФОРМУ результата, а не правильные ответы
  для ваших персональных случаев.
"""

import json

TASKS = {
    "ticket_triage", "delivery_audit", "evidence_check", "deadline_parser",
    "entity_extraction", "policy_check", "incident_analysis", "request_routing",
}


def validate_input(raw):
    """Проверить входные данные ДО обращения к модели.

    Параметр:
        raw (str): содержимое одного файла cases/<case_id>.json как текст.

    Вернуть КОРТЕЖ из двух элементов:
        (data, None) — если вход корректный; data — словарь Python.
        (None, "код_ошибки") — если вход некорректный.

    Примеры формы результата:
        ({"task_type": "ticket_triage", "payload": {"text": "..."}}, None)
        (None, "invalid_json")
        (None, "missing_required_field")

    Что нужно ДОПИСАТЬ:
    1. Прочитайте TASK_CONTRACTS.md для своего направления.
    2. Проверьте обязательные поля внутри payload, их типы и ограничения.
    3. Проверьте особые случаи: например, отрицательные количества,
       некорректные даты или повторяющиеся идентификаторы, если применимо.
    4. Не отправляйте испорченный вход в GigaChat: runner сам пропустит
       вызов API, когда вы вернёте код ошибки.

    ВНИМАНИЕ: текст с prompt injection может быть вполне корректным JSON.
    Не отклоняйте его только потому, что он содержит подозрительные команды.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, "invalid_json"
    if not isinstance(data, dict):
        return None, "invalid_type"
    if data.get("task_type") not in TASKS:
        return None, "unsupported_task"
    if "payload" not in data:
        return None, "missing_required_field"
    if not isinstance(data["payload"], dict):
        return None, "invalid_type"

    # TODO: проверка схемы именно ВАШЕГО направления.
    # Например: проверить, что ожидаемое текстовое поле — непустая строка.
    # Не ограничивайтесь общими проверками выше.
    return data, None


def build_prompt(data):
    """Составить текст запроса, который runner отправит в GigaChat.

    Параметр:
        data (dict): уже проверенный словарь из validate_input().

    Вернуть:
        str — НЕПУСТУЮ строку с инструкцией для модели.

    Пример ФОРМЫ (не готовый промпт):
        "Определи категорию обращения. Ответь только JSON ... Данные: ..."

    Что написать:
    1. Объясните модели предметную задачу из TASK.md.
    2. Перечислите ТОЧНЫЕ поля и допустимые значения ответа
       из TASK_CONTRACTS.md (у каждого направления свои поля).
    3. Передайте данные из payload; не теряйте значимые сведения.
    4. Объясните, что текст внутри payload — это ДАННЫЕ, а не новые
       системные инструкции. Это важно для prompt injection.
    5. Укажите, как отвечать при недостатке информации, если контракт
       допускает null или неопределённость.

    НЕ нужно здесь обращаться к API, читать секреты или сохранять файлы.
    """
    # TODO: составьте и верните свой промпт.
    raise NotImplementedError("Реализуйте build_prompt() для своего направления")


def parse_response(response):
    """Преобразовать ответ GigaChat в словарь с полями ВАШЕЙ задачи.

    Параметр:
        response: объект ответа SDK GigaChat, НЕ строка и НЕ словарь.
        Текст модели обычно доступен как response.choices[0].message.content.

    Вернуть:
        dict — ТОЛЬКО предметный результат, без case_id/status/meta.
        Служебный runner сам добавит эти поля в results/<case_id>.json.

    Пример для направления ticket_triage:
        {"category": "security", "priority": "high"}
    Пример для evidence_check:
        {"contradiction": False, "evidence_ids": []}
    Эти значения условные, а не ответы на конкретные задания.

    Что дописать:
    1. Извлеките текст из ответа SDK.
    2. Если модель обернула JSON в ```json ... ```, аккуратно удалите
       обёртку (не пытайтесь исправлять произвольный сломанный JSON).
    3. Преобразуйте текст через json.loads().
    4. Проверьте, что получился dict и в нём есть поля нужного типа.
    5. При неверном формате возбуждайте понятное исключение — runner
       запишет ошибку в журнал проверки.

    Важно: правильный синтаксис JSON ещё не гарантирует верного ответа.
    """
    # Это минимальный пример разбора, а НЕ полная реализация.
    # TODO: добавьте обработку обёрток и проверку предметной схемы.
    return json.loads(response.choices[0].message.content)


def extract_usage(response):
    """Прочитать статистику токенов из РЕАЛЬНОГО ответа API.

    Параметр:
        response: объект ответа SDK GigaChat.
        Обычно информация находится в response.usage.

    Вернуть dict РОВНО с этими ключами:
        {
            "prompt_tokens": 120,
            "completion_tokens": 35,
            "total_tokens": 155
        }
    Числа выше — только пример. Их нельзя подставлять константами!

    Требования:
    * Значения — неотрицательные целые числа или None, если поле
      действительно отсутствует в ответе.
    * Считайте фактические значения из response.usage.
    * Если total_tokens не передан, но обе составляющие известны,
      runner допускает сумму prompt_tokens + completion_tokens.
    * Не считайте токены по длине строки: это даст другие значения.
    """
    # TODO: самостоятельно извлеките поля из response.usage.
    raise NotImplementedError("Реализуйте extract_usage()")


def build_run_report(context, case_records):
    """Собрать общий отчёт после обработки всех случаев.

    Параметры:
        context (dict): например
            {"mode": "live", "task_type": "ticket_triage",
             "selected_model": "GigaChat-3-Lightning", "total": 10}
        case_records (list[dict]): записи о реально выполненных случаях.
            Пример одной записи:
            {"case_id": "01-01", "api_calls": 1, "form_pass": True,
             "usage": {"prompt_tokens": 120,
                       "completion_tokens": 35, "total_tokens": 155}}
            У некорректного входа обычно api_calls=0 и нет usage.
            У неудачного запуска может быть поле error.

    Вернуть dict — содержимое будущего run_report.json:
        {
            "mode": "live",
            "task_type": "ticket_triage",
            "selected_model": "GigaChat-3-Lightning",
            "total": 10,
            "api_calls": 8,
            "form_pass": 10,
            "failures": 0,
            "usage_totals": {
                "prompt_tokens": 960,
                "completion_tokens": 280,
                "total_tokens": 1240
            },
            "usage_reported_for": 8,
            "cases": [ ... ]
        }
    Это пример ФОРМЫ успешного отчёта, а не ожидаемые числа!

    Как считать:
    * api_calls — сумма case_records[*]["api_calls"].
    * form_pass — число записей, где form_pass == True.
    * failures — число записей с ошибкой (обычно total - form_pass).
    * usage_totals — суммы токенов по записям, где есть usage.
      Если какая-то метрика отсутствует, не придумывайте значение.
    * usage_reported_for — число записей с реально полученным usage.
    * cases — исходный список case_records, БЕЗ изменений.
    * mode/task_type/selected_model/total — значения из context.

    Runner сравнит ваш отчёт с фактическими API-вызовами и счётчиками.
    """
    # TODO: самостоятельно соберите словарь и верните его.
    raise NotImplementedError("Реализуйте build_run_report()")
