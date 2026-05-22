import os
import sys
import json
import uuid
import subprocess
import shutil
from pathlib import Path
import webbrowser
import openai
import requests  # Handle transactional API routing tasks
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table
from huggingface_hub import HfApi

console = Console()
hf_api = HfApi()

CONFIG_DIR = Path.home() / ".config" / "hf-bot"
CONFIG_FILE = CONFIG_DIR / "keys.json"
UUID_FILE = CONFIG_DIR / "device_id.json"

PROXY_SERVER_URL = "https://hf-bot-proxy.vercel.app/v1" 
PROJECT_SHARE_LINK = "https://pypi.org/project/hf-bot/"  
GITHUB_REPO_LINK = "https://github.com/kuyesu/hf-bot"

# ==========================================
# 🔐 CONFIGURATION MANAGEMENT LAYER
# ==========================================
def get_device_uuid() -> str:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if UUID_FILE.exists():
        with open(UUID_FILE, "r") as f:
            return json.load(f).get("uuid", str(uuid.uuid4()))
    uid = str(uuid.uuid4())
    with open(UUID_FILE, "w") as f:
        json.dump({"uuid": uid}, f)
    return uid

def load_resolved_provider_context() -> tuple[openai.OpenAI, str, bool]:
    env_xai_key = os.getenv("XAI_API_KEY")
    local_url = os.getenv("LOCAL_MODEL_URL")
    
    if env_xai_key:
        return openai.OpenAI(base_url="https://api.x.ai/v1", api_key=env_xai_key), os.getenv("XAI_MODEL_NAME", "grok-4.3"), False
    if local_url:
        return openai.OpenAI(base_url=local_url, api_key="dummy-key"), os.getenv("LOCAL_MODEL_NAME", "llama3"), False

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved_key = json.load(f).get("XAI_API_KEY")
                if saved_key:
                    return openai.OpenAI(base_url="https://api.x.ai/v1", api_key=saved_key), os.getenv("XAI_MODEL_NAME", "grok-4.3"), False
        except Exception:
            pass

    device_id = get_device_uuid()
    proxy_client = openai.OpenAI(
        base_url=PROXY_SERVER_URL,
        api_key="proxy-unneeded",
        default_headers={"X-Client-UUID": device_id}
    )
    return proxy_client, "grok-4.3", True

# ==========================================
# 🔐 CONFIGURATION MENUS WORKFLOWS
# ==========================================
def run_interactive_config_setup():
    console.print("\n🔐 [bold purple]hf-bot Workspace Token Configuration (Option B)[/]")
    console.print("Set your own keys to eliminate shared resource constraints.\n")
    
    provider_table = Table.grid(padding=(0, 2))
    provider_table.add_column("Index ID", style="bold cyan", width=10)
    provider_table.add_column("API Provider", style="bold white")
    provider_table.add_row("1", "xAI (Grok)")
    provider_table.add_row("2", "Anthropic (Claude)")
    provider_table.add_row("3", "OpenAI (GPT / Codex)")
    
    console.print(Panel(provider_table, title="Select Target API Provider Node", border_style="purple", padding=(1, 2)))
    choice = Prompt.ask("[bold white]Choose a provider number (1-3)[/]", choices=["1", "2", "3"], default="1")
    
    if choice == "1":
        provider_label = "xAI (Grok)"; json_key_name = "XAI_API_KEY"
    elif choice == "2":
        provider_label = "Anthropic (Claude)"; json_key_name = "ANTHROPIC_API_KEY"
    else:
        provider_label = "OpenAI (GPT / Codex)"; json_key_name = "OPENAI_CODEX_KEY"
        
    console.print(f"\n⚙️ Selected layout: [bold green]{provider_label}[/bold green]")
    user_key = Prompt.ask(f"[bold white]Enter your personal {provider_label} API Key[/]", password=True).strip()
    
    if not user_key:
        console.print("[red]Operation canceled. Key entry cannot be blank.[/]")
        return
        
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        existing_config = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f: existing_config = json.load(f)
            except Exception: pass
                
        existing_config[json_key_name] = user_key
        with open(CONFIG_FILE, "w") as f: json.dump(existing_config, f, indent=4)
        console.print(f"\n[bold green]✓ Success![/] Custom credential token registered cleanly.\n")
    except Exception as e:
        console.print(f"[bold red]Failed to write configuration maps safely:[/] {e}")

