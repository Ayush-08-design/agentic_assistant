import uuid

from pydantic import BaseModel, Field

from config.config import Config
from src.tools.base import Tool, ToolInvocation, ToolKind, ToolResult

    
class ToDosParams(BaseModel):
    action: str = Field(..., description="Action : 'add' , 'complete' , 'list' , 'clear' ")
    id : str | None = Field(None , description='ToDo id (for complete)')
    content: str | None = Field(
        None, description="TODO content (for add)"
    )

class ToDosTool(Tool):

    name = "todos"
    description = "Manage the task list for the current session . Use this to track progress on multi step task"
    kind = ToolKind.MEMORY
    schema = ToDosParams

    def __init__(self, config : Config):
        super().__init__(config)
        self._todos : dict[str , str] = {}
        
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ToDosParams(**invocation.params)
        
        if params.action.lower() == 'add':
            if not params.content:
                return ToolResult.error_result(
                    '`Content` required for add action'
                )
            todo_id = str(uuid.uuid4()[:8])
            self._todos[todo_id] = params.content
            return ToolResult.success_result(
                f'Added TODO [{todo_id}] : {params.content}'
            )
            
        elif params.action.lower() == 'delete':
            if not params.id:
                return ToolResult.error_result(
                    '`id` required for complete action'
                )
            if params.id not in self._todos:
                return ToolResult.error_result(
                    f'Todo not found : {params.id}'
                )
            content = self._todos.pop(params.id)
            return ToolResult.success_result(
                f'Completed todo [{params.id}] : {content}'
            )
        elif params.action.lower() == 'list':
            if not self._todos:
                return ToolResult.success_result(
                    f'Completed todo [{params.id}] : {content}'
                )
            lines = ['Todos: ']
            for todo_id , content in self._todos.items():
                lines.append(f" [{todo_id}] : {content}")
                
            return ToolResult.success_result(
                "\n".join(lines)            
            )
        elif params.action.lower() == 'clear':
            count = len(self._todos)
            self._todos.clear()
            return ToolResult.success_result(
                f'Cleared {count} todos'
            )
        else:
            return ToolResult.error_result(
                f"Unknown Action : {params.action}"
            )