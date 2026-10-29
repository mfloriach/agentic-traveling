from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def is_retryable(exc: BaseException) -> bool:
    if isinstance(
        exc,
        (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
        ),
    ):
        return True

    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES

    return False


# def log_retry(retry_state) -> None:
#     exc = retry_state.outcome.exception()

#     logger.warning(
#         "http.retry",
#         extra={
#             "attempt": retry_state.attempt_number,
#             "exception": type(exc).__name__ if exc else None,
#             "next_wait_seconds": retry_state.next_action.sleep
#             if retry_state.next_action
#             else None,
#         },
#     )


class APIClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, connect=3.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )

    async def close(self) -> None:
        await self.client.aclose()

    @retry(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(
            multiplier=0.5,
            max=8,
        ),
        # before_sleep=log_retry,
        reraise=True,
    )
    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        response = await self.client.get(path, **kwargs)
        response.raise_for_status()
        return response.json()
