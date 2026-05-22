# Recipe: Multi-Agent Orchestrator

Điều phối nhiều CLI agent (Claude Code, Gemini CLI, OpenAI Codex CLI...) từ 1 entry point: nhận prompt → preflight check → chọn agent phù hợp → chạy song song / tuần tự (qua `ExecutionStrategy`) → gộp kết quả thành markdown + JSON report.

## When to use

Task signals từ user:
- "Tôi muốn điều phối nhiều agent (Claude / Gemini / Codex) trong cùng workflow"
- "Khi dùng Claude Code, tôi muốn delegate 1 step cho Gemini hoặc Codex"
- "Tool tự chọn agent nào hợp với task nào, rồi gộp output"
- "Chạy review chéo: 1 agent code, 1 agent review, 1 agent test"

Không phải:
- Chỉ dùng 1 agent → không cần orchestrator, dùng CLI gốc.
- Realtime chat multi-agent (kiểu Slack bot) → ngoài scope solo builder.
- Train/fine-tune model → khác hoàn toàn, đây là orchestration tầng CLI.

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | Async/subprocess sạch, dễ đọc cho non-tech |
| Async runtime | `asyncio` (built-in) | Chạy nhiều CLI song song không block |
| Subprocess | `asyncio.create_subprocess_exec` | Capture stdout/stderr từng agent, control process group |
| **Agent adapter layer** | Python class per vendor (`ClaudeAdapter` / `GeminiAdapter` / `CodexAdapter`) | Isolate vendor CLI drift (flags/output/auth khác nhau); FORCE non-interactive flag |
| **Execution strategy** | `ExecutionStrategy` interface (`ParallelStrategy` V1) | Stub sẵn pipeline/judge/fallback/consensus cho V2 — không refactor core |
| **Process group control** | `start_new_session=True` (POSIX) + `CREATE_NEW_PROCESS_GROUP` (Windows) | Kill cả process tree, không leak subprocess |
| **Preflight checker** | `AgentAdapter.health_check()` chạy `--version` (timeout 5s) | CLI chưa cài/chưa auth → `status: agent_unavailable`, KHÔNG crash batch |
| Routing config | YAML (`pyyaml`) | User edit file thêm agent / template / capability |
| CLI entrypoint | `typer` | Tự sinh help/autocomplete, ít boilerplate |
| Terminal UI | `rich.Console` (color only, KHÔNG Live/Panel) | Tránh rabbit hole stdout flush; output text đơn giản `[1/N] {agent} running...` |
| Report (human) | Markdown plain | Đọc trong VSCode / GitHub, schema cố định để parse được sau |
| Report (machine) | JSON | Diff / benchmark / eval future-proof |
| Path | `pathlib.Path` xuyên suốt | Cross-platform; không hardcode `/` hay `\` |

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install typer pyyaml rich
# Verify các agent CLI đã cài + auth (preflight chạy lại lúc orchestrate):
claude --version && gemini --version && codex --version
```

