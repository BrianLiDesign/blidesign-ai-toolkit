[CmdletBinding()]
param(
    [ValidateSet('minimal', 'development', 'full')]
    [string]$Profile = 'development',
    [string]$Source,
    [string]$Ref = 'stable',
    [switch]$ReconfigureMarketplace,
    [switch]$SkipExternal,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
if (-not $Source) {
    $Source = $repositoryRoot
}

$profilePath = Join-Path $repositoryRoot "profiles\$Profile.json"
if (-not (Test-Path -LiteralPath $profilePath)) {
    throw "Unknown profile: $Profile"
}
$configuration = Get-Content -Raw -LiteralPath $profilePath | ConvertFrom-Json
$marketplaceName = $configuration.marketplace

function Write-CodexCommand {
    param([string[]]$Arguments)
    Write-Output ("codex " + ($Arguments -join ' '))
}

function Invoke-CodexCommand {
    param(
        [string[]]$Arguments,
        [switch]$Optional
    )

    if ($DryRun) {
        Write-Output -NoEnumerate '[dry-run] '
        Write-CodexCommand -Arguments $Arguments
        return
    }

    & codex @Arguments
    if ($LASTEXITCODE -ne 0) {
        if ($Optional) {
            Write-Warning "Optional command failed: codex $($Arguments -join ' ')"
            return
        }
        throw "Command failed: codex $($Arguments -join ' ')"
    }
}

if (-not $DryRun) {
    foreach ($command in @('git', 'codex')) {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
            throw "$command is required and was not found on PATH."
        }
    }
    if ($configuration.plugins -contains 'developer-mcps' -and -not (Get-Command node -ErrorAction SilentlyContinue)) {
        throw 'Node.js is required by the developer-mcps profile selection.'
    }
}

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
if ($python) {
    & $python.Source (Join-Path $PSScriptRoot 'verify.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'Repository verification failed.'
    }
} elseif (-not $DryRun) {
    throw 'Python is required to verify the marketplace.'
}

$marketplaceArguments = @('plugin', 'marketplace', 'add', $Source, '--json')
$localSource = Test-Path -LiteralPath $Source
if (-not $localSource -and $Ref) {
    $marketplaceArguments += @('--ref', $Ref)
}
if ($ReconfigureMarketplace) {
    Invoke-CodexCommand -Arguments @('plugin', 'marketplace', 'remove', $marketplaceName)
}
if ($DryRun) {
    Invoke-CodexCommand -Arguments $marketplaceArguments
} else {
    $addOutput = & codex @marketplaceArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Marketplace source conflicts with an existing registration or could not be added: $Source"
    }
    $addResult = $addOutput | ConvertFrom-Json
    Write-Output $addOutput
    if ($addResult.alreadyAdded -and -not $localSource) {
        Invoke-CodexCommand -Arguments @('plugin', 'marketplace', 'upgrade', $marketplaceName)
    }
}

foreach ($plugin in $configuration.plugins) {
    Invoke-CodexCommand -Arguments @('plugin', 'add', "$plugin@$marketplaceName")
}

if (-not $SkipExternal) {
    foreach ($external in $configuration.externalPlugins) {
        Invoke-CodexCommand -Arguments @('plugin', 'add', $external.id) -Optional:$external.optional
    }
}

if ($DryRun) {
    Write-Output "Dry run complete for profile '$Profile'."
} else {
    $installedData = & codex plugin list --json | ConvertFrom-Json
    $installedIds = @($installedData.installed | ForEach-Object { $_.pluginId })
    $missing = @($configuration.plugins | Where-Object { "$($_)@$marketplaceName" -notin $installedIds })
    if ($missing.Count -gt 0) {
        throw "Health check failed; missing plugins: $($missing -join ', ')"
    }
    if ($configuration.plugins -contains 'developer-mcps') {
        $mcpServers = @(& codex mcp list --json | ConvertFrom-Json)
        $marketplaceStatus = $mcpServers | Where-Object { $_.name -eq 'marketplaceStatus' -and $_.enabled }
        if (-not $marketplaceStatus) {
            throw 'Health check failed; marketplaceStatus MCP is not enabled.'
        }
        $developerPlugin = $installedData.installed | Where-Object { $_.pluginId -eq "developer-mcps@$marketplaceName" } | Select-Object -First 1
        $pluginRoot = $developerPlugin.source.path
        if (-not $pluginRoot) {
            throw 'Health check failed; developer-mcps has no local installed source path.'
        }
        $serverPath = Join-Path $pluginRoot 'scripts\marketplace_status_mcp.mjs'
        $probeRequests = @(
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"marketplace_status","arguments":{}}}'
        ) -join "`n"
        $probeOutput = ($probeRequests + "`n") | & node $serverPath
        if ($LASTEXITCODE -ne 0) {
            throw 'Health check failed; marketplaceStatus MCP process did not start.'
        }
        $probeResponses = @($probeOutput | ForEach-Object { $_ | ConvertFrom-Json })
        $statusResponse = $probeResponses | Where-Object { $_.id -eq 2 } | Select-Object -First 1
        if (-not $statusResponse.result.structuredContent.healthy) {
            throw 'Health check failed; marketplaceStatus MCP returned an unhealthy result.'
        }
    }
    if (-not $SkipExternal -and $configuration.externalPlugins.Count -gt 0) {
        Write-Output 'Optional external plugins may require per-machine authentication on first use.'
    }
    Write-Output "Health check passed: $($configuration.plugins.Count) marketplace plugins installed."
    Write-Output "Profile '$Profile' installed. Start a new Codex task to load new skills and MCP tools."
}
