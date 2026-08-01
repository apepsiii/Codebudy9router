"""
==========================================================
  Professional TUI Dashboard Module
  QwenCloud API Key Generator — btop/lazygit style
==========================================================

Uses Rich library for terminal rendering.
Thread-safe state management for concurrent workers.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import threading
import time

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# ── Enums ─────────────────────────────────────────────────


class Stage(str, Enum):
    """Processing stages — reflects actual backend steps."""
    INITIALIZE = "Initialize"
    CREATE_EMAIL = "Create Email"
    REQUEST_SSO = "Request SSO"
    OAUTH_REDIRECT = "OAuth Redirect"
    EXCHANGE_TOKEN = "Exchange Token"
    CREATE_SESSION = "Create Session"
    VERIFY_ACCOUNT = "Verify Account"
    GENERATE_API_KEY = "Generate API Key"
    SAVE_RESULT = "Save Result"
    COMPLETED = "Completed"


class Status(str, Enum):
    """Account status values."""
    WAITING = "WAITING"
    CONNECTING = "CONNECTING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY = "RETRY"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    REDIRECT = "REDIRECT"
    VERIFYING = "VERIFYING"


class ErrorCategory(str, Enum):
    """Error categories for grouping."""
    RATE_LIMIT = "429 Rate Limit"
    TIMEOUT = "Timeout"
    NETWORK = "Network Error"
    INVALID_SESSION = "Invalid Session"
    EMAIL_EXISTS = "Email Exists"
    CAPTCHA = "Captcha Failed"
    OAUTH_ERROR = "OAuth Error"
    TOKEN_ERROR = "Token Creation Failed"
    UNKNOWN = "Unknown Error"


# ── Stage Progress Mapping ────────────────────────────────

STAGE_PROGRESS: Dict[Stage, int] = {
    Stage.INITIALIZE: 0,
    Stage.CREATE_EMAIL: 5,
    Stage.REQUEST_SSO: 10,
    Stage.OAUTH_REDIRECT: 20,
    Stage.EXCHANGE_TOKEN: 35,
    Stage.CREATE_SESSION: 50,
    Stage.VERIFY_ACCOUNT: 65,
    Stage.GENERATE_API_KEY: 80,
    Stage.SAVE_RESULT: 90,
    Stage.COMPLETED: 100,
}


# ── Status Color Mapping ──────────────────────────────────

STATUS_COLORS: Dict[Status, str] = {
    Status.SUCCESS: "bold green",
    Status.FAILED: "bold red",
    Status.WAITING: "yellow",
    Status.RETRY: "yellow",
    Status.PROCESSING: "cyan",
    Status.CONNECTING: "blue",
    Status.RATE_LIMIT: "bold magenta",
    Status.TIMEOUT: "red",
    Status.REDIRECT: "blue",
    Status.VERIFYING: "cyan",
}


# ── Data Classes ──────────────────────────────────────────


@dataclass
class AccountInfo:
    """Tracks one account's processing state."""
    index: int
    email: str
    worker_id: int
    stage: Stage = Stage.INITIALIZE
    status: Status = Status.WAITING
    progress: int = 0
    retry_count: int = 0
    max_retries: int = 3
    start_time: float = 0.0
    elapsed_ms: int = 0
    country: str = ""
    proxy_label: str = ""
    error_category: Optional[ErrorCategory] = None
    error_message: str = ""
    is_active: bool = True
    finish_time: float = 0.0


# ── Event Log ─────────────────────────────────────────────