def run_interactive_config_clear():
    console.print("\n🗑️  [bold red]hf-bot Workspace Token Reset[/bold red]")
    if not CONFIG_FILE.exists():
        console.print("[dim]No custom API keys found. You are already using the shared proxy (Option A).[/dim]\n")
        return
    confirm = Prompt.ask("[bold white]Are you sure you want to delete your saved keys? (y/N)[/]", choices=["y", "n"], default="n").lower()
    if confirm != "y": return
    try:
        CONFIG_FILE.unlink()
        console.print("[bold green]✓ Success![/bold green] Custom API tokens deleted cleanly.\n")
    except Exception as e:
        console.print(f"[bold red]Failed to clear token properties cleanly:[/] {e}")

# ==========================================
# 🚀 VIRAL UTILITY SHARE HUB WORKFLOW
# ==========================================
def run_sharing_engine_pipeline() -> bool:
    """Displays the copyable link, prompts for email, and asks for an optional sender name."""
    console.print("\n🤝 [bold cyan]Share hf-bot and try it out together.[/bold cyan]")
    console.print("Spread the news about [bold yellow]hf-bot[/bold yellow] with colleagues and software engineers.\n")
    
    # 1. Display the link in a high-visibility container layout instantly
    console.print(Panel(
        f"🔗 [bold white]Project Link:[/bold white] [underline cyan]{PROJECT_SHARE_LINK}[/underline cyan]\n"
        "[dim]↳ Copy this link manually, or enter an email below to send an invite automatically.[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    
    # 2. Capture the recipient email
    email_target = Prompt.ask("[bold white]Enter colleague's email address[/]").strip()
    
    if not email_target:
        console.print("[yellow]No email provided. Skipped automated transmission.[/yellow]\n")
        return True

    # 3. New Prompt: Optional identity attribution
    sender_name = None
    reveal_identity = Prompt.ask(
        "[bold white]Do you want them to know it's you who shared?[/]", 
        choices=["y", "n"], 
        default="n"
    ).lower()
    
    if reveal_identity == "y":
        sender_name = Prompt.ask("[bold white]Enter your name[/]").strip()
        if not sender_name:
            sender_name = "A colleague"
            
    # 4. Pack payload and transmit
    headers = {"X-Client-UUID": get_device_uuid()}
    payload = {
        "recipient_email": email_target, 
        "share_link": PROJECT_SHARE_LINK,
        "sender_name": sender_name 
    }
    
    console.print("\n[dim]⚡ Wait while we send the email...[/dim]")
    try:
        base_url = PROXY_SERVER_URL.replace("/v1", "")
        response = requests.post(f"{base_url}/v1/share", json=payload, headers=headers, timeout=20)
        
        if response.status_code == 200:
            console.print(Panel(
                f"[bold green]✉️ Transmission confirmed![/bold green] Feedback loop reported delivery successful.\n\n"
                f"[bold white]Recipient Target:[/bold white] {email_target}\n"
                f"[bold white]Attribution Status:[/bold white] {f'Identified as {sender_name}' if sender_name else 'Anonymous'}\n"
                f"[bold white]Resource Link Dispatched:[/bold white] [underline cyan]{PROJECT_SHARE_LINK}[/underline cyan]",
                title="Outbound Success Verification Metrics",
                border_style="green"
            ))
            return True
        else:
            reason = response.json().get("detail", "Unknown server rejection parameters.")
            console.print(f"[bold red]Server Pipeline Refusal Code ({response.status_code}):[/bold red] {reason}\n")
    except Exception as e:
        console.print(f"[bold red]Transactional Connection Handshake Failure Instance Details:[/bold red] {e}\n")
        
    return False

# ==========================================
# 🛠️ AGENT TOOLSET DEFINITIONS
# ==========================================
def get_hf_repository_metadata(repo_id: str) -> str:
    try:
        model_info = hf_api.model_info(repo_id=repo_id)
        return json.dumps({
            "repo_id": repo_id, "likes": getattr(model_info, "likes", 0),
            "downloads": getattr(model_info, "downloads", 0),
            "pipeline_tag": getattr(model_info, "pipeline_tag", "Unknown")
        })
    except Exception as e: return json.dumps({"error": str(e)})

def check_system_resources() -> str:
    total, used, free = shutil.disk_usage(".")
    return json.dumps({"available_disk_space_gb": round(free / (1024**3), 2), "os_platform": sys.platform})

def execute_system_command(command: str) -> str:
    console.print(f"\n[bold red]⚠️  CRITICAL SECURITY GATE:[/] The AI agent wants to execute this shell command:")
    console.print(Panel(f"[bold yellow]{command}[/]", border_style="red"))
    confirm = console.input("[bold white]Do you approve running this command? (y/N): [/]").strip().lower()
    if confirm not in ['y', 'yes']: return json.dumps({"status": "rejected", "error": "Blocked for safety."})
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=60)
        return json.dumps({"status": "success", "stdout": result.stdout, "stderr": result.stderr})
    except Exception as e: return json.dumps({"status": "failed", "error": str(e)})

OPENAI_FORMAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_hf_repository_metadata",
            "description": "Fetch real-time popularity trends, download counters, and likes from any Hugging Face model repository path.",
            "parameters": {
                "type": "object",
                "properties": {"repo_id": {"type": "string", "description": "The Hugging Face repository identifier"}},
                "required": ["repo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_system_resources",
            "description": "Check the local system's environment properties such as remaining free disk space (GB) and current directory.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_system_command",
            "description": "Execute an approved command inside the local terminal bash shell environment.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The exact terminal shell command sequence string to execute."}},
                "required": ["command"]
            }
        }
    }
]

