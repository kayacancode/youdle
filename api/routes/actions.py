"""
GitHub Actions API Routes
Endpoints for managing GitHub Actions workflows - list, trigger, cancel, enable/disable.
"""
import sys
import os

# Load environment variables from parent directory's .env file
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))
except ImportError:
    pass
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import httpx
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class WorkflowInput(BaseModel):
    """Input definition for workflow_dispatch"""
    name: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[str] = None
    type: str = "string"  # "string", "boolean", "choice"
    options: Optional[List[str]] = None


class Workflow(BaseModel):
    """GitHub Actions workflow"""
    id: int
    name: str
    path: str
    state: str  # "active", "disabled_manually", etc.
    created_at: str
    updated_at: str
    html_url: str
    badge_url: str
    schedule: Optional[str] = None
    inputs: List[WorkflowInput] = []


class WorkflowRun(BaseModel):
    """GitHub Actions workflow run"""
    id: int
    name: str
    workflow_id: int
    status: str  # "queued", "in_progress", "completed"
    conclusion: Optional[str] = None  # "success", "failure", "cancelled", etc.
    event: str  # "schedule", "workflow_dispatch", "push", etc.
    created_at: str
    updated_at: str
    run_started_at: Optional[str] = None
    html_url: str
    actor: Optional[str] = None
    run_number: int
    duration_seconds: Optional[int] = None


class WorkflowListResponse(BaseModel):
    workflows: List[Workflow]


class WorkflowRunListResponse(BaseModel):
    runs: List[WorkflowRun]
    total_count: int


class TriggerWorkflowRequest(BaseModel):
    ref: str = "main"
    inputs: Dict[str, Any] = {}


class TriggerWorkflowResponse(BaseModel):
    message: str
    workflow_id: int
    ref: str


class CancelRunResponse(BaseModel):
    message: str
    run_id: int


class ActionsStatus(BaseModel):
    configured: bool
    owner: Optional[str] = None
    repo: Optional[str] = None
    workflow_count: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# GitHub Actions Client
# ============================================================================

