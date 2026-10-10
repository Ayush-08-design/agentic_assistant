from urllib.parse import urlparse

import httpx2
from pydantic import BaseModel, Field

from src.tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class WebFetchParams(BaseModel):
    url: str = Field(..., description="URL to fetch (must be http:// or https://)")
    timeout : int = Field(
        30,
        ge = 5,
        le = 120,
        description='Request timeout in seconds (default to : 120)',
        )
    max_results: int = Field(
        10, ge = 1 , le = 20 , description="Maximum results to return (deafults : 10)"
    )

class WebFetchTool(Tool):

    name = "web_fetch"
    description = "Fetch content from a URL. Returns the response body as text"
    kind = ToolKind.NETWORK
    schema = WebFetchParams


    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WebFetchParams(**invocation.params)
        parsed = urlparse(params.url)
        if not parsed.scheme or parsed.scheme not in ('http' , 'https'):
            return ToolResult.error_result(
                'URL must be http:// or https://',
            )
        try:
            async with httpx2.AsyncClient(
                timeout=httpx2.Timeout(params.timeout),
                follow_redirects=True,
                
            ) as client:
                response = await client.get(params.url)
                response.raise_for_status()
                text = response.text # extract text
        except httpx2.HTTPStatusError as e:
            return ToolResult.error_result(
                f'HTTP : {e.response.status_code} : {e.response.reason_phrase}'
            )
        except Exception as e:
            return ToolResult.error_result(
                f'Request failed {e}'
            )
            
        if len(text) > 100 * 1024:
            text = text[:100*1024] + "\n...[content truncated]"
            
        return ToolResult.success_result(
            text,
            metadata={
                'status_code' : response.status_code,
                'content_length' : len(response.content),
            },
        )