class EventLog:
    """Scrolling event log — keeps last N events."""

    def __init__(self, maxlen: int = 50):
        self._events: deque = deque(maxlen=maxlen)

    def add(self, account_index: int, message: str, style: str = ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._events.append((timestamp, account_index, message, style))

    def get_recent(self, count: int = 20) -> list:
        return list(self._events)[-count:]

    def clear(self):
        self._events.clear()


# ── Dashboard State (Thread-Safe) ─────────────────────────


class DashboardState:
    """
    Central state manager for the TUI dashboard.
    All public methods are thread-safe (uses threading.Lock).
    """

    def __init__(self, total_accounts: int, num_workers: int = 2, public_ip: str = "Unknown"):
        self.lock = threading.Lock()
        self.public_ip = public_ip
        self.total_accounts = total_accounts
        self.num_workers = num_workers
        self.start_time = time.time()

        # Account tracking
        self.accounts: Dict[int, AccountInfo] = {}
        self.active_accounts: List[int] = []
        self.completed_accounts: List[int] = []

        # Counters
        self.success_count: int = 0
        self.failed_count: int = 0
        self.retry_count: int = 0

        # Error summary
        self.error_summary: Dict[ErrorCategory, int] = {}

        # Event log
        self.event_log = EventLog(maxlen=50)

        # Performance metrics
        self.request_count: int = 0
        self.total_response_time: float = 0.0
        self.total_registration_time: float = 0.0

        # Worker state
        self.workers: Dict[int, dict] = {}
        for i in range(1, num_workers + 1):
            self.workers[i] = {"status": "Idle", "email": "", "index": 0}

    # ── Account Lifecycle ─────────────────────────────────

    def start_account(self, index: int, email: str, worker_id: int,
                      country: str = "", proxy_label: str = ""):
        """Register a new account being processed."""
        with self.lock:
            account = AccountInfo(
                index=index,
                email=email,
                worker_id=worker_id,
                status=Status.CONNECTING,
                stage=Stage.INITIALIZE,
                start_time=time.time(),
                country=country,
                proxy_label=proxy_label,
            )
            self.accounts[index] = account
            if index not in self.active_accounts:
                self.active_accounts.append(index)
            self.workers[worker_id] = {
                "status": "Processing",
                "email": email,
                "index": index,
            }
            self.event_log.add(index, "Started processing", "cyan")

    def update_account(self, index: int, stage: Optional[Stage] = None,
                       status: Optional[Status] = None, progress: Optional[int] = None,
                       error_category: Optional[ErrorCategory] = None,
                       error_message: str = ""):
        """Update an account's processing state."""
        with self.lock:
            if index not in self.accounts:
                return

            account = self.accounts[index]

            if stage is not None:
                account.stage = stage
                # Auto-set progress from stage if not explicitly provided
                if progress is None:
                    progress = STAGE_PROGRESS.get(stage, account.progress)

            if status is not None:
                account.status = status
            if progress is not None:
                account.progress = min(100, max(0, progress))
            if error_category is not None:
                account.error_category = error_category
            if error_message:
                account.error_message = error_message

            account.elapsed_ms = int((time.time() - account.start_time) * 1000)

            # Log stage changes
            if stage is not None:
                style = STATUS_COLORS.get(account.status, "white")
                self.event_log.add(
                    index,
                    f"{stage.value} — {account.status.value}",
                    style,
                )

            # Update worker
            self.workers[account.worker_id] = {
                "status": account.status.value,
                "email": account.email,
                "index": index,
            }

    def finish_account(self, index: int, success: bool,
                       error_category: Optional[ErrorCategory] = None,
                       error_message: str = ""):
        """Mark an account as finished."""
        with self.lock:
            if index not in self.accounts:
                return

            account = self.accounts[index]
            account.finish_time = time.time()
            account.elapsed_ms = int((account.finish_time - account.start_time) * 1000)
            account.is_active = False

            if success:
                account.status = Status.SUCCESS
                account.stage = Stage.COMPLETED
                account.progress = 100
                self.success_count += 1
                self.event_log.add(index, f"SUCCESS ({account.elapsed_ms}ms)", "bold green")
            else:
                account.status = Status.FAILED
                account.error_category = error_category or ErrorCategory.UNKNOWN
                account.error_message = error_message
                self.failed_count += 1
                cat = account.error_category.value
                self.error_summary[account.error_category] = (
                    self.error_summary.get(account.error_category, 0) + 1
                )
                self.event_log.add(index, f"FAILED: {cat}", "bold red")

            # Track registration time
            self.total_registration_time += (account.finish_time - account.start_time)
            self.request_count += 1

            # Move from active to completed
            if index in self.active_accounts:
                self.active_accounts.remove(index)
            if index not in self.completed_accounts:
                self.completed_accounts.append(index)

            # Reset worker
            wid = account.worker_id
            self.workers[wid] = {"status": "Idle", "email": "", "index": 0}

    def retry_account(self, index: int):
        """Increment retry count for an account."""
        with self.lock:
            if index not in self.accounts:
                return
            account = self.accounts[index]
            account.retry_count += 1
            account.status = Status.RETRY
            account.stage = Stage.INITIALIZE
            account.progress = 0
            self.retry_count += 1
            self.event_log.add(
                index,
                f"RETRY ({account.retry_count}/{account.max_retries})",
                "yellow",
            )

    # ── Metrics ───────────────────────────────────────────

    def get_elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def get_accounts_per_minute(self) -> float:
        elapsed = self.get_elapsed_seconds()
        if elapsed < 1:
            return 0.0
        return (self.success_count + self.failed_count) / elapsed * 60

    def get_requests_per_second(self) -> float:
        elapsed = self.get_elapsed_seconds()
        if elapsed < 1:
            return 0.0
        return self.request_count / elapsed

    def get_avg_registration_time(self) -> float:
        total = self.success_count + self.failed_count
        if total == 0:
            return 0.0
        return self.total_registration_time / total

    def get_success_rate(self) -> float:
        total = self.success_count + self.failed_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100

    def get_failure_rate(self) -> float:
        return 100.0 - self.get_success_rate()

    def get_completed_count(self) -> int:
        return self.success_count + self.failed_count

    def get_overall_progress(self) -> int:
        if self.total_accounts == 0:
            return 0
        return int(self.get_completed_count() / self.total_accounts * 100)

    def get_display_accounts(self, max_rows: int = 50) -> List[AccountInfo]:
        """
        Get accounts for display: active first, then recently completed.
        Completed accounts stay visible for ~10 seconds after finishing.
        """
        with self.lock:
            result: List[AccountInfo] = []

            # Active accounts first
            for idx in self.active_accounts:
                if idx in self.accounts:
                    result.append(self.accounts[idx])

            # Recently completed (within last 10 seconds)
            now = time.time()
            for idx in reversed(self.completed_accounts):
                if idx in self.accounts:
                    account = self.accounts[idx]
                    if now - account.finish_time < 10.0:
                        result.append(account)
                    else:
                        break

            return result[:max_rows]


# ── Layout Generator ──────────────────────────────────────


def _format_elapsed(seconds: float) -> str:
    """Format seconds into HH:MM:SS."""
    secs = int(seconds)
    h, remainder = divmod(secs, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _make_progress_bar(pct: int, width: int = 8) -> str:
    """Generate a text progress bar."""
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


def generate_layout(state: DashboardState) -> Panel:
    """
    Generate the complete dashboard layout.
    Returns a Rich Panel ready for Live.update().
    """

    # ── Header ────────────────────────────────────────────

    elapsed_str = _format_elapsed(state.get_elapsed_seconds())
    accounts_per_min = state.get_accounts_per_minute()
    running = len(state.active_accounts)
    queue = state.total_accounts - state.get_completed_count() - running
    if queue < 0:
        queue = 0

    header_line1 = Text()
    header_line1.append("Accounts : ", style="dim")
    header_line1.append(f"{state.total_accounts:<6}", style="bold white")
    header_line1.append("Workers : ", style="dim")
    header_line1.append(f"{state.num_workers:<5}", style="bold white")
    header_line1.append("Running : ", style="dim")
    header_line1.append(f"{running:<5}", style="bold cyan")
    header_line1.append("Queue : ", style="dim")
    header_line1.append(f"{queue}", style="bold white")

    header_line2 = Text()
    header_line2.append("Success : ", style="dim")
    header_line2.append(f"{state.success_count:<6}", style="bold green")
    header_line2.append("Failed  : ", style="dim")
    header_line2.append(f"{state.failed_count:<6}", style="bold red")
    header_line2.append("Retry   : ", style="dim")
    header_line2.append(f"{state.retry_count}", style="bold yellow")

    header_line3 = Text()
    header_line3.append("Speed   : ", style="dim")
    header_line3.append(f"{accounts_per_min:.1f} acc/min", style="bold green")
    header_line3.append("    Elapsed : ", style="dim")
    header_line3.append(f"{elapsed_str}", style="bold white")
    header_line3.append("    IP : ", style="dim")
    header_line3.append(f"{state.public_ip}", style="bold magenta")

    header = Panel(
        Group(header_line1, header_line2, header_line3),
        title="[bold bright_white]Kiro API Key Bot v1.0[/]",
        border_style="orange1",
        padding=(0, 2),
    )

    # ── Main Table ────────────────────────────────────────

    table = Table(
        box=box.HEAVY_EDGE,
        show_header=True,
        header_style="bold bright_white on grey11",
        border_style="orange1",
        padding=(0, 1),
        expand=True,
        row_styles=["", "dim"],
    )

    table.add_column("#", width=4, justify="right", style="dim")
    table.add_column("Email", min_width=20, max_width=30, no_wrap=True, overflow="ellipsis")
    table.add_column("Work.", width=5, justify="center")
    table.add_column("Stage", min_width=12, max_width=16)
    table.add_column("Status", min_width=10, max_width=14)
    table.add_column("Progress", min_width=12, max_width=16)
    table.add_column("Retry", width=5, justify="center")
    table.add_column("MS", width=6, justify="right")
    table.add_column("Country", min_width=8, max_width=12)

    display_accounts = state.get_display_accounts(max_rows=40)

    for account in display_accounts:
        # Status style
        status_color = STATUS_COLORS.get(account.status, "white")
        status_text = Text(account.status.value, style=status_color)

        # Stage style
        stage_color = "green" if account.stage == Stage.COMPLETED else "cyan"
        stage_text = Text(account.stage.value[:16], style=stage_color)

        # Progress bar
        pct = account.progress
        bar = _make_progress_bar(pct, 8)
        progress_text = Text()
        bar_style = "green" if pct >= 100 else "cyan"
        progress_text.append(f"{bar} ", style=bar_style)
        progress_text.append(f"{pct:>3}%", style=status_color)

        # Retry
        retry_str = f"{account.retry_count}/{account.max_retries}"
        retry_style = "yellow" if account.retry_count > 0 else "dim"

        # Email truncation
        email = account.email
        if len(email) > 28:
            email = email[:25] + "..."

        # Country
        country = account.country or "---"

        # Dim completed accounts
        row_style = "dim" if not account.is_active else ""

        table.add_row(
            Text(str(account.index), style="dim"),
            Text(email, style="bright_white" if account.is_active else "grey50"),
            Text(f"{account.worker_id:>3}", style="yellow" if account.is_active else "grey50"),
            stage_text,
            status_text,
            progress_text,
            Text(retry_str, style=retry_style),
            Text(f"{account.elapsed_ms}", style="dim"),
            Text(country, style="bright_white" if account.is_active else "grey50"),
            style=row_style,
        )

    if not display_accounts:
        table.add_row(
            Text("---", style="dim"),
            Text("Waiting for accounts...", style="dim"),
            Text("---", style="dim"),
            Text("---", style="dim"),
            Text("---", style="dim"),
            Text("---", style="dim"),
            Text("---", style="dim"),
            Text("---", style="dim"),
            Text("---", style="dim"),
        )

    # ── Event Log Panel ───────────────────────────────────

    events = state.event_log.get_recent(20)
    event_lines: List[Text] = []

    for timestamp, acc_idx, message, style in events:
        line = Text()
        line.append(f"  {timestamp}  ", style="dim")
        line.append(f"#{acc_idx:<4}", style="bold bright_white")
        line.append(f" {message}", style=style or "white")
        event_lines.append(line)

    if not event_lines:
        event_lines.append(Text("  Waiting for activity...", style="dim"))

    event_log_panel = Panel(
        Group(*event_lines),
        title="[bold bright_white]Recent Events[/]",
        border_style="blue",
        padding=(0, 1),
    )

    # ── Error Summary Panel ───────────────────────────────

    error_lines: List[Text] = []

    if state.error_summary:
        for category, count in sorted(state.error_summary.items(), key=lambda x: -x[1]):
            line = Text()
            line.append(f"  {category.value:<22}", style="white")
            line.append(" : ", style="dim")
            line.append(f"{count}", style="bold red")
            error_lines.append(line)
    else:
        error_lines.append(Text("  No errors", style="dim"))

    error_panel = Panel(
        Group(*error_lines),
        title="[bold bright_white]Error Summary[/]",
        border_style="red",
        padding=(0, 1),
    )

    # ── Performance Panel ─────────────────────────────────

    avg_time = state.get_avg_registration_time()
    success_rate = state.get_success_rate()
    req_per_sec = state.get_requests_per_second()
    acc_per_min = state.get_accounts_per_minute()

    perf_line1 = Text()
    perf_line1.append("  Req/sec       : ", style="dim")
    perf_line1.append(f"{req_per_sec:<8.1f}", style="bold bright_white")
    perf_line1.append("Acc/min       : ", style="dim")
    perf_line1.append(f"{acc_per_min:.1f}", style="bold bright_white")

    perf_line2 = Text()
    perf_line2.append("  Avg Time      : ", style="dim")
    perf_line2.append(f"{avg_time:<8.1f} sec", style="bold bright_white")
    perf_line2.append("Success Rate  : ", style="dim")
    rate_color = "bold green" if success_rate >= 90 else "bold yellow" if success_rate >= 70 else "bold red"
    perf_line2.append(f"{success_rate:.1f}%", style=rate_color)

    perf_panel = Panel(
        Group(perf_line1, perf_line2),
        title="[bold bright_white]Performance[/]",
        border_style="green",
        padding=(0, 1),
    )

    # ── Overall Progress Bar ──────────────────────────────

    overall_pct = state.get_overall_progress()
    bar_width = 40
    filled = int(bar_width * overall_pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)

    progress_line = Text()
    progress_line.append(f"  {bar} ", style="cyan" if overall_pct < 100 else "green")
    progress_line.append(f"{overall_pct}%", style="bold bright_white")

    overall_panel = Panel(
        progress_line,
        title="[bold bright_white]Overall Progress[/]",
        border_style="cyan",
        padding=(0, 1),
    )

    # ── Compose Layout ────────────────────────────────────

    # Bottom row: Error Summary + Performance side by side
    bottom_table = Table(box=None, expand=True, show_header=False, padding=0)
    bottom_table.add_column(ratio=1)
    bottom_table.add_column(ratio=2)
    bottom_table.add_row(error_panel, perf_panel)

    # Combine all sections
    layout = Group(
        header,
        table,
        event_log_panel,
        bottom_table,
        overall_panel,
    )

    return Panel(
        layout,
        border_style="orange1",
        padding=(0, 0),
    )
