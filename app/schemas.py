"""Request and response schemas for the posting API."""

import re
from typing import List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator

HOSTNAME_REGEX = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    r'|^localhost$'
    r'|^(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$'
)

URL_PATTERN = re.compile(
    r'(?:[a-zA-Z][a-zA-Z0-9+.-]*://\S*|www\.\S+|mailto:\S+|javascript:\S+)'
)


class PostingRequest(BaseModel):
    message: str = Field(
        ...,
        description="The message text to publish across platforms (max 200 characters, exactly one CTA URL)"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")

        if len(v) > 200:
            raise ValueError(f"Message length exceeds 200 characters (length: {len(v)})")

        candidates = URL_PATTERN.findall(v)
        if len(candidates) == 0:
            raise ValueError("Message must contain exactly one CTA URL (found 0)")
        if len(candidates) > 1:
            raise ValueError(f"Message must contain exactly one CTA URL (found {len(candidates)})")

        raw_url = candidates[0].rstrip(".,;:!?")
        if raw_url.endswith(")") and "(" not in raw_url:
            raw_url = raw_url[:-1]

        try:
            parsed = urlparse(raw_url)
        except Exception as e:
            raise ValueError(f"Malformed URL: {e}")

        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError(
                f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS schemes are allowed"
            )

        if not parsed.netloc:
            raise ValueError("Malformed URL: missing hostname or network location")

        try:
            hostname = parsed.hostname
        except ValueError:
            raise ValueError("Malformed URL: invalid host or port")

        if not hostname:
            raise ValueError("Malformed URL: missing valid hostname")

        if not HOSTNAME_REGEX.match(hostname):
            raise ValueError(f"Invalid URL hostname: '{hostname}'")

        return v


class PlatformPostResult(BaseModel):
    platform: str = Field(..., description="Name of the platform")
    status: str = Field(..., description="Status of the post: 'success' or 'failed'")
    posted_url: Optional[str] = Field(
        default=None,
        description="Public URL to the published post"
    )
    public_access: bool = Field(
        default=False,
        description="Whether the published post is publicly accessible"
    )
    date: Optional[str] = Field(
        default=None,
        description="Publication date (YYYY-MM-DD)"
    )
    time: Optional[str] = Field(
        default=None,
        description="Publication time (HH:MM:SS)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error details if publishing failed"
    )


class PostingResponse(BaseModel):
    """Standardized response from the posting endpoint.

    The 'success' field indicates overall outcome:
    - True: Complete or partial success (at least one platform succeeded).
    - False: Total failure (all platforms failed).
    """

    success: bool = Field(
        ...,
        description="True if at least one platform succeeded; False if all failed"
    )
    results: List[PlatformPostResult] = Field(
        ...,
        description="List of publishing results from each platform"
    )
