"""Gate validation logic for PreToolUse hooks."""

from pathlib import Path
from typing import Any


def validate_tool_use(payload: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate whether a tool use should be allowed.

    Args:
        payload: JSON payload from Claude containing tool use information

    Returns:
        Tuple of (allowed: bool, reason: str)
        - (True, "") if allowed
        - (False, reason) if denied
    """
    tool_name = payload.get("tool_name", "")

    # Rule 1: Deny Bash tool
    if tool_name == "Bash":
        return False, "Bash tool is denied by security policy"

    # Rule 2: Check for sensitive paths in any write operation
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target_path = payload.get("target_path", "")
        if target_path:
            path = Path(target_path)
            path_str = str(path)

            # Check sensitive paths
            sensitive_patterns = [".env", "secrets/", ".git/"]
            for pattern in sensitive_patterns:
                if pattern in path_str or path_str.startswith(pattern):
                    return False, f"Access to sensitive path denied: {pattern}"

            # Check if write is outside repo (assuming repo root is cwd or parent dirs)
            # For now, we'll check if path tries to go outside with ../ patterns
            try:
                resolved = path.resolve()
                if ".." in str(path):
                    # Check if path tries to escape
                    cwd = Path.cwd()
                    if not str(resolved).startswith(str(cwd)):
                        return False, f"Write outside repository denied: {path}"
            except (ValueError, OSError):
                # Invalid path
                return False, f"Invalid path: {path}"

    # Rule 3: Check URL domains if present
    if "url" in payload:
        url = payload["url"]
        # Extract domain from URL
        import urllib.parse

        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()

            # Check for invalid URL (no domain)
            if not domain:
                return False, f"Invalid URL: {url}"

            # Get allow/deny lists from payload if provided
            allow_list = payload.get("allowed_domains", [])
            deny_list = payload.get("denied_domains", [])

            # Check deny list first (deny wins)
            for denied in deny_list:
                if denied.startswith("*."):
                    # Wildcard domain
                    suffix = denied[2:]
                    if domain.endswith(suffix) or domain == suffix[1:]:
                        return False, f"Domain {domain} matches denied pattern {denied}"
                elif domain == denied:
                    return False, f"Domain {domain} is explicitly denied"

            # If allow list is not empty, domain must be in it
            if allow_list:
                allowed = False
                for allow in allow_list:
                    if allow.startswith("*."):
                        # Wildcard domain
                        suffix = allow[2:]
                        if domain.endswith(suffix) or domain == suffix[1:]:
                            allowed = True
                            break
                    elif domain == allow:
                        allowed = True
                        break

                if not allowed:
                    return False, f"Domain {domain} not in allow list"
        except Exception as e:
            return False, f"Invalid URL: {e}"

    # Default: allow
    return True, ""
