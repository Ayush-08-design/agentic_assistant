from typing import Any

from src.agent.context.manager import ContextManager
from src.client.llm_client import LLMClient
from src.client.response import StreamEventType, TokenUsage
from src.prompts.system import get_compression_prompt


class ChatCompactor:
    def __init__(self , client : LLMClient):
        self.client = client

    def _format_history_for_compaction(self , messages : dict[str , Any]) -> str:
        
        output = ['Here is the conversation that needs to be continue : \n']
        for msg in messages:
            role = msg.get('role' , '')
            content = msg.get('content' , '')
            
            if role == 'system':
                continue
            
            if role == 'tool':
                tool_id = msg.get('tool_call_id' , 'unknown')
                truncated = content[:2000] if len(content) > 2000 else content
                if len(content) > 2000:
                    truncated += '\n...[Tool output truncated]'
                    
                output.append(f'[Tool Result ({tool_id})]: \n {truncated}')
                
            elif role == 'assistant':

                if content:
                    truncated = content[:2000] if len(content) > 2000 else content
                    if len(content) > 2000:
                        truncated += '\n...[response truncated]'
                    output.append(f"Assistant: \n{truncated}")
                tool_details = []
                
                if msg.get('tool_calls'):
                    for tc in msg['tool_calls']:
                        func = tc.get('function' , {})
                        name = func.get('name' , 'unknown')
                        args = func.get('arguments' , {})
                        
                        if len(args) > 500:
                            args = args[:500]
                        tool_details.append(f" - ({name}) ({args})")
                    output.append('Assistant called tools :\n' + '\n'.join(tool_details))
                    
            elif role == 'user':
                if content:
                    truncated = content[:2000] if len(content) > 2000 else content
                    if len(content) > 2000:
                        truncated += '\n...[message truncated]'
                    output.append(f"User: \n{truncated}")
                    
        return "\n\n --- \n\n".join(output)
    
    
    async def compress(self , ctx_manager : ContextManager) -> tuple[str | None , TokenUsage | None]:
        messages = ctx_manager.get_messages()
        if len(messages) < 3:
            return None , None
        
        compression_messages = {
            {
                'role' : 'system',
                'content' : get_compression_prompt(),
            },
            {
                'role' : 'user',
                'content' : self._format_history_for_compaction(messages)
                    
            },   
        }
        try:
            summary = ''
            usage = None

            async for event in self.client.chat_completion(
                compression_messages,
                stream = False
            ):
                if event.type == StreamEventType.MESSAGE_COMPLETE:
                    usage = event.usage
                    summary += event.text_delta_content
            if not summary or not usage:
                return None , None
            
            return summary , usage
        
        except Exception as e:
            return None , None