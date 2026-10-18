"""Map repository paths to domains with ordered glob patterns. `{name}` in a glob captures one path part."""
import re
from pathlib import Path

from .config import ConfigError

UNMAPPED = "unmapped"
IGNORED = None


def glob_to_regex(glob: str) -> re.Pattern:
    """`**/` matches zero or more folders, `**` anything, `*` and `?` stay inside one folder, `{x}` captures one folder name."""
    out = []
    i = 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        elif glob[i] == "{":
            end = glob.index("}", i)
            out.append(f"(?P<{glob[i + 1:end]}>[^/]+)")
            i = end + 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


class DomainMap:
    def __init__(self, config: dict, repo_root: Path):
        self.ignore = [glob_to_regex(glob) for glob in config["ignore"]]
        self.rules = [(entry["glob"], glob_to_regex(entry["glob"]), entry["domain"], entry.get("require_capability", False))
                      for entry in config["domains"]]
        self.capabilities_dir = Path(repo_root) / config["capabilities_dir"] if "capabilities_dir" in config else None
        self.unknown: dict[str, str] = {}
        self._check_static_domains()

    def _check_static_domains(self) -> None:
        if self.capabilities_dir is None:
            return
        for glob, _, domain, _ in self.rules:
            if "{" not in domain and not self._exists(domain):
                raise ConfigError(f"pattern '{glob}' names the domain '{domain}', which has no folder in {self.capabilities_dir}")

    def _exists(self, domain: str) -> bool:
        return (self.capabilities_dir / domain).is_dir()

    def domain_of(self, path: str) -> str | None:
        """The domain of a path, `unmapped`, or None when the path is ignored."""
        path = path.replace("\\", "/")
        if any(regex.match(path) for regex in self.ignore):
            return IGNORED
        for glob, regex, template, require_capability in self.rules:
            match = regex.match(path)
            if not match:
                continue
            domain = template.format(**match.groupdict())
            if self.capabilities_dir is None or self._exists(domain):
                return domain
            if require_capability:
                continue
            # A captured domain can name a capability that was removed later; history keeps it, the report flags it.
            self.unknown.setdefault(domain, glob)
            return domain
        return UNMAPPED
