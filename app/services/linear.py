import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict


class LinearService:
	def __init__(self) -> None:
		self.api_key = os.getenv("LINEAR_API_KEY", "")
		self.team_id = os.getenv("LINEAR_TEAM_ID", "")
		self.endpoint = os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql")

	def _is_configured(self) -> bool:
		return bool(self.api_key and self.team_id)

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
				"errors": [
					{
						"message": f"Linear HTTP error {exc.code}: {exc.reason}",
					}
				],
			}
		except Exception as exc:
			return {
				"success": False,
				"errors": [{"message": f"Linear request failed: {exc}"}],
			}

	def _create_issue(
		self,
		title: str,
		description: str,
		priority: int = 2,
	) -> Dict[str, Any]:
		if not self._is_configured():
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
				"teamId": self.team_id,
				"title": title,
				"description": description,
				"priority": priority,
			}
		}

		result = self._execute_graphql(mutation, variables)
		if not result["success"]:
			return result

		issue_payload = (
			result.get("data", {})
			.get("issueCreate", {})
		)
		if not issue_payload or not issue_payload.get("success"):
			return {
				"success": False,
				"errors": [{"message": "Linear issueCreate did not return success."}],
			}

		return {
			"success": True,
			"provider": "linear",
			"ticket": issue_payload.get("issue", {}),
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