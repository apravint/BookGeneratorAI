import unittest
from unittest.mock import patch
import io
import urllib.error
from email.message import Message
from generator.llm_client import LlmClient, QuotaExceededError


def http_error(code, body, retry_after=None):
    headers = Message()
    if retry_after:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://x", code, "err", headers, io.BytesIO(body.encode()))


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


class TestRetries(unittest.TestCase):
    def setUp(self):
        self.client = LlmClient(provider="openai", api_key="x", model="m")

    def post(self, *errors):
        with patch("urllib.request.urlopen", side_effect=list(errors)) as urlopen, patch("time.sleep") as sleep:
            try:
                self.client._post_json("https://x", {}, {})
            finally:
                self.calls, self.sleeps = urlopen.call_count, [c.args[0] for c in sleep.call_args_list]

    def test_exhausted_quota_fails_without_retrying(self):
        with self.assertRaises(QuotaExceededError):
            self.post(http_error(429, '{"error": {"code": "insufficient_quota"}}'))
        self.assertEqual(self.calls, 1)

    def test_gemini_daily_limit_fails_without_retrying(self):
        with self.assertRaises(QuotaExceededError):
            self.post(http_error(429, '{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}'))
        self.assertEqual(self.calls, 1)

    def test_long_requested_wait_fails_fast(self):
        with self.assertRaises(QuotaExceededError):
            self.post(http_error(429, "slow down", retry_after="3600"))
        self.assertEqual(self.calls, 1)

    def test_brief_rate_limit_waits_as_asked_then_retries(self):
        with self.assertRaises(RuntimeError):
            self.post(http_error(429, '{"retryDelay": "17s"}'), http_error(400, "bad"))
        self.assertEqual(self.calls, 2)
        self.assertEqual(self.sleeps, [18])


if __name__ == "__main__":
    unittest.main()
