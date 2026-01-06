"""
Jobs API Routes
Endpoints for job queue management and monitoring.
"""
import sys
import os
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter()


class JobStatus(BaseModel):
    """Job status model"""
    id: str
    status: str
    config: Optional[dict]
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[dict]
    error: Optional[str]


class JobListResponse(BaseModel):
    """Response for job list endpoint"""
    jobs: List[JobStatus]
    total: int


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = Query(default=None, description="Filter by status: pending, running, completed, failed"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    List all jobs with optional filtering.
    """
    # #region agent log
    import json; open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:list_jobs:entry","message":"list_jobs called","data":{"status":status,"limit":limit},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"E"})+'\n')
    # #endregion
    try:
        # #region agent log
        open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:import","message":"Attempting import supabase_storage","data":{},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"C"})+'\n')
        # #endregion
        from supabase_storage import get_supabase_client
        # #region agent log
        open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:import_success","message":"Import succeeded","data":{},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"C"})+'\n')
        # #endregion
        supabase = get_supabase_client()
        # #region agent log
        open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:supabase_client","message":"get_supabase_client result","data":{"is_none":supabase is None,"type":str(type(supabase))},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"A"})+'\n')
        # #endregion
        
        # Check if supabase is None
        if supabase is None:
            # #region agent log
            open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:supabase_none","message":"Supabase client is None - returning empty","data":{},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"A"})+'\n')
            # #endregion
            return JobListResponse(jobs=[], total=0)
        
        # #region agent log
        open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:before_query","message":"About to query job_queue","data":{"has_client":hasattr(supabase,'client')},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"B"})+'\n')
        # #endregion
        
        # Get total count
        count_query = supabase.table("job_queue").select("id", count="exact")
        if status:
            count_query = count_query.eq("status", status)
        count_result = count_query.execute()
        total = count_result.count if count_result.count else 0
        
        # Get jobs
        query = supabase.table("job_queue").select("*").order("started_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        # #region agent log
        open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:query_success","message":"Query completed","data":{"total":total,"result_count":len(result.data) if result.data else 0},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"B"})+'\n')
        # #endregion
        
        return JobListResponse(
            jobs=result.data if result.data else [],
            total=total
        )
        
    except Exception as e:
        # #region agent log
        import traceback; open('/Users/kayajones/youdle/.cursor/debug.log','a').write(json.dumps({"location":"jobs.py:exception","message":"Exception in list_jobs","data":{"error":str(e),"type":str(type(e).__name__),"traceback":traceback.format_exc()},"timestamp":__import__('time').time()*1000,"sessionId":"debug-session","hypothesisId":"D"})+'\n')
        # #endregion
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    """
    Get status of a specific job.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        result = supabase.table("job_queue").select("*").eq("id", job_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.get("/{job_id}/posts")
async def get_job_posts(job_id: str):
    """
    Get all blog posts generated by a specific job.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        result = supabase.table("blog_posts").select("*").eq("job_id", job_id).execute()
        
        return {
            "job_id": job_id,
            "posts": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job posts: {str(e)}")


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or running job.
    Note: This only updates the status - it doesn't actually stop a running process.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        # Check current status
        job = supabase.table("job_queue").select("status").eq("id", job_id).single().execute()
        
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.data["status"] in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job.data['status']}")
        
        # Update status to cancelled
        result = supabase.table("job_queue").update({
            "status": "cancelled",
            "completed_at": datetime.utcnow().isoformat(),
            "error": "Cancelled by user"
        }).eq("id", job_id).execute()
        
        return {"message": "Job cancelled", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/{job_id}/logs")
async def get_job_logs(job_id: str):
    """
    Get logs for a specific job.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        # Get job to check logs in result
        result = supabase.table("job_queue").select("*").eq("id", job_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = result.data
        logs = []
        
        # Extract logs from result if available
        if job.get("result") and job["result"].get("logs"):
            logs = job["result"]["logs"]
        
        return {
            "job_id": job_id,
            "status": job["status"],
            "logs": logs,
            "error": job.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job logs: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_jobs(
    days_old: int = Query(default=30, ge=1, le=365, description="Delete jobs older than N days")
):
    """
    Clean up old completed/failed jobs.
    """
    try:
        from supabase_storage import get_supabase_client
        from datetime import timedelta
        supabase = get_supabase_client()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
        
        # Delete old completed and failed jobs
        result = supabase.table("job_queue").delete().lt(
            "completed_at", cutoff_date
        ).in_("status", ["completed", "failed", "cancelled"]).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        return {
            "message": f"Cleaned up {deleted_count} old jobs",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup jobs: {str(e)}")