### Windows native (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install typer pyyaml rich
Get-Command claude, gemini, codex -ErrorAction SilentlyContinue
```

### Windows + Docker (KHÔNG khuyến nghị)

Docker khiến gọi CLI agent trên host phức tạp (mount socket, share auth token). Recipe này chạy native tốt hơn — Python + subprocess không có system deps nặng.

## Trade-offs

**Vì sao Python + asyncio + subprocess**:
- Mỗi agent đã có CLI riêng. Gọi subprocess đơn giản hơn embed SDK 3 vendor.
- `asyncio` chạy song song không cần threading.
- Code dễ extend: thêm adapter class mới + entry YAML, không sửa core.

**Vì sao có `AgentAdapter` layer (KHÔNG spawn trực tiếp từ YAML)**:
- Vendor CLI thay đổi flags / output format / auth flow nhanh và không đồng nhất (Claude `-p`, Gemini `--prompt`, Codex `exec`...). Nếu spawn trực tiếp từ YAML, mỗi lần vendor đổi flag là core orchestrator vỡ.
- Adapter cô lập drift: 1 class = 1 vendor, chứa cmd + non-interactive flag + output normalization + health_check.
- Thêm agent mới (vd Mistral) = thêm 1 class + 1 entry YAML, KHÔNG sửa core.

**Vì sao tách `ExecutionStrategy` ngay V1 (chỉ build Parallel)**:
- Chi phí thiết kế interface ≈ 0 (1 abstract base class).
- Sớm muộn cũng cần pipeline (B đọc output A), judge (2 agent + 1 trọng tài), fallback (Claude fail → Gemini), consensus (so output). Nếu nhồi vào `run()` thẳng, sau refactor core.
- V1 chỉ build `ParallelStrategy` — phần còn lại stub.

**Vì sao KHÔNG alternative**:
- **Node.js + child_process**: Claude Code là Node, có vẻ tự nhiên. Nhưng Python ecosystem cho CLI tooling tốt hơn, và pack-solo-builder default Python — user không cần học stack mới.
- **LangChain / CrewAI / AutoGen**: framework agent-based heavy, lock-in API, thiết kế cho LLM call trực tiếp chứ không phải orchestrate CLI tools.
- **Claude Code subagents (built-in)**: chỉ điều phối Claude. Không gọi được Gemini/Codex.
- **MCP server**: MCP là protocol tool inside-host, không phải orchestrator giữa nhiều host.
- **Bash + xargs**: parallel OK nhưng khó parse structured output, khó retry, khó cross-platform.
- **GNU Make**: rule-based đơn giản, routing động bất tiện.
- **Rich Live/Panel UI**: stdout flush behavior khác nhau giữa vendor (Claude stream token, Gemini buffer, Codex flush khác) → rabbit hole. V1 dùng text đơn giản.

## Skeleton

```python
# orchestrator.py — Multi-agent CLI orchestrator (V1: parallel + markdown/JSON report)
import asyncio
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

app = typer.Typer()
console = Console()

CONFIG_PATH = Path("agents.yaml")
REPORTS_ROOT = Path("reports")

# ─────────────────────────── Data ───────────────────────────

@dataclass
class AgentResult:
    name: str
    status: str  # "success" | "failed" | "timed_out" | "agent_unavailable"
    exit_code: Optional[int]
    stdout: str
    stderr: str
    duration_s: float
    cmd: list[str] = field(default_factory=list)
    # Cost schema — defer fill V1, schema-ready cho V2 (mỗi adapter parse --usage):
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None


# ─────────────────────────── Adapter ───────────────────────────

