import json

from django.test import SimpleTestCase

from expense_analyzer.ai import ExpenseAIUnavailable, _parse_response


class ExpenseAnalyzerGeminiParsingTests(SimpleTestCase):
    def test_parses_structured_gemini_narrative(self):
        raw = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "summary": "This purchase fits your plan.",
                            "reasoning": ["Your weekly savings target remains protected."],
                            "recommendations": ["Keep money aside for transport.", "Record the final amount."],
                            "alternatives": ["Compare a lower-cost option."],
                        })
                    }]
                }
            }]
        })

        result = _parse_response(raw)

        self.assertEqual(result["summary"], "This purchase fits your plan.")
        self.assertEqual(len(result["recommendations"]), 2)
        self.assertEqual(result["alternatives"], ["Compare a lower-cost option."])

    def test_rejects_incomplete_gemini_response(self):
        raw = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": json.dumps({"summary": "", "recommendations": []})}]
                }
            }]
        })

        with self.assertRaises(ExpenseAIUnavailable):
            _parse_response(raw)

    def test_limits_untrusted_long_ai_output(self):
        raw = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "summary": "S" * 2000,
                            "reasoning": ["R" * 900],
                            "recommendations": ["A" * 900],
                            "alternatives": [],
                        })
                    }]
                }
            }]
        })

        result = _parse_response(raw)

        self.assertEqual(len(result["summary"]), 900)
        self.assertEqual(len(result["reasoning"][0]), 420)
        self.assertEqual(len(result["recommendations"][0]), 420)
