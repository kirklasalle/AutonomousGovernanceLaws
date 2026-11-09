# notify_stub.ps1 - Optional notifier stub
param(
    [string]$method = "none",
    [string]$subject = "Audit Alert",
    [string]$body = ""
)
# Placeholder: implement methods: smtp, openclaw-message, webhook
switch($method){
    'smtp' { Write-Output "SMTP notifier not configured." }
    'openclaw-message' { Write-Output "OpenClaw message notifier not implemented in script; use 'message' tool from agent." }
    default { Write-Output "No notifier selected. Subject: $subject" }
}
