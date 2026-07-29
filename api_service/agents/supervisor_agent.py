"""
Supervisor Agent — Orchestrator
================================
The entry point for all investigation requests.

Flow:
  1. Receives natural language query from user
  2. Calls FetcherAgent → extracts scope
  3. Calls InvestigationEngine.run(scope) → gets SQL analytics data
  4. Calls RunnerAgent → generates AI report
  5. Returns structured response
"""

from agents.fetcher_agent import FetcherAgent
from agents.runner_agent import RunnerAgent
from analytics_engine import InvestigationEngine

# Shared instances (initialized once)
_fetcher = None
_runner = None
_engine = None


def get_fetcher() -> FetcherAgent:
    global _fetcher
    if _fetcher is None:
        _fetcher = FetcherAgent()
    return _fetcher


def get_runner() -> RunnerAgent:
    global _runner
    if _runner is None:
        _runner = RunnerAgent()
    return _runner


def get_engine() -> InvestigationEngine:
    global _engine
    if _engine is None:
        _engine = InvestigationEngine()
    return _engine


class SupervisorAgent:
    """
    Orchestrates the full investigation pipeline:
    Query → Scope Extraction → SQL Analytics → AI Report
    """

    def __init__(self):
        self.fetcher = get_fetcher()
        self.runner = get_runner()
        self.engine = get_engine()

    def investigate(self, user_query: str) -> dict:
        """
        Full investigation pipeline.

        Args:
            user_query: Natural language question e.g.
                        "Why is Delhivery performing poorly in West India?"

        Returns:
            {
                "query": original user question,
                "scope": extracted parameters,
                "analytics": raw SQL data,
                "report": AI-generated investigation report (markdown)
            }
        """

        # Step 1: Extract scope from the query
        scope = self.fetcher.extract_scope(user_query)

        # Step 2: Run SQL analytics with that scope
        analytics_data = self.engine.run(scope=scope)

        # Step 3: Generate AI report from analytics data
        report = self.runner.generate_report(
            user_query=user_query,
            scope=scope,
            analytics_data=analytics_data
        )

        return {
            "query": user_query,
            "scope": scope,
            "analytics": analytics_data,
            "report": report
        }