#==========================================
# 🌐 GITHUB REPOSITORY QUICK ACCESS FUNCTION
#==========================================

def open_github_repository():
    """Launches the default system web browser directly to the project's source code."""
    console.print("\n🌐 [bold open]Opening GitHub Repository...[/bold open]")
    console.print(f"[dim]Directing to: {GITHUB_REPO_LINK}[/dim]\n")
    try:
        webbrowser.open(GITHUB_REPO_LINK)
        console.print("[bold green]✓ Browser initialized successfully![/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]Failed to open system browser automatically:[/] {e}\n")


# ==========================================
# Welcome Banner Dashboard
# ==========================================
def display_welcome():
    layout_grid = Table.grid(padding=(1, 0))
    layout_grid.add_column("content")
    
    welcome_text = (
        "[bold white]You are now inside the local execution sandbox environment.[/bold white]\n"
        "Ask questions about bugs, or Hugging Face, or request local file automation actions.\n\n"
        "──────────────────────────────────────────────────────────────────────────────\n"
        "[bold cyan]Available Core Actions:[/bold cyan]"
    )
    layout_grid.add_row(welcome_text)
    
    action_table = Table.grid(padding=(0, 2))
    action_table.add_column("Command Action", style="bold magenta", width=25)
    action_table.add_column("Description", style="dim white")
    
    action_table.add_row("config setup", "Enter your own API token properties (Option B).")
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f: saved_keys = json.load(f)
            if saved_keys and any(saved_keys.values()):
                action_table.add_row("config clear", "Wipe custom tokens; fall back to shared proxy (Option A).")
        except Exception: pass
    action_table.add_row("share", "Share a word about hf-bot with a friend.") # 🌟 Added share option visualization row
    action_table.add_row("repo", "Open the GitHub repository and give us a star.")
    action_table.add_row("clear", "Wipe the active terminal screen buffer layout.")
    action_table.add_row("exit / quit", "Terminate the sandbox agent workspace safely.")
    
    layout_grid.add_row(action_table)
    console.print(Panel(layout_grid, border_style="cyan", title="🤗 hf-bot Interactive Session Workspace", padding=(1, 2)))

def run_agent(initial_message: str):
    if initial_message.strip().lower() == "config setup":
        run_interactive_config_setup()
        return
    run_interactive_loop(initial_message)

