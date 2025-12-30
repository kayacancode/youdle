# learning_memory.py
# Cross-session learning memory for the blog generation agent

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from supabase_storage import get_supabase_client, SupabaseStorage


class LearningMemory:
    """
    Cross-session learning memory for storing and retrieving
    insights, patterns, and improvement data.
    """
    
    def __init__(self, supabase_client: Optional[SupabaseStorage] = None):
        """
        Initialize the learning memory.
        
        Args:
            supabase_client: Optional Supabase client
        """
        self.client = supabase_client or get_supabase_client()
        self._local_memory: Dict[str, Any] = {
            "insights": [],
            "metrics": [],
            "patterns": []
        }
    
    def store_insight(
        self,
        insight_type: str,
        description: str,
        category: str = "",
        frequency: int = 1
    ) -> Dict[str, Any]:
        """
        Store a learning insight.
        
        Args:
            insight_type: Type of insight (common_mistake, improvement_pattern, etc.)
            description: Description of the insight
            category: Related category
            frequency: How often this pattern occurs
            
        Returns:
            Result dictionary
        """
        insight = {
            "insight_type": insight_type,
            "description": description,
            "category": category,
            "frequency": frequency,
            "created_at": datetime.now().isoformat()
        }
        
        if self.client:
            return self.client.save_learning_insight(
                insight_type=insight_type,
                description=description,
                category=category,
                frequency=frequency
            )
        else:
            self._local_memory["insights"].append(insight)
            return {"success": True, "cached": True}
    
    def get_insights(
        self,
        insight_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve learning insights.
        
        Args:
            insight_type: Filter by type
            category: Filter by category
            limit: Maximum number of insights
            
        Returns:
            List of insights
        """
        if self.client:
            return self.client.get_learning_insights(
                insight_type=insight_type,
                category=category,
                limit=limit
            )
        else:
            insights = self._local_memory["insights"]
            if insight_type:
                insights = [i for i in insights if i.get("insight_type") == insight_type]
            if category:
                insights = [i for i in insights if i.get("category") == category]
            return insights[:limit]
    
    def store_session_metrics(
        self,
        category: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store metrics from a generation session.
        
        Args:
            category: 'shoppers' or 'recall'
            metrics: Session metrics (posts_generated, approval_rate, etc.)
            
        Returns:
            Result dictionary
        """
        metric_record = {
            "category": category,
            "metrics": metrics,
            "created_at": datetime.now().isoformat()
        }
        
        self._local_memory["metrics"].append(metric_record)
        
        # Store key metrics as insights if notable
        if metrics.get("approval_rate", 0) >= 90:
            self.store_insight(
                insight_type="improvement_pattern",
                description=f"High approval rate ({metrics.get('approval_rate')}%) achieved",
                category=category
            )
        elif metrics.get("approval_rate", 100) < 50:
            self.store_insight(
                insight_type="problem",
                description=f"Low approval rate ({metrics.get('approval_rate')}%) - needs attention",
                category=category
            )
        
        return {"success": True}
    
    def get_performance_summary(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of performance across sessions.
        
        Args:
            category: Filter by category
            
        Returns:
            Performance summary
        """
        metrics = self._local_memory["metrics"]
        
        if category:
            metrics = [m for m in metrics if m.get("category") == category]
        
        if not metrics:
            return {
                "sessions": 0,
                "avg_approval_rate": 0,
                "trend": "no_data"
            }
        
        # Calculate averages
        total_sessions = len(metrics)
        approval_rates = [
            m.get("metrics", {}).get("approval_rate", 0) 
            for m in metrics
        ]
        
        avg_approval = sum(approval_rates) / len(approval_rates) if approval_rates else 0
        
        # Calculate trend
        if len(approval_rates) >= 3:
            recent = approval_rates[-3:]
            older = approval_rates[:-3] if len(approval_rates) > 3 else approval_rates[:1]
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older) if older else 0
            
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "sessions": total_sessions,
            "avg_approval_rate": round(avg_approval, 2),
            "trend": trend,
            "recent_metrics": metrics[-5:] if metrics else []
        }
    
    def get_common_mistakes(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[str]:
        """
        Get common mistakes to avoid.
        
        Args:
            category: Filter by category
            limit: Maximum number of mistakes
            
        Returns:
            List of common mistake descriptions
        """
        insights = self.get_insights(
            insight_type="common_mistake",
            category=category,
            limit=limit
        )
        
        return [i.get("description", "") for i in insights]
    
    def get_successful_patterns(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[str]:
        """
        Get successful patterns to follow.
        
        Args:
            category: Filter by category
            limit: Maximum number of patterns
            
        Returns:
            List of successful pattern descriptions
        """
        insights = self.get_insights(
            insight_type="improvement_pattern",
            category=category,
            limit=limit
        )
        
        return [i.get("description", "") for i in insights]
    
    def load_session_memory(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load memory at the start of a generation session.
        
        Args:
            category: Filter by category
            
        Returns:
            Memory data for the session
        """
        return {
            "common_mistakes": self.get_common_mistakes(category),
            "successful_patterns": self.get_successful_patterns(category),
            "performance_summary": self.get_performance_summary(category),
            "recent_insights": self.get_insights(category=category, limit=5)
        }
    
    def save_session_memory(
        self,
        category: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save memory at the end of a generation session.
        
        Args:
            category: Category of the session
            session_data: Data from the session
            
        Returns:
            Result dictionary
        """
        # Store session metrics
        metrics = {
            "posts_generated": session_data.get("posts_generated", 0),
            "posts_approved": session_data.get("posts_approved", 0),
            "approval_rate": session_data.get("approval_rate", 0),
            "avg_reflection_attempts": session_data.get("avg_attempts", 0)
        }
        
        self.store_session_metrics(category, metrics)
        
        # Store any new insights
        for insight in session_data.get("new_insights", []):
            self.store_insight(
                insight_type=insight.get("type", "general"),
                description=insight.get("description", ""),
                category=category
            )
        
        return {"success": True}


# Convenience function for loading memory
def load_learning_memory(category: str = "shoppers") -> Dict[str, Any]:
    """
    Load learning memory for a generation session.
    
    Args:
        category: 'shoppers' or 'recall'
        
    Returns:
        Memory data
    """
    memory = LearningMemory()
    return memory.load_session_memory(category)


# For testing
if __name__ == "__main__":
    memory = LearningMemory()
    
    print("Testing learning memory...")
    
    # Store some insights
    memory.store_insight(
        insight_type="common_mistake",
        description="Often forgets the community link at the end",
        category="shoppers"
    )
    
    memory.store_insight(
        insight_type="improvement_pattern",
        description="Using bullet points improves readability",
        category="shoppers"
    )
    
    # Store session metrics
    memory.store_session_metrics(
        category="shoppers",
        metrics={
            "posts_generated": 6,
            "posts_approved": 5,
            "approval_rate": 83.3
        }
    )
    
    # Load session memory
    session_memory = memory.load_session_memory("shoppers")
    print(f"Common mistakes: {session_memory['common_mistakes']}")
    print(f"Successful patterns: {session_memory['successful_patterns']}")
    print(f"Performance: {session_memory['performance_summary']}")



