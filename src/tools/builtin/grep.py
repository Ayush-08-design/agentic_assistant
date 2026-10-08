import os
import re
from pathlib import Path

from pydantic import BaseModel, Field

from src.tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from src.utils.paths import is_binary_file, resolve_path


class GrepParams(BaseModel):
    pattern: str = Field(..., description="Regular expression pattern to search for")
    path: str = Field(
        ".", description="Directory path to list (default : current directory)"
    )
    case_insensitive: bool = Field(
        False,
        description="Case insensitive search (default : false)",
    )


class GrepTool(Tool):

    name = "grep"
    description = "Search for a regex pattern in file contents , Returns matching lines with files path and line number"
    kind = ToolKind.READ
    schema = GrepParams

    def _find_files(self, search_path: Path) -> list[Path]:
        files = []
        for root, dirs, filenames in os.walk(search_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", "__pycache__", ".git", ".venv", "venv"}
            ]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                file_path = Path(root) / filename
                if not is_binary_file(file_path):
                    files.append(file_path)
                    if len(files) >= 50:
                        return files
        return files

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GrepParams(**invocation.params)
        search_path = resolve_path(invocation.cwd, params.path)

        if not search_path.exists():
            return ToolResult.error_result(f"Path does not exist : {search_path}")
        try:
            flag = re.IGNORECASE if params.case_insensitive else 0
            pattern = re.compile(params.pattern, flag)
        except re.error as e:
            return ToolResult.error_result(f"Invalid Regex Pattern : {e}")

        if search_path.is_dir():
            files = self._find_files(search_path)
        else:
            files = [search_path]

        output_lines = []
        matches = 0
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = content.splitlines()
            file_matches = False

            for idx, line in enumerate(lines , 1):
                if pattern.search(line):
                    matches += 1
                    if not file_matches:
                        rel_path = file_path.relative_to(invocation.cwd)
                        output_lines.append(f"=== {rel_path} ===")
                        file_matches = True
                    else:
                        pass
                    output_lines.append(f"{idx}:{line}")
            if file_matches:
                output_lines.append("")

        if not output_lines:
            return ToolResult.success_result(
                f"No matches found for pattern : {pattern}",
                metadata={
                    "path": str(search_path),
                    "matches": 0,
                    "file_searched": len(files),
                },
            )

        return ToolResult.success_result(
            "\n".join(output_lines),
            metadata={
                "path": str(search_path),
                "matches": matches,
                "file_searched": len(files),
            },
        )
