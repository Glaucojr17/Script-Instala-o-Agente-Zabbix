# Configurações
$zabbixServer = "10.46.0.114"
$agentHostname = $env:COMPUTERNAME
$msiUrl = "https://cdn.zabbix.com/zabbix/binaries/stable/6.2/6.2.9/zabbix_agent-6.2.9-windows-amd64-openssl.msi"
$msiPath = "$env:TEMP\zabbix_agent.msi"

# Função para parar com erro
function Stop-OnError {
    param($message)
    Write-Host "ERRO: $message" -ForegroundColor Red
    exit 1
}

# Baixar o MSI
Write-Host "Baixando o instalador do Zabbix Agent..."
try {
    Invoke-WebRequest -Uri $msiUrl -OutFile $msiPath -ErrorAction Stop
} catch {
    Stop-OnError "Falha ao baixar o instalador MSI do Zabbix."
}

# Instalar o MSI
Write-Host "Instalando o agente do Zabbix..."
$installArgs = @(
    "/i `"$msiPath`"",
    "SERVER=$zabbixServer",
    "SERVERACTIVE=$zabbixServer",
    "HOSTNAME=$agentHostname",
    "/quiet"
)

$installResult = Start-Process -FilePath "msiexec.exe" -ArgumentList $installArgs -Wait -Passthru

if ($installResult.ExitCode -ne 0) {
    Stop-OnError "Erro durante a instalação. Código: $($installResult.ExitCode)"
}

# Regras de Firewall
Write-Host "Configurando o firewall para liberar portas 10050 e 10051..."
try {
    New-NetFirewallRule -DisplayName "Zabbix Agent TCP 10050" -Direction Inbound -Protocol TCP -LocalPort 10050 -Action Allow -ErrorAction Stop
    New-NetFirewallRule -DisplayName "Zabbix Server TCP 10051" -Direction Outbound -Protocol TCP -RemotePort 10051 -Action Allow -ErrorAction Stop
} catch {
    Stop-OnError "Erro ao configurar o firewall."
}

# Iniciar o serviço
Write-Host "Iniciando o serviço do Zabbix Agent..."
try {
    Start-Service -Name "Zabbix Agent"
    Set-Service -Name "Zabbix Agent" -StartupType Automatic
} catch {
    Stop-OnError "Erro ao iniciar o serviço Zabbix Agent."
}

# Verificar se está rodando
Start-Sleep -Seconds 3
$service = Get-Service -Name "Zabbix Agent" -ErrorAction SilentlyContinue
if ($service.Status -ne "Running") {
    Stop-OnError "Serviço Zabbix Agent não está rodando."
} else {
    Write-Host "Zabbix Agent instalado e em execução." -ForegroundColor Green
}

# Testar conexão com o servidor Zabbix
Write-Host "Testando conectividade com o servidor Zabbix ($zabbixServer)..."
if (Test-Connection -ComputerName $zabbixServer -Count 2 -Quiet) {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($zabbixServer, 10051)
        if ($tcpClient.Connected) {
            Write-Host "Conexão com o servidor Zabbix (porta 10051) bem-sucedida." -ForegroundColor Green
        } else {
            Stop-OnError "Não foi possível conectar à porta 10051 do servidor Zabbix."
        }
    } catch {
        Stop-OnError "Erro ao conectar na porta 10051 do servidor Zabbix."
    } finally {
        $tcpClient.Close()
    }
} else {
    Stop-OnError "Servidor Zabbix ($zabbixServer) não respondeu ao ping."
}