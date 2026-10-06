import json

# from enum import Enum
from pydantic import BaseModel, Field

from config.loader import get_data_dir
from src.tools.base import Tool, ToolInvocation, ToolKind, ToolResult

# class Action(str , Enum):
#     SET = 'set'
#     GET = 'get'
#     DELETE = 'delete'
#     LIST = 'list'
#     CLEAR = 'clear'
    
class MemoryParams(BaseModel):
    action: str = Field(..., description="Action : 'set' , 'get' , 'delete' ,  'list' , 'clear' ")
    key : str | None = Field(None , description='Memory key (required for set , get , delete)')
    value : str | None = Field(
        None, description="Value to store (required for `set` opeartion)"
    )

class MemoryTool(Tool):

    name = "memory"
    description = "Store and retrieve persistent memory. Use this to remember user preferences. Important context or Notes"
    kind = ToolKind.MEMORY
    schema = MemoryParams
        
    def _load_memory(self) -> dict:
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True , exist_ok=True)
        path = data_dir / 'user_memory.json'
        
        if not path.exists():
            return {'entries' : {}}
        try:
            content = path.read_text(encoding='utf-8')
            return json.loads(content)
        
        except json.JSONDecodeError:
            return {'entries' : {}}
        
    def _save_memory(self , memory : dict) -> None:
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True , exist_ok=True)
        path = data_dir / 'user_memory.json'
        
        path.write_text(json.dumps(memory , indent=2 , ensure_ascii=False))
                
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = MemoryParams(**invocation.params)
        
        if params.action.lower() == 'set':
            if not params.key or not params.value:
                return ToolResult.error_result(
                    '`Key` and `Value` are required for set action'
                )
            memory = self._load_memory()
            memory['entries'][params.key] = params.value
            self._save_memory(memory)
            
            return ToolResult.success_result(
                f'Set memory [{params.key}]'
            )
            
        elif params.action.lower() == 'get':
            if not params.key:
                return ToolResult.error_result(
                    '`Key` is required for `get` action'
                )
            memory = self._load_memory()
            
            if params.key not in memory['entries']:
                return ToolResult.success_result(
                    f'Memory not found [{params.key}]',
                    metadata = {
                        'found' : False,
                    }
                )
            return ToolResult.success_result(
                f'Memory found [{params.key}] : {memory['entries'][params.key]}',
                metadata = {
                    'found' : True,
                }
            )
                
        elif params.action.lower() == 'delete':
            if not params.key:
                return ToolResult.error_result(
                    '`Key` is required for `delete` action'
                )
            memory = self._load_memory()
            if params.key not in memory['entries']:
                return ToolResult.success_result(
                    f'Memory not found [{params.key}]'
                )
            del memory['entries'][params.key]
            self._save_memory(memory)
            
            return ToolResult.success_result(
                f'Memory deleted successfully : deleted memory [{params.key}]'
            )
            
        elif params.action.lower() == 'list':
            memory = self._load_memory()
            entries = memory.get('entries' , {})
            if not entries:
                return ToolResult.success_result(
                    'No memories stored',
                    metadata = {
                        'found' : False,
                    }
                )
            lines = ['Stored memories: ']
            for key , value in sorted(entries.items()):
                lines.append(f" [{key}] : {value}")
                
            return ToolResult.success_result(
                "\n".join(lines),
                metadata = {
                    'found' : True,
                    }    
            )
            
        elif params.action.lower() == 'clear':
            memory = self._load_memory()
            entries = memory.get('entries' , {})
            count = len(entries)
            
            memory['entries'] = {}
            
            self._save_memory(memory)
            return ToolResult.success_result(
                f'Cleared {count} memory entries'
            )
            
        else:
            return ToolResult.error_result(
                f"Unknown Action : {params.action}"
            )