class AgentAdapter(ABC):
    """Cô lập 1 vendor CLI. Concrete class PHẢI:
    - Set non-interactive flag (vd `-p`, `--prompt`, `exec`, `--no-tty`).
    - Set `CLI_VERSION_TESTED = "<vendor> <major.minor>"` để detect drift.
    - Implement `health_check()` (probe `--version` hoặc tương đương).
    - Implement `build_cmd(prompt)` trả về list[str] sẵn sàng `create_subprocess_exec`.
    """
    CLI_VERSION_TESTED: str = ""   # override per subclass; major diff → warning
    name: str
    cmd_base: list[str]
    template: Optional[str] = None

    def __init__(self, name: str, cmd_base: list[str], template: Optional[str] = None):
        self.name = name
        self.cmd_base = cmd_base
        self.template = template

    def render_prompt(self, prompt: str) -> str:
        if not self.template:
            return prompt
        return self.template.replace("{{prompt}}", prompt)

    @abstractmethod
    def build_cmd(self, prompt: str) -> list[str]:
        ...

    async def health_check(self, timeout: float = 5.0) -> bool:
        """Probe CLI tồn tại + responsive. Subclass override nếu vendor không có --version."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.cmd_base[0], "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return False
            return proc.returncode == 0
        except FileNotFoundError:
            return False

    async def run(self, prompt: str, timeout: float = 300.0) -> AgentResult:
        rendered = self.render_prompt(prompt)
        cmd = self.build_cmd(rendered)
        started = time.monotonic()

        # Cross-platform process group: kill cả children khi timeout.
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            preexec_fn = None
            start_new_session = False
        else:
            creationflags = 0
            preexec_fn = None
            start_new_session = True

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=creationflags,
                start_new_session=start_new_session,
            )
        except FileNotFoundError:
            return AgentResult(self.name, "agent_unavailable", None, "", f"CLI not found: {cmd[0]}", 0.0, cmd)

        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = time.monotonic() - started
            status = "success" if proc.returncode == 0 else "failed"
            return AgentResult(
                self.name, status, proc.returncode,
                stdout_b.decode("utf-8", errors="replace"),
                stderr_b.decode("utf-8", errors="replace"),
                duration, cmd,
            )
        except asyncio.TimeoutError:
            _kill_process_tree(proc)
            duration = time.monotonic() - started
            return AgentResult(self.name, "timed_out", None, "", f"timeout after {timeout}s", duration, cmd)


def _kill_process_tree(proc: asyncio.subprocess.Process):
    """Kill toàn bộ process group, không chỉ pid. Tránh leak child subprocess (đặc biệt Node-based Claude CLI)."""
    if proc.returncode is not None:
        return
    try:
        if sys.platform == "win32":
            # CREATE_NEW_PROCESS_GROUP cho phép send CTRL_BREAK_EVENT → terminate cả tree.
            # Fallback: taskkill /T /F /PID.
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                           capture_output=True, check=False)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            # grace period rồi SIGKILL nếu còn.
    except (ProcessLookupError, PermissionError):
        pass


# Concrete adapters — non-interactive flag bắt buộc.
class ClaudeAdapter(AgentAdapter):
    """Claude Code CLI. Non-interactive: `claude -p <prompt>` (print mode, không TUI)."""
    CLI_VERSION_TESTED = "claude-code 1.0"

    def build_cmd(self, prompt: str) -> list[str]:
        return [*self.cmd_base, prompt]

class GeminiAdapter(AgentAdapter):
    """Gemini CLI. Non-interactive: `gemini --prompt <prompt>`."""
    CLI_VERSION_TESTED = "gemini 0.1"

    def build_cmd(self, prompt: str) -> list[str]:
        return [*self.cmd_base, prompt]

class CodexAdapter(AgentAdapter):
    """OpenAI Codex CLI. Non-interactive: `codex exec <prompt>`."""
    CLI_VERSION_TESTED = "codex 0.1"

    def build_cmd(self, prompt: str) -> list[str]:
        return [*self.cmd_base, prompt]

ADAPTER_REGISTRY = {
    "claude": ClaudeAdapter,
    "gemini": GeminiAdapter,
    "codex": CodexAdapter,
}


# ─────────────────────────── Strategy ───────────────────────────

class ExecutionStrategy(ABC):
    @abstractmethod
    async def run(self, adapters: list[AgentAdapter], prompt: str, timeout: float) -> list[AgentResult]:
        ...

class ParallelStrategy(ExecutionStrategy):
    """V1: chạy song song độc lập. Mọi agent nhận cùng prompt (đã render qua template riêng)."""
    async def run(self, adapters, prompt, timeout):
        # Preflight: probe tất cả trước.
        health = await asyncio.gather(*[a.health_check() for a in adapters])
        results: list[AgentResult] = []
        to_run = []
        for adapter, ok in zip(adapters, health):
            if ok:
                to_run.append(adapter)
            else:
                results.append(AgentResult(
                    adapter.name, "agent_unavailable", None, "",
                    "preflight failed: CLI missing or not authed", 0.0, adapter.cmd_base,
                ))
        ran = await asyncio.gather(*[a.run(prompt, timeout) for a in to_run])
        return results + list(ran)

# Stub cho V2 — chưa implement, chỉ định nghĩa shape.
# class PipelineStrategy(ExecutionStrategy): ...
# class JudgeStrategy(ExecutionStrategy): ...
# class FallbackStrategy(ExecutionStrategy): ...
# class ConsensusStrategy(ExecutionStrategy): ...

STRATEGY_REGISTRY = {"parallel": ParallelStrategy}


# ─────────────────────────── Routing ───────────────────────────

def pick_agents(prompt: str, config: dict) -> tuple[list[str], Optional[dict]]:
    """Return (selected_agent_names, matched_route_dict_or_None)."""
    for rule in config.get("routes", []):
        if any(kw.lower() in prompt.lower() for kw in rule.get("keywords", [])):
            return rule["agents"], rule
    return config.get("default_agents", []), None


def load_adapters(names: list[str], config: dict) -> list[AgentAdapter]:
    out = []
    for n in names:
        spec = config["agents"][n]
        cls = ADAPTER_REGISTRY[spec["adapter"]]
        out.append(cls(name=n, cmd_base=spec["cmd"], template=spec.get("template")))
    return out


# ─────────────────────────── Report ───────────────────────────

def write_reports(results: list[AgentResult], prompt: str, selected: list[str],
                  matched_route: Optional[dict], total_duration: float) -> tuple[Path, Path]:
    sha12 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    now = datetime.now()
    day_dir = REPORTS_ROOT / now.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    base = f"orchestration-{now.strftime('%H%M%S')}-{sha12}"
    md_path = day_dir / f"{base}.md"
    json_path = day_dir / f"{base}.json"

    counts = {"success": 0, "failed": 0, "timed_out": 0, "agent_unavailable": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    metadata = {
        "timestamp": now.isoformat(),
        "prompt": prompt,
        "prompt_sha": sha12,
        "selected_agents": selected,
        "matched_route": matched_route,
        "total_duration_s": total_duration,
        "summary": counts,
    }

    # JSON
    json_path.write_text(json.dumps({
        "metadata": metadata,
        "agents": [asdict(r) for r in results],
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown — schema cố định: ## Metadata / ## Agent: X / ## Summary
    lines = ["# Orchestration Report", "", "## Metadata", ""]
    for k, v in metadata.items():
        lines.append(f"- **{k}**: `{v}`")
    lines.append("")
    for r in results:
        lines += [
            f"## Agent: {r.name}",
            "",
            f"- **Status**: `{r.status}`",
            f"- **Exit code**: `{r.exit_code}`",
            f"- **Duration**: `{r.duration_s:.2f}s`",
            "",
            "### Stdout", "```", r.stdout[:8000], "```", "",
            "### Stderr", "```", r.stderr[:2000], "```", "",
        ]
    lines += ["## Summary", ""]
    for k, v in counts.items():
        lines.append(f"- {k}: {v}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # latest pointer — copy file (đồng nhất 2 OS, tránh symlink fail trên Windows non-dev-mode).
    latest_md = REPORTS_ROOT / "latest.md"
    latest_json = REPORTS_ROOT / "latest.json"
    shutil.copyfile(md_path, latest_md)
    shutil.copyfile(json_path, latest_json)

    return md_path, json_path


# ─────────────────────────── CLI ───────────────────────────

@app.command()
def run(prompt: str, timeout: float = 300.0):
    """Điều phối agents theo prompt. V1: parallel only."""
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    names, route = pick_agents(prompt, config)
    if not names:
        console.print("[red]No agents selected (no route matched + no default_agents).[/red]")
        raise typer.Exit(2)
    console.print(f"Selected: {names}  (route: {route['keywords'] if route else 'default'})")

    adapters = load_adapters(names, config)
    strategy_name = config.get("strategy", "parallel")
    strategy = STRATEGY_REGISTRY[strategy_name]()

    started = time.monotonic()
    for i, n in enumerate(names, 1):
        console.print(f"[{i}/{len(names)}] {n} running...")
    results = asyncio.run(strategy.run(adapters, prompt, timeout))
    total = time.monotonic() - started

    for r in results:
        console.print(f"[DONE] {r.name} ({r.duration_s:.1f}s, {r.status})")

    md, js = write_reports(results, prompt, names, route, total)
    console.print(f"[green]✓ Report: {md}[/green]")
    console.print(f"[green]✓ JSON:   {js}[/green]")

if __name__ == "__main__":
    app()
```

```yaml
# agents.yaml — routing + per-agent config
agents:
  claude:
    adapter: claude
    cmd: ["claude", "-p"]          # non-interactive flag bắt buộc
    template: |
      Review architecture and reasoning:
      {{prompt}}
    capabilities: [architecture, reasoning, refactor]
  gemini:
    adapter: gemini
    cmd: ["gemini", "--prompt"]
    capabilities: [long-context, cross-check]
  codex:
    adapter: codex
    cmd: ["codex", "exec"]
    template: |
      Write tests only for:
      {{prompt}}
    capabilities: [tests, refactor]

strategy: parallel                  # parallel | (V2: pipeline | judge | fallback | consensus)
default_agents: [claude]

routes:
  - keywords: [review, audit, security]
    agents: [claude, gemini]
  - keywords: [test, "unit test", pytest]
    agents: [codex]
  - keywords: [refactor, complex, lớn]
    agents: [claude, codex, gemini]
```

Chạy:
```bash
python orchestrator.py run "review file auth.py có lỗ hổng nào không"
# → preflight check → Claude + Gemini song song → reports/YYYY-MM-DD/orchestration-*.{md,json} + reports/latest.{md,json}
```

## Decision tree

✅ **Match recipe này KHI**:
- Cần gọi ≥ 2 CLI agent khác vendor trong cùng workflow.
- Mỗi agent đã có CLI riêng (`claude`, `gemini`, `codex`...).
- Output dạng text/markdown, không cần streaming UI tinh vi.
- Solo / small team, chấp nhận config YAML manual.

❌ **KHÔNG match KHI**:
- Chỉ dùng 1 agent → dùng CLI gốc.
- Cần realtime UI multi-pane web → recipe `team-shared-web-tool` phù hợp hơn.
- Cần state-machine phức tạp ngoài Parallel/Pipeline/Judge/Fallback/Consensus → cân nhắc LangGraph.
- Cần token-level realtime streaming UI → V1 không cover (stdout flush behavior khác nhau giữa vendor là rabbit hole).
- Cần SLA / production uptime → recipe này solo/dev workflow, không HA.

## Notes

- **LUÔN kill process group**, không chỉ pid — tránh leak subprocess (đặc biệt Node-based Claude CLI spawn child Node process).
- **LUÔN dùng non-interactive flag** ở adapter — vendor CLI default vào TUI sẽ treo subprocess.
- **LUÔN ghi JSON song song markdown** — markdown cho người đọc, JSON cho diff/benchmark/eval sau.
- **LUÔN hash prompt** vào filename (`sha256[:12]`) — dedupe + truy ngược cùng 1 prompt qua các lần chạy.
- **LUÔN decode stdout/stderr với `errors="replace"`** — Windows console hay cp1252, prompt có emoji sẽ crash nếu không.
- **LUÔN preflight `--version`** trước khi spawn — CLI chưa cài/chưa auth → mark `agent_unavailable`, không crash batch.
- **LUÔN `pathlib.Path`** — không hardcode `/` hay `\` trong code.
- **Capability metadata** chuẩn bị sẵn dù V1 routing chỉ keyword — tránh schema migration khi V2 thêm LLM classifier.
- **KHÔNG paste secret vào prompt** — prompt được log vào report markdown + JSON.
- **Cost tracking**: ngoài V1. Mỗi vendor flag `--usage` khác nhau, append sau khi cần.
