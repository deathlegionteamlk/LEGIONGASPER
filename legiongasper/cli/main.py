import asyncio
import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.insert(0, '/app/legiongasper_framework_0813')

from legiongasper.core.factory import AgentFactory
from legiongasper.core.orchestrator import Orchestrator
from legiongasper.gateway.server import GatewayServer

console = Console()

@click.group()
@click.version_option(version="1.0.0", prog_name="legiongasper")
def cli():
    
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8081, help='Port to bind to')
@click.option('--dashboard-port', default=8080, help='Dashboard port')
def serve(host: str, port: int, dashboard_port: int):
    
    console.print(Panel.fit(
        "[bold cyan]⚡ LEGIONGASPER Gateway Server[/bold cyan]\n"
        "[dim]OpenClaw Factory Edition - DEATH LEGION Team[/dim]",
        border_style="cyan"
    ))
    
    console.print(f"\n[green]Starting server on {host}:{port}...[/green]")
    console.print(f"[dim]Dashboard available on port {dashboard_port}[/dim]\n")
    
    server = GatewayServer(host=host, port=port)
    server.run_sync()

@cli.group()
def agent():
    
    pass

@agent.command(name='list')
def list_agents():
    
    async def _list():
        factory = AgentFactory()
        agents = await factory.list_agents()
        
        table = Table(title="Active Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Template", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Created", style="dim")
        
        for agent in agents:
            status_color = {
                'idle': 'green',
                'processing': 'yellow',
                'error': 'red'
            }.get(agent.get('status'), 'white')
            
            table.add_row(
                agent.get('agent_id', 'N/A'),
                agent.get('template_id', 'N/A'),
                f"[{status_color}]{agent.get('status', 'unknown')}[/{status_color}]",
                agent.get('created', 'N/A')
            )
        
        console.print(table)
    
    asyncio.run(_list())

@agent.command(name='spawn')
@click.option('--template', '-t', required=True, help='Template ID')
@click.option('--id', 'agent_id', help='Custom agent ID')
@click.option('--config', '-c', help='Config JSON')
def spawn_agent(template: str, agent_id: Optional[str], config: Optional[str]):
    
    async def _spawn():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Spawning agent...", total=None)
            
            factory = AgentFactory()
            cfg = json.loads(config) if config else {}
            
            agent = await factory.spawn(
                template_id=template,
                agent_id=agent_id,
                config=cfg
            )
            
            progress.update(task, completed=True)
            console.print(f"[green]✓ Agent spawned:[/green] {agent.agent_id}")
    
    asyncio.run(_spawn())

@agent.command(name='terminate')
@click.argument('agent_id')
def terminate_agent(agent_id: str):
    
    async def _terminate():
        factory = AgentFactory()
        await factory.recycle(agent_id)
        console.print(f"[yellow]Agent {agent_id} terminated[/yellow]")
    
    asyncio.run(_terminate())

@cli.group()
def task():
    
    pass

@task.command(name='submit')
@click.argument('description')
@click.option('--agent', '-a', help='Assign to specific agent')
@click.option('--priority', '-p', default='normal', 
              type=click.Choice(['low', 'normal', 'high']))
def submit_task(description: str, agent: Optional[str], priority: str):
    
    async def _submit():
        orchestrator = Orchestrator()
        await orchestrator.start()
        
        task_id = await orchestrator.submit(
            description=description,
            agent_id=agent,
            priority=priority
        )
        
        console.print(f"[green]✓ Task submitted:[/green] {task_id}")
    
    asyncio.run(_submit())

@task.command(name='list')
def list_tasks():
    
    async def _list():
        orchestrator = Orchestrator()
        tasks = await orchestrator.list_tasks()
        
        table = Table(title="Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Priority", style="green")
        
        for t in tasks:
            table.add_row(
                t.task_id[:8] + "...",
                t.description[:40],
                t.status.value,
                t.priority.value
            )
        
        console.print(table)
    
    asyncio.run(_list())

@task.command(name='status')
@click.argument('task_id')
def task_status(task_id: str):
    
    async def _status():
        orchestrator = Orchestrator()
        task = await orchestrator.get_task(task_id)
        
        if task:
            console.print(Panel(
                f"[bold]Task:[/bold] {task.task_id}\n"
                f"[bold]Status:[/bold] {task.status.value}\n"
                f"[bold]Priority:[/bold] {task.priority.value}\n"
                f"[bold]Description:[/bold] {task.description}",
                title="Task Status"
            ))
        else:
            console.print("[red]Task not found[/red]")
    
    asyncio.run(_status())

@cli.group()
def squad():
    
    pass

@squad.command(name='create')
@click.argument('task_description')
@click.option('--count', '-n', default=3, help='Number of agents')
@click.option('--templates', '-t', help='Comma-separated template IDs')
def create_squad(task_description: str, count: int, templates: Optional[str]):
    
    async def _create():
        from legiongasper.core.squad import Squad
        from legiongasper.core.factory import AgentFactory
        
        template_list = templates.split(',') if templates else ['research', 'code', 'review']
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating squad...", total=None)
            
            factory = AgentFactory()
            squad = Squad(
                squad_id=f"squad_{task_description[:10]}",
                max_concurrent=count
            )
            
            for i, template in enumerate(template_list[:count]):
                agent = await factory.spawn(
                    template_id=template,
                    agent_id=f"{squad.squad_id}_agent_{i}"
                )
                squad.add_agent(agent)
            
            progress.update(task, completed=True)
            
            console.print(f"[green]✓ Squad created with {len(squad.agents)} agents[/green]")
    
    asyncio.run(_create())

@cli.command()
def status():
    
    async def _status():
        factory = AgentFactory()
        orchestrator = Orchestrator()
        
        agents = await factory.list_agents()
        tasks = await orchestrator.get_stats()
        
        console.print(Panel.fit(
            f"[bold cyan]LEGIONGASPER System Status[/bold cyan]\n\n"
            f"[green]Agents:[/green] {len(agents)} active\n"
            f"[yellow]Tasks:[/yellow] {tasks.total} total "
            f"({tasks.completed} completed, {tasks.failed} failed)\n"
            f"[blue]Pending:[/blue] {tasks.pending} | [magenta]Running:[/magenta] {tasks.running}",
            border_style="cyan"
        ))
    
    asyncio.run(_status())

@cli.command()
def init():
    
    console.print(Panel.fit(
        "[bold green]⚡ LEGIONGASPER Initialization[/bold green]\n\n"
        "Creating default configuration files...",
        border_style="green"
    ))
    
    import os
    
    dirs = [
        '/app/legiongasper_framework_0813/configs',
        '/app/legiongasper_framework_0813/data',
        '/app/legiongasper_framework_0813/logs'
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        console.print(f"[dim]Created:[/dim] {d}")
    
    config_content = 
    
    config_path = '/app/legiongasper_framework_0813/configs/default.yaml'
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    console.print(f"\n[green]✓ Configuration created at {config_path}[/green]")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("  1. Set your API keys in environment variables")
    console.print("  2. Run 'legiongasper serve' to start the server")
    console.print("  3. Visit http://localhost:8080 for the dashboard")

if __name__ == '__main__':
    cli()