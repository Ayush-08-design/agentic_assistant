from pydantic import BaseModel, Field

from src.tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from src.utils.paths import resolve_path


class GlobParams(BaseModel):
    pattern: str = Field(..., description="Glob pattern to match file name")
    path: str = Field(
        ".", description="Directory to seach in (default : current directory)"
    )

class GlobTool(Tool):

    name = "glob"
    description = "Find files matching a glob pattern. Supports ** for recursive matching"
    kind = ToolKind.READ
    schema = GlobParams


    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GlobParams(**invocation.params)
        search_path = resolve_path(invocation.cwd, params.path)

        if not search_path.exists() or not search_path.is_dir():
            return ToolResult.error_result(f"Directory does not exist : {search_path}")
        
        try:
            matches = list(search_path.glob(params.pattern))
            matches = [p for p in matches if p.is_file()]
        except Exception as e:
            return ToolResult.error_result(f"Error Searching : {e}")

        output_lines = []
        
        for file_path in matches[:500]:
            try:
                rel_path = file_path.relative_to(invocation.cwd)
            except Exception:
                rel_path = file_path
                
            output_lines.append(str(rel_path))

        if len(matches) > 500:
            output_lines.append('...(limited to 500 results)')
        return ToolResult.success_result(
            "\n".join(output_lines),
            metadata={
                "path": str(search_path),
                'matches' : len(matches),
            },
        )