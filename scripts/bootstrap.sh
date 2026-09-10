#!/usr/bin/env bash
set -euo pipefail

profile="development"
source_path=""
git_ref="stable"
reconfigure_marketplace=false
dry_run=false
skip_external=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      profile="${2:?--profile requires a value}"
      shift 2
      ;;
    --source)
      source_path="${2:?--source requires a value}"
      shift 2
      ;;
    --ref)
      git_ref="${2:?--ref requires a value}"
      shift 2
      ;;
    --reconfigure-marketplace)
      reconfigure_marketplace=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --skip-external)
      skip_external=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$profile" in
  minimal|development|full) ;;
  *)
    echo "Unknown profile: $profile" >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd "$script_dir/.." && pwd)"
source_path="${source_path:-$repository_root}"
profile_path="$repository_root/profiles/$profile.json"

python_command=""
if command -v python3 >/dev/null 2>&1; then
  python_command="python3"
elif command -v python >/dev/null 2>&1; then
  python_command="python"
fi

if [[ -n "$python_command" ]]; then
  "$python_command" "$script_dir/verify.py"
else
  echo "Python is required to verify the marketplace." >&2
  exit 1
fi

marketplace_name="$($python_command -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["marketplace"])' "$profile_path" | tr -d '\r')"
plugins=()
while IFS= read -r plugin; do
  [[ -n "$plugin" ]] && plugins+=("$plugin")
done < <("$python_command" -c 'import json,sys; print(*json.load(open(sys.argv[1], encoding="utf-8"))["plugins"], sep="\n")' "$profile_path" | tr -d '\r')
external_plugins=()
while IFS= read -r plugin; do
  [[ -n "$plugin" ]] && external_plugins+=("$plugin")
done < <("$python_command" -c 'import json,sys; sys.stdout.write("\n".join(item["id"] for item in json.load(open(sys.argv[1], encoding="utf-8"))["externalPlugins"]))' "$profile_path" | tr -d '\r')

run_codex() {
  if [[ "$dry_run" == true ]]; then
    printf '[dry-run] codex'
    printf ' %q' "$@"
    printf '\n'
  else
    codex "$@"
  fi
}

if [[ "$dry_run" == false ]]; then
  for command_name in git codex; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      echo "$command_name is required and was not found on PATH." >&2
      exit 1
    fi
  done
  for plugin in "${plugins[@]}"; do
    if [[ "$plugin" == "developer-mcps" ]] && ! command -v node >/dev/null 2>&1; then
      echo "Node.js is required by the developer-mcps profile selection." >&2
      exit 1
    fi
  done
fi

marketplace_args=(plugin marketplace add "$source_path" --json)
if [[ ! -d "$source_path" ]] && [[ -n "$git_ref" ]]; then
  marketplace_args+=(--ref "$git_ref")
fi
if [[ "$reconfigure_marketplace" == true ]]; then
  run_codex plugin marketplace remove "$marketplace_name"
fi
if [[ "$dry_run" == true ]]; then
  run_codex "${marketplace_args[@]}"
else
  if ! add_output="$(codex "${marketplace_args[@]}")"; then
    echo "Marketplace source conflicts with an existing registration or could not be added: $source_path" >&2
    exit 1
  fi
  echo "$add_output"
  already_added="$(printf '%s' "$add_output" | "$python_command" -c 'import json,sys; print("true" if json.load(sys.stdin).get("alreadyAdded") else "false")' | tr -d '\r')"
  if [[ "$already_added" == true ]] && [[ ! -d "$source_path" ]]; then
    run_codex plugin marketplace upgrade "$marketplace_name"
  fi
fi

for plugin in "${plugins[@]}"; do
  run_codex plugin add "$plugin@$marketplace_name"
done

if [[ "$skip_external" == false ]]; then
  for plugin in "${external_plugins[@]}"; do
    if ! run_codex plugin add "$plugin"; then
      echo "Optional external plugin unavailable: $plugin" >&2
    fi
  done
fi

if [[ "$dry_run" == true ]]; then
  echo "Dry run complete for profile '$profile'."
else
  installed_json="$(codex plugin list --json)"
  if ! printf '%s' "$installed_json" | "$python_command" -c 'import json,sys; market=sys.argv[1]; expected=sys.argv[2:]; data=json.load(sys.stdin); ids={item["pluginId"] for item in data["installed"]}; missing=[name for name in expected if f"{name}@{market}" not in ids]; print(", ".join(missing)); raise SystemExit(bool(missing))' "$marketplace_name" "${plugins[@]}"; then
    echo "Health check failed; one or more marketplace plugins are missing." >&2
    exit 1
  fi
  for plugin in "${plugins[@]}"; do
    if [[ "$plugin" == "developer-mcps" ]]; then
      if ! codex mcp list --json | "$python_command" -c 'import json,sys; data=json.load(sys.stdin); raise SystemExit(0 if any(item["name"] == "marketplaceStatus" and item["enabled"] for item in data) else 1)'; then
        echo "Health check failed; marketplaceStatus MCP is not enabled." >&2
        exit 1
      fi
      developer_root="$(printf '%s' "$installed_json" | "$python_command" -c 'import json,sys; plugin=sys.argv[1]; data=json.load(sys.stdin); match=next((item for item in data["installed"] if item["pluginId"] == plugin), None); print(match.get("source", {}).get("path", "") if match else "")' "developer-mcps@$marketplace_name" | tr -d '\r')"
      if [[ -z "$developer_root" ]]; then
        echo "Health check failed; developer-mcps has no local installed source path." >&2
        exit 1
      fi
      probe_output="$(printf '%s\n%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"marketplace_status","arguments":{}}}' | node "$developer_root/scripts/marketplace_status_mcp.mjs")"
      if ! printf '%s' "$probe_output" | "$python_command" -c 'import json,sys; responses=[json.loads(line) for line in sys.stdin if line.strip()]; match=next((item for item in responses if item.get("id") == 2), None); raise SystemExit(0 if match and match.get("result", {}).get("structuredContent", {}).get("healthy") else 1)'; then
        echo "Health check failed; marketplaceStatus MCP returned an unhealthy result." >&2
        exit 1
      fi
    fi
  done
  if [[ "$skip_external" == false ]] && [[ ${#external_plugins[@]} -gt 0 ]]; then
    echo "Optional external plugins may require per-machine authentication on first use."
  fi
  echo "Health check passed: ${#plugins[@]} marketplace plugins installed."
  echo "Profile '$profile' installed. Start a new Codex task to load new skills and MCP tools."
fi
