import sys

from src.agent.agent import Agent
from src.agent.events import AgentEventType
import asyncio
import click
from typing import Any

from ui.tui import TUI , get_console

console = get_console()

class CLI:
    def __init__(self):
        self.agent : Agent | None = None
        self.tui = TUI(console)
        
        self.assistant_streaming = False
        
    async def run_single(self , message : str) -> str | None:
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)
            
    async def _process_message(self , message : str) -> str | None:
        if not self.agent:
            return None

        final_response : str | None = None
        
        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get('content' , '')
                
                if not self.assistant_streaming:
                    self.tui.begin_assistant()
                    self.assistant_streaming = True
                self.tui.stream_assistant_delta(content)
                
            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get('content')
                if self.assistant_streaming:
                    
                    self.tui.end_assistant()
                    self.assistant_streaming = False

            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get('error' , 'Unknown Error')
                console.print(f'\n[error]Error : {error} [/error]')
                    
        return final_response
    
        
@click.command()
@click.argument("prompt" , required = False)
def main(
    prompt : str | None = None
):
    cli = CLI()

    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)
main()