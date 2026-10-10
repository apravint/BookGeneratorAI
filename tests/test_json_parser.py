import unittest
from generator.json_parser import clean_json_string, parse_llm_json
from schemas.models import WorldRule


class TestJsonParser(unittest.TestCase):
    def test_clean_json_string_markdown_fences(self):
        raw = """Here is the json output:
```json
{
  "key": "value",
  "num": 42
}
```
Hope this helps!"""
        cleaned = clean_json_string(raw)
        self.assertIn('"key": "value"', cleaned)
        self.assertNotIn("Here is the json", cleaned)

    def test_clean_json_string_trailing_commas(self):
        raw = """{
  "items": [
    "apple",
    "banana",
  ],
  "name": "fruits",
}"""
        cleaned = clean_json_string(raw)
        data = parse_llm_json(cleaned)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "fruits")
        self.assertEqual(len(data["items"]), 2)

    def test_clean_json_string_deepseek_think_tags(self):
        raw = """<think>
We need to generate a world rule. Let's think about constraints.
</think>
```json
{
  "category": "Ancient",
  "name": "Blood Oath",
  "description": "Never break an oath.",
  "consequence": "Curse of silence"
}
```"""
        rule = parse_llm_json(raw, model_class=WorldRule)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.rule_name, "Blood Oath")
        self.assertEqual(rule.narrative_consequence, "Curse of silence")

    def test_parse_llm_json_invalid(self):
        self.assertIsNone(parse_llm_json("This is definitely not json"))
        self.assertIsNone(parse_llm_json(""))


if __name__ == "__main__":
    unittest.main()
