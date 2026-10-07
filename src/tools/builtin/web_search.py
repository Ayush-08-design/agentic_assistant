from ddgs import DDGS
from pydantic import BaseModel, Field

from src.tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class WebSearchParams(BaseModel):
    query: str = Field(..., description="Search Query ...")
    max_results: int = Field(
        10, ge = 1 , le = 20 , description="Maximum results to return (deafults : 10)"
    )

class WebSearchTool(Tool):

    name = "web_search"
    description = "Search the web for information. Returns  seach results with titles, URLs and snippets"
    kind = ToolKind.NETWORK
    schema = WebSearchParams


    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WebSearchParams(**invocation.params)
        
        try:
            results = DDGS().text(
                params.query, 
                region = 'us-en',
                safesearch = 'off',
                timelimit = 'y',
                page=1,
                backend = 'auto'
            )
        except Exception as e:
            return ToolResult.error_result(
                f'search failed {e}'
            )
            
        if not results:
            return ToolResult.error_result(
                f'No results found for {params.query}',
                metadata={
                    'results' : len(results),
                },
            )
        output_lines = [f'Search results for : {params.query}']
        for idx , result in enumerate(results , 1):
            output_lines.append(f"{idx}. title : {result['title']}")
            output_lines.append(f"URL : {result['href']}")
            if result.get('body'):
                output_lines.append(f"Snippet : {result['body']}")
            output_lines.append("")
            
        return ToolResult.success_result(
            "\n".join(output_lines),
            metadata={
                'results' : len(results),
            },
        )