class GitHubActionsClient:
    """Client for GitHub Actions REST API"""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.owner = os.getenv("GITHUB_OWNER")
        self.repo = os.getenv("GITHUB_REPO")

        if not all([self.token, self.owner, self.repo]):
            raise ValueError("Missing GITHUB_TOKEN, GITHUB_OWNER, or GITHUB_REPO environment variables")

        self.base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def list_workflows(self) -> Dict[str, Any]:
        """GET /repos/{owner}/{repo}/actions/workflows"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/actions/workflows",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_workflow_file(self, workflow_path: str) -> str:
        """GET /repos/{owner}/{repo}/contents/{path} - returns raw YAML content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/contents/{workflow_path}",
                headers={**self.headers, "Accept": "application/vnd.github.raw+json"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.text

    async def list_workflow_runs(
        self,
        workflow_id: Optional[int] = None,
        status: Optional[str] = None,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """GET /repos/{owner}/{repo}/actions/runs or /workflows/{id}/runs"""
        params = {"per_page": per_page}
        if status:
            params["status"] = status

        if workflow_id:
            url = f"{self.base_url}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"{self.base_url}/actions/runs"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def trigger_workflow(
        self,
        workflow_id: int,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None
    ) -> None:
        """POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"""
        body = {"ref": ref}
        if inputs:
            # Convert all values to strings as required by GitHub API
            body["inputs"] = {k: str(v) if not isinstance(v, str) else v for k, v in inputs.items()}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/actions/workflows/{workflow_id}/dispatches",
                headers=self.headers,
                json=body,
                timeout=30.0
            )
            # Returns 204 No Content on success
            response.raise_for_status()

    async def cancel_run(self, run_id: int) -> None:
        """POST /repos/{owner}/{repo}/actions/runs/{run_id}/cancel"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/actions/runs/{run_id}/cancel",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()

    async def enable_workflow(self, workflow_id: int) -> None:
        """PUT /repos/{owner}/{repo}/actions/workflows/{workflow_id}/enable"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/actions/workflows/{workflow_id}/enable",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()

    async def disable_workflow(self, workflow_id: int) -> None:
        """PUT /repos/{owner}/{repo}/actions/workflows/{workflow_id}/disable"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/actions/workflows/{workflow_id}/disable",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()


# ============================================================================
# Helper Functions
# ============================================================================

def cron_to_human(cron: str) -> str:
    """Convert cron expression to human-readable format (CST)"""
    # Map common patterns used in this project
    patterns = {
        "0 15 * * 2": "Tuesdays 9 AM CST",
        "0 15 * * 4": "Thursdays 9 AM CST",
        "0 2 * * 3": "Tuesdays 8 PM CST",
        "0 16 * * 3": "Wednesdays 10 AM CST",
        "0 2 * * 4": "Wednesdays 8 PM CST",
        "0 9 * * 1": "Mondays 3 AM CST",
    }
    return patterns.get(cron, cron)


def parse_workflow_yaml(yaml_content: str) -> Dict[str, Any]:
    """Parse workflow YAML to extract schedule and inputs"""
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        return {"schedule": None, "inputs": []}

    result = {
        "schedule": None,
        "inputs": []
    }

    # YAML interprets 'on' as boolean True, so check both
    on_triggers = data.get("on") or data.get(True) or {}
    if isinstance(on_triggers, dict):
        # Extract schedule
        schedule = on_triggers.get("schedule", [])
        if schedule and len(schedule) > 0:
            cron = schedule[0].get("cron", "")
            result["schedule"] = cron_to_human(cron)

        # Extract workflow_dispatch inputs
        workflow_dispatch = on_triggers.get("workflow_dispatch", {})
        if workflow_dispatch and isinstance(workflow_dispatch, dict) and "inputs" in workflow_dispatch:
            for name, config in workflow_dispatch["inputs"].items():
                if isinstance(config, dict):
                    input_type = config.get("type", "string")
                    result["inputs"].append({
                        "name": name,
                        "description": config.get("description", ""),
                        "required": config.get("required", False),
                        "default": str(config.get("default", "")) if config.get("default") is not None else None,
                        "type": input_type,
                        "options": config.get("options", []) if input_type == "choice" else None
                    })

    return result


def calculate_duration(run: Dict[str, Any]) -> Optional[int]:
    """Calculate run duration in seconds"""
    if run.get("run_started_at") and run.get("updated_at"):
        try:
            from dateutil import parser
            start = parser.isoparse(run["run_started_at"])
            end = parser.isoparse(run["updated_at"])
            return int((end - start).total_seconds())
        except Exception:
            pass
    return None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=ActionsStatus)
async def get_actions_status():
    """Check if GitHub Actions is configured and accessible"""
    try:
        client = GitHubActionsClient()
        data = await client.list_workflows()
        return ActionsStatus(
            configured=True,
            owner=client.owner,
            repo=client.repo,
            workflow_count=data.get("total_count", 0)
        )
    except ValueError as e:
        return ActionsStatus(configured=False, error=str(e))
    except httpx.HTTPStatusError as e:
        return ActionsStatus(configured=False, error=f"GitHub API error: {e.response.status_code}")
    except Exception as e:
        return ActionsStatus(configured=False, error=f"Error: {str(e)}")


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows():
    """List all GitHub Actions workflows with parsed inputs and schedules"""
    try:
        client = GitHubActionsClient()
        data = await client.list_workflows()

        workflows = []
        for wf in data.get("workflows", []):
            # Fetch and parse YAML for each workflow
            try:
                yaml_content = await client.get_workflow_file(wf["path"])
                parsed = parse_workflow_yaml(yaml_content)
            except Exception:
                parsed = {"schedule": None, "inputs": []}

            workflows.append(Workflow(
                id=wf["id"],
                name=wf["name"],
                path=wf["path"],
                state=wf["state"],
                created_at=wf["created_at"],
                updated_at=wf["updated_at"],
                html_url=wf["html_url"],
                badge_url=wf["badge_url"],
                schedule=parsed["schedule"],
                inputs=[WorkflowInput(**inp) for inp in parsed["inputs"]]
            ))

        return WorkflowListResponse(workflows=workflows)

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@router.get("/workflows/{workflow_id}/runs", response_model=WorkflowRunListResponse)
async def list_workflow_runs(
    workflow_id: int,
    status: Optional[str] = Query(None, description="Filter: queued, in_progress, completed"),
    limit: int = Query(20, ge=1, le=100)
):
    """List runs for a specific workflow"""
    try:
        client = GitHubActionsClient()
        data = await client.list_workflow_runs(workflow_id, status, limit)

        runs = []
        for run in data.get("workflow_runs", []):
            runs.append(WorkflowRun(
                id=run["id"],
                name=run["name"],
                workflow_id=run["workflow_id"],
                status=run["status"],
                conclusion=run.get("conclusion"),
                event=run["event"],
                created_at=run["created_at"],
                updated_at=run["updated_at"],
                run_started_at=run.get("run_started_at"),
                html_url=run["html_url"],
                actor=run.get("actor", {}).get("login") if run.get("actor") else None,
                run_number=run["run_number"],
                duration_seconds=calculate_duration(run)
            ))

        return WorkflowRunListResponse(
            runs=runs,
            total_count=data.get("total_count", len(runs))
        )

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


@router.get("/runs", response_model=WorkflowRunListResponse)
async def list_all_runs(
    status: Optional[str] = Query(None, description="Filter: queued, in_progress, completed"),
    limit: int = Query(30, ge=1, le=100)
):
    """List all recent workflow runs across all workflows"""
    try:
        client = GitHubActionsClient()
        data = await client.list_workflow_runs(None, status, limit)

        runs = []
        for run in data.get("workflow_runs", []):
            runs.append(WorkflowRun(
                id=run["id"],
                name=run["name"],
                workflow_id=run["workflow_id"],
                status=run["status"],
                conclusion=run.get("conclusion"),
                event=run["event"],
                created_at=run["created_at"],
                updated_at=run["updated_at"],
                run_started_at=run.get("run_started_at"),
                html_url=run["html_url"],
                actor=run.get("actor", {}).get("login") if run.get("actor") else None,
                run_number=run["run_number"],
                duration_seconds=calculate_duration(run)
            ))

        return WorkflowRunListResponse(
            runs=runs,
            total_count=data.get("total_count", len(runs))
        )

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


@router.post("/workflows/{workflow_id}/dispatch", response_model=TriggerWorkflowResponse)
async def trigger_workflow(workflow_id: int, request: TriggerWorkflowRequest):
    """Trigger a workflow_dispatch event"""
    try:
        client = GitHubActionsClient()
        await client.trigger_workflow(workflow_id, request.ref, request.inputs)

        return TriggerWorkflowResponse(
            message="Workflow triggered successfully",
            workflow_id=workflow_id,
            ref=request.ref
        )

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            raise HTTPException(status_code=422, detail="Invalid inputs or workflow does not support workflow_dispatch")
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger workflow: {str(e)}")


@router.post("/runs/{run_id}/cancel", response_model=CancelRunResponse)
async def cancel_run(run_id: int):
    """Cancel an in-progress workflow run"""
    try:
        client = GitHubActionsClient()
        await client.cancel_run(run_id)

        return CancelRunResponse(
            message="Run cancellation requested",
            run_id=run_id
        )

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            raise HTTPException(status_code=409, detail="Run cannot be cancelled (already completed or not in progress)")
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel run: {str(e)}")


@router.put("/workflows/{workflow_id}/enable")
async def enable_workflow(workflow_id: int):
    """Enable a disabled workflow"""
    try:
        client = GitHubActionsClient()
        await client.enable_workflow(workflow_id)

        return {"message": "Workflow enabled", "workflow_id": workflow_id}

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable workflow: {str(e)}")


@router.put("/workflows/{workflow_id}/disable")
async def disable_workflow(workflow_id: int):
    """Disable a workflow (stops scheduled runs)"""
    try:
        client = GitHubActionsClient()
        await client.disable_workflow(workflow_id)

        return {"message": "Workflow disabled", "workflow_id": workflow_id}

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"GitHub API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable workflow: {str(e)}")
