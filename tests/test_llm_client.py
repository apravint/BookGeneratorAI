import unittest
from unittest.mock import patch
from generator.llm_client import LlmClient


class TestCleanOutput(unittest.TestCase):
    def setUp(self):
        self.client = LlmClient(provider="openai", api_key="x", model="m")

    def test_prose_is_not_mangled(self):
        prose = 'Sure, he had seen worse.\nDetail: the knife was gone. Interaction: none, she said.'
        self.assertEqual(self.client._clean_llm_output(prose), prose)

    def test_meta_preamble_and_thinking_removed(self):
        self.assertEqual(self.client._clean_llm_output("<think>hm</think>Here is the scene:\nRain fell."), "Rain fell.")

    def test_anthropic_never_defaults_to_an_openai_model(self):
        self.assertTrue(LlmClient(provider="anthropic", api_key="x").model.startswith("claude"))

    def test_empty_response_raises(self):
        with patch.object(self.client, "_post_json", return_value={"choices": [{"message": {"content": ""}}]}):
            with self.assertRaises(RuntimeError):
                self.client.generate_text("p")

    def test_truncated_reply_retries_with_more_room(self):
        cut = {"choices": [{"message": {"content": "Half a sen"}, "finish_reason": "length"}]}
        whole = {"choices": [{"message": {"content": "A whole sentence."}, "finish_reason": "stop"}]}
        with patch.object(self.client, "_post_json", side_effect=[cut, whole]) as post:
            self.assertEqual(self.client.generate_text("p", max_tokens=100), "A whole sentence.")
        self.assertEqual(post.call_args.args[1]["max_tokens"], 200)


if __name__ == "__main__":
    unittest.main()