# ==========================================
# 🔄 CORE EXECUTION AND STREAM INTERCEPTOR LOOP
# ==========================================
def run_interactive_loop(first_input: str):
    display_welcome()
    conversation_history = []
    current_input = first_input

    while True:
        client, model_name, is_using_proxy = load_resolved_provider_context()

        if not current_input or not current_input.strip():
            try:
                current_input = console.input("\n[bold green]hf-bot[/] ❯ ").strip()
            except (KeyboardInterrupt, EOFError):
                current_input = "exit" # Translate hardware signals into uniform software paths gracefully

        if not current_input: continue

        # 🎯 CRITICAL INTERCEPT MATRIX MODIFICATION: Trigger viral share menus on standard session termination calls
        if current_input.lower() in ["exit", "quit"]:
            print()
            wants_share = Prompt.ask(
                "[bold yellow]Before you go:[/bold yellow] Would you like to share [bold green]hf-bot[/bold green] with other developers or programmers? (y/N)",
                choices=["y", "n"],
                default="n"
            ).lower()
            
            if wants_share == "y":
                run_sharing_engine_pipeline()
                
            console.print("\n[bold cyan]Let's catchup later.[/bold cyan] [bold yellow]👋 Goodbye![/bold yellow]\n")
            break
            
        if current_input.lower() == "share":
            run_sharing_engine_pipeline()
            current_input = None
            continue

        if current_input.lower() == "repo":
            open_github_repository()
            current_input = None
            continue
            
        if current_input.lower() == "clear":
            console.print("\033[H\033[2J", end="")
            display_welcome()
            current_input = None
            continue
            
        if current_input.lower() == "config setup":
            run_interactive_config_setup()
            console.print("\033[H\033[2J", end="")
            display_welcome()
            current_input = None
            continue

        if current_input.lower() == "config clear":
            run_interactive_config_clear()
            console.print("\033[H\033[2J", end="")  
            display_welcome()                      
            current_input = None
            continue

        conversation_history.append({"role": "user", "content": current_input})
        system_intents = ["run", "execute", "ls", "cd", "file", "disk", "space", "system", "repo", "huggingface", "download"]
        should_bind_tools = any(keyword in current_input.lower() for keyword in system_intents)
        
        current_input = None  
        print()

        tool_calls_buffer = {}
        text_buffer = ""
        is_tool_call = False

        with Live(Panel(Markdown("Thinking..."), border_style="cyan", padding=(1, 2)), auto_refresh=False) as live:
            try:
                # first_stream = client.chat.completions.create(model=model_name, messages=conversation_history, tools=OPENAI_FORMAT_TOOLS, stream=True)
                first_stream = client.chat.completions.create(
                    model=model_name,
                    messages=conversation_history,
                    # 🔥 Only pass tools if the input matches system/repo keywords!
                    tools=OPENAI_FORMAT_TOOLS if should_bind_tools else None,
                    stream=True
                )
                for chunk in first_stream:
                    if not chunk.choices: continue
                    delta = chunk.choices[0].delta
                    
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        is_tool_call = True
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer: tool_calls_buffer[idx] = {"id": tc.id, "name": "", "arguments": ""}
                            if tc.id: tool_calls_buffer[idx]["id"] = tc.id
                            if tc.function and tc.function.name: tool_calls_buffer[idx]["name"] += tc.function.name
                            if tc.function and tc.function.arguments: tool_calls_buffer[idx]["arguments"] += tc.function.arguments
                        live.update(Panel(Markdown("⚙️ *Agent analyzing platform capabilities...*"), border_style="yellow"))
                        live.refresh()
                    elif hasattr(delta, "content") and delta.content:
                        text_buffer += delta.content
                        live.update(Panel(Markdown(text_buffer), border_style="cyan"))
                        live.refresh()
            except Exception as e:
                live.stop()
                if "429" in str(e) and is_using_proxy:
                    console.print(Panel("🛑 [bold red]Shared Sandbox Limit Reached (50/50 Chats Used Today).[/]\n\nTo continue running requests seamlessly, let's step up to your own private access config (Option B).", border_style="red", title="Quota Exceeded"))
                    run_interactive_config_setup()
                    conversation_history.pop()
                    continue
                else:
                    console.print(f"[bold red]Execution Stream Error:[/] {e}")
                    continue

            if is_tool_call:
                assistant_tool_msg = {"role": "assistant", "tool_calls": [{"id": v["id"], "type": "function", "function": {"name": v["name"], "arguments": v["arguments"]}} for v in tool_calls_buffer.values()]}
                conversation_history.append(assistant_tool_msg)
                first_call = list(tool_calls_buffer.values())[0]
                tool_name = first_call["name"]
                args = json.loads(first_call["arguments"]) if first_call["arguments"] else {}
                
                live.stop()
                if tool_name == "get_hf_repository_metadata": tool_output = get_hf_repository_metadata(args.get("repo_id"))
                elif tool_name == "check_system_resources": tool_output = check_system_resources()
                elif tool_name == "execute_system_command": tool_output = execute_system_command(args.get("command"))
                else: tool_output = json.dumps({"error": f"Unknown tool: {tool_name}"})

                live.start()
                conversation_history.append({"role": "tool", "tool_call_id": first_call["id"], "name": tool_name, "content": tool_output})
                try:
                    final_stream = client.chat.completions.create(model=model_name, messages=conversation_history, stream=True)
                    final_text_buffer = ""
                    for chunk in final_stream:
                        if chunk.choices and hasattr(chunk.choices[0].delta, "content"):
                            c = chunk.choices[0].delta.content
                            if c:
                                final_text_buffer += c
                                live.update(Panel(Markdown(final_text_buffer), border_style="cyan"))
                                live.refresh()
                    conversation_history.append({"role": "assistant", "content": final_text_buffer})
                except Exception as e: console.print(f"[bold red]Response Generation Error:[/] {e}")
            else: conversation_history.append({"role": "assistant", "content": text_buffer})