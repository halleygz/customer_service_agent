import json
import os
import urllib.error
import urllib.request
from uuid import UUID
from typing import Any, Dict

from app.services.logger import get_logger


logger = get_logger("linear")


class LinearService:
	def __init__(self) -> None:
		self.api_key = os.getenv("LINEAR_API_KEY", "")
		self.team_ref = os.getenv("LINEAR_TEAM_ID", "")
		self.endpoint = os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql")
		self._resolved_team_id: str | None = None

	def _is_configured(self) -> bool:
		return bool(self.api_key and self.team_ref)

	@staticmethod
	def _is_uuid(value: str) -> bool:
		try:
			UUID(value)
			return True
		except Exception:
			return False

	def _execute_graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
		payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
		request = urllib.request.Request(
			self.endpoint,
			data=payload,
			headers={
				"Content-Type": "application/json",
				"Authorization": self.api_key,
			},
			method="POST",
		)

		try:
			with urllib.request.urlopen(request, timeout=15) as response:
				body = response.read().decode("utf-8")
				parsed = json.loads(body)
				if parsed.get("errors"):
					return {
						"success": False,
						"errors": parsed["errors"],
					}
				return {"success": True, "data": parsed.get("data", {})}
		except urllib.error.HTTPError as exc:
			return {
				"success": False,
				"errors": [{"message": f"Linear HTTP error {exc.code}: {exc.reason}"}],
			}
		except Exception as exc:
			return {
				"success": False,
				"errors": [{"message": f"Linear request failed: {exc}"}],
			}

	def _resolve_team_id(self) -> Dict[str, Any]:
		if self._resolved_team_id:
			return {"success": True, "team_id": self._resolved_team_id}

		if self._is_uuid(self.team_ref):
			self._resolved_team_id = self.team_ref
			return {"success": True, "team_id": self._resolved_team_id}

		query = """
		query TeamsQuery {
		  teams {
			nodes {
			  id
			  key
			  name
			}
		  }
		}
		"""
		result = self._execute_graphql(query, {})
		if not result.get("success"):
			return result

		nodes = ((result.get("data") or {}).get("teams") or {}).get("nodes") or []
		for node in nodes:
			if str(node.get("key", "")).lower() == self.team_ref.lower():
				self._resolved_team_id = node.get("id")
				return {"success": True, "team_id": self._resolved_team_id, "team": node}

		return {
			"success": False,
			"errors": [
				{
					"message": (
						"LINEAR_TEAM_ID is not a UUID and could not be matched to a team key. "
						f"Provided value: {self.team_ref}"
					)
				}
			],
		}

	def _create_issue(
		self,
		title: str,
		description: str,
		priority: int = 2,
	) -> Dict[str, Any]:
		if not self._is_configured():
			logger.warning("linear_not_configured returning_mock_ticket")
			return {
				"success": True,
				"provider": "mock",
				"ticket": {
					"id": "mock-ticket",
					"identifier": "MOCK-1",
					"title": title,
					"url": "https://linear.app/mock/issue/MOCK-1",
				},
				"message": "Linear is not configured. Returned a mock ticket.",
			}

		team_result = self._resolve_team_id()
		if not team_result.get("success"):
			logger.error("linear_team_resolution_failed errors=%s", team_result.get("errors"))
			return {
				"success": False,
				"errors": team_result.get("errors", []),
			}

		mutation = """
		mutation CreateIssue($input: IssueCreateInput!) {
		  issueCreate(input: $input) {
			success
			issue {
			  id
			  identifier
			  title
			  url
			}
		  }
		}
		"""

		variables = {
			"input": {
				"teamId": team_result["team_id"],
				"title": title,
				"description": description,
				"priority": priority,
			}
		}

		result = self._execute_graphql(mutation, variables)
		if not result["success"]:
			logger.error("linear_issue_create_failed errors=%s", result.get("errors"))
			return result

		issue_payload = (result.get("data", {}).get("issueCreate", {}))
		if not issue_payload or not issue_payload.get("success"):
			return {
				"success": False,
				"errors": [{"message": "Linear issueCreate did not return success."}],
			}

		logger.info(
			"linear_issue_created identifier=%s",
			(issue_payload.get("issue") or {}).get("identifier"),
		)
		return {
			"success": True,
			"provider": "linear",
			"ticket": issue_payload.get("issue", {}),
		}

	def verify_connection(self) -> Dict[str, Any]:
		if not self._is_configured():
			return {
				"success": False,
				"configured": False,
				"message": "LINEAR_API_KEY or LINEAR_TEAM_ID is missing.",
			}

		query = """
		query ViewerQuery {
		  viewer {
			id
			name
			email
		  }
		}
		"""
		result = self._execute_graphql(query, {})
		if not result.get("success"):
			return {
				"success": False,
				"configured": True,
				"message": "Linear API call failed.",
				"errors": result.get("errors", []),
			}

		team_result = self._resolve_team_id()
		if not team_result.get("success"):
			return {
				"success": False,
				"configured": True,
				"message": "Linear authenticated, but team configuration is invalid.",
				"errors": team_result.get("errors", []),
			}

		viewer = (result.get("data") or {}).get("viewer")
		logger.info("linear_connection_verified viewer=%s", viewer.get("email") if viewer else None)
		return {
			"success": True,
			"configured": True,
			"viewer": viewer,
			"team_id": team_result.get("team_id"),
			"team": team_result.get("team"),
		}

	def createFeatureRequestTicket(
		self,
		customer_id: int,
		customer_tier: str,
		summary: str,
		details: str,
	) -> Dict[str, Any]:
		title = f"Feature Request | Customer {customer_id} | {summary[:72]}"
		description = (
			"### Request Type\nFeature Request\n\n"
			f"### Customer ID\n{customer_id}\n\n"
			f"### Customer Tier\n{customer_tier or 'Unknown'}\n\n"
			f"### Summary\n{summary}\n\n"
			f"### Details\n{details}\n"
		)
		return self._create_issue(title=title, description=description, priority=3)

	def createBugReportTicket(
		self,
		customer_id: int,
		customer_tier: str,
		summary: str,
		reproduction_steps: str,
	) -> Dict[str, Any]:
		title = f"Bug Report | Customer {customer_id} | {summary[:72]}"
		description = (
			"### Request Type\nBug Report\n\n"
			f"### Customer ID\n{customer_id}\n\n"
			f"### Customer Tier\n{customer_tier or 'Unknown'}\n\n"
			f"### Summary\n{summary}\n\n"
			f"### Reproduction / Details\n{reproduction_steps}\n"
		)
		return self._create_issue(title=title, description=description, priority=1)