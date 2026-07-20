import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class DeepSeekConfigurationError(Exception):
    pass


class DeepSeekTimeoutError(Exception):
    pass


class DeepSeekUpstreamError(Exception):
    pass


class DeepSeekResponseError(Exception):
    pass


REQUIRED_ANALYSIS_FIELDS = {
    "summary": str,
    "popular_attractions": list,
    "business_recommendations": list,
    "evidence": list,
    "limitations": list,
}


def analyze_visitor_metrics(question, metrics):
    api_key = settings.DEEPSEEK_API_KEY.strip()
    if not api_key:
        raise DeepSeekConfigurationError("DeepSeek API key is not configured.")

    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是景区运营数据分析助手。只能依据提供的匿名聚合指标回答，"
                    "不得推断个人身份或虚构数据。返回 JSON 对象，必须包含 summary、"
                    "popular_attractions、business_recommendations、evidence、limitations；"
                    "其中 summary 是字符串，其余字段是数组。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"question": question, "metrics": metrics}, ensure_ascii=False
                ),
            },
        ],
    }
    request = Request(
        f"{settings.DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.DEEPSEEK_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (socket.timeout, TimeoutError) as exc:
        raise DeepSeekTimeoutError("DeepSeek request timed out.") from exc
    except HTTPError as exc:
        raise DeepSeekUpstreamError(
            f"DeepSeek returned HTTP status {exc.code}."
        ) from exc
    except URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise DeepSeekTimeoutError("DeepSeek request timed out.") from exc
        raise DeepSeekUpstreamError("DeepSeek request failed.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeepSeekResponseError("DeepSeek returned invalid JSON.") from exc

    try:
        content = response_payload["choices"][0]["message"]["content"]
        analysis = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise DeepSeekResponseError("DeepSeek returned an invalid response.") from exc

    if not isinstance(analysis, dict) or any(
        not isinstance(analysis.get(field), expected_type)
        for field, expected_type in REQUIRED_ANALYSIS_FIELDS.items()
    ):
        raise DeepSeekResponseError("DeepSeek response is missing required fields.")
    return analysis
