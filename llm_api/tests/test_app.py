import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from src import app


ROOT = Path(__file__).resolve().parents[1]


def response_with(content, usage=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=usage,
    )


class ValidationTests(unittest.TestCase):
    def test_assigned_cases_validation(self):
        assignment = json.loads((ROOT / "assignment.json").read_text(encoding="utf-8"))
        for case_id in assignment["case_ids"]:
            with self.subTest(case_id=case_id):
                raw = (ROOT / "cases" / f"{case_id}.json").read_text(encoding="utf-8")
                data, error = app.validate_input(raw)
                if case_id in {"07-13", "07-14"}:
                    self.assertIsNone(data)
                    self.assertEqual(error, "invalid_type")
                else:
                    self.assertIsNone(error)
                    self.assertEqual(data["task_type"], "incident_analysis")

    def test_malformed_and_non_object_json(self):
        self.assertEqual(app.validate_input("{"), (None, "invalid_json"))
        self.assertEqual(app.validate_input("[]"), (None, "invalid_type"))
        self.assertEqual(app.validate_input(None), (None, "invalid_json"))

    def test_required_fields_and_types(self):
        raw = (ROOT / "cases" / "07-03.json").read_text(encoding="utf-8")
        original = json.loads(raw)

        mutations = []
        for field in ("case_id", "task_type", "payload"):
            value = copy.deepcopy(original)
            del value[field]
            mutations.append((value, "missing_required_field"))

        for field in ("description", "severity_rules"):
            value = copy.deepcopy(original)
            del value["payload"][field]
            mutations.append((value, "missing_required_field"))

        for level in ("low", "medium", "high"):
            value = copy.deepcopy(original)
            del value["payload"]["severity_rules"][level]
            mutations.append((value, "missing_required_field"))

        value = copy.deepcopy(original)
        value["task_type"] = "ticket_triage"
        mutations.append((value, "unsupported_task"))
        value = copy.deepcopy(original)
        value["payload"]["description"] = "   "
        mutations.append((value, "invalid_value"))
        value = copy.deepcopy(original)
        value["payload"]["severity_rules"]["low"] = 1
        mutations.append((value, "invalid_type"))
        value = copy.deepcopy(original)
        value["rules"]["unknown_as_null"] = "yes"
        mutations.append((value, "invalid_type"))

        for value, expected_error in mutations:
            with self.subTest(expected_error=expected_error, value=value):
                data, error = app.validate_input(json.dumps(value, ensure_ascii=False))
                self.assertIsNone(data)
                self.assertEqual(error, expected_error)


class PromptTests(unittest.TestCase):
    def test_prompt_contains_task_data_and_injection_defence(self):
        raw = (ROOT / "cases" / "07-15.json").read_text(encoding="utf-8")
        data, error = app.validate_input(raw)
        self.assertIsNone(error)
        prompt = app.build_prompt(data)
        self.assertIsInstance(prompt, str)
        self.assertTrue(prompt.strip())
        self.assertIn("HACKED", prompt)
        self.assertIn("severity_rules", prompt)
        self.assertIn("недоверенные данные", prompt)
        self.assertIn('"severity"', prompt)
        self.assertIn("JSON null", prompt)


class ParseResponseTests(unittest.TestCase):
    def test_valid_values_and_fenced_json(self):
        for value in ("low", "medium", "high", None):
            with self.subTest(value=value):
                content = json.dumps({"severity": value})
                self.assertEqual(app.parse_response(response_with(content)), {"severity": value})
        self.assertEqual(
            app.parse_response(response_with('```json\n{"severity":"high"}\n```')),
            {"severity": "high"},
        )

    def test_invalid_responses(self):
        invalid = (
            "HACKED",
            "OK",
            "null",
            '["high"]',
            '{"severity":"critical"}',
            '{"severity":"null"}',
            '{"result":{"severity":"high"}}',
            '{"severity":"high","comment":"extra"}',
            "",
        )
        for content in invalid:
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    app.parse_response(response_with(content))

    def test_missing_message_content(self):
        with self.assertRaises(ValueError):
            app.parse_response(SimpleNamespace(choices=[]))


class UsageTests(unittest.TestCase):
    def test_actual_usage(self):
        usage = SimpleNamespace(prompt_tokens=120, completion_tokens=35, total_tokens=155)
        self.assertEqual(
            app.extract_usage(response_with("{}", usage)),
            {"prompt_tokens": 120, "completion_tokens": 35, "total_tokens": 155},
        )

    def test_total_fallback_and_missing_usage(self):
        usage = SimpleNamespace(prompt_tokens=120, completion_tokens=35, total_tokens=None)
        self.assertEqual(app.extract_usage(response_with("{}", usage))["total_tokens"], 155)
        self.assertEqual(
            app.extract_usage(response_with("{}")),
            {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
        )

    def test_bool_and_negative_values_are_not_token_counts(self):
        usage = SimpleNamespace(prompt_tokens=True, completion_tokens=-1, total_tokens=2.5)
        self.assertEqual(
            app.extract_usage(response_with("{}", usage)),
            {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
        )


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "mode": "live",
            "task_type": "incident_analysis",
            "selected_model": "GigaChat-3-Lightning",
            "total": 3,
        }

    def test_counters_and_totals(self):
        records = [
            {
                "case_id": "07-03",
                "api_calls": 1,
                "form_pass": True,
                "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110},
            },
            {
                "case_id": "07-09",
                "api_calls": 1,
                "form_pass": True,
                "usage": {"prompt_tokens": 120, "completion_tokens": 20, "total_tokens": 140},
            },
            {"case_id": "07-13", "api_calls": 0, "form_pass": True},
        ]
        original = copy.deepcopy(records)
        report = app.build_run_report(self.context, records)
        self.assertEqual(report["api_calls"], 2)
        self.assertEqual(report["form_pass"], 3)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report["usage_reported_for"], 2)
        self.assertEqual(
            report["usage_totals"],
            {"prompt_tokens": 220, "completion_tokens": 30, "total_tokens": 250},
        )
        self.assertEqual(report["cases"], original)
        self.assertIs(report["cases"], records)

    def test_missing_metric_makes_only_that_total_unknown(self):
        records = [
            {
                "case_id": "07-03",
                "api_calls": 1,
                "form_pass": True,
                "usage": {"prompt_tokens": 100, "completion_tokens": None, "total_tokens": None},
            }
        ]
        report = app.build_run_report(self.context, records)
        self.assertEqual(
            report["usage_totals"],
            {"prompt_tokens": 100, "completion_tokens": None, "total_tokens": None},
        )

    def test_no_usage_is_not_zero_consumption(self):
        records = [{"case_id": "07-13", "api_calls": 0, "form_pass": True}]
        report = app.build_run_report(self.context, records)
        self.assertEqual(report["usage_reported_for"], 0)
        self.assertEqual(
            report["usage_totals"],
            {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None},
        )


if __name__ == "__main__":
    unittest.main()
