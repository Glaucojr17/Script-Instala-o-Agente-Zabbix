#!/bin/bash

ZABBIX_SERVER="10.46.0.114"
ZABBIX_VERSION="6.4"
AGENT_HOSTNAME=$(hostname)
ZABBIX_CONF="/etc/zabbix/zabbix_agentd.conf"

stop_on_error() {
    echo "❌ ERRO: $1"
    exit 1
}

echo "🔧 Detectando sistema operacional..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION_ID=$VERSION_ID
else
    stop_on_error "Não foi possível detectar a distribuição."
fi

echo "🖥 Instalando Zabbix Agent em $DISTRO $VERSION_ID"

# Adiciona repositório do Zabbix conforme a distro
if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" ]]; then
    wget https://repo.zabbix.com/zabbix/${ZABBIX_VERSION}/$DISTRO/pool/main/z/zabbix-release/zabbix-release_${ZABBIX_VERSION}-1+$DISTRO${VERSION_ID}_all.deb -O /tmp/zabbix-release.deb \
        || stop_on_error "Falha ao baixar o repositório do Zabbix"
    dpkg -i /tmp/zabbix-release.deb || stop_on_error "Falha ao adicionar repositório"
    apt update || stop_on_error "Erro ao atualizar pacotes"
else
    stop_on_error "Distribuição não suportada: $DISTRO $VERSION_ID"
fi

# Instala agente
apt install -y zabbix-agent || stop_on_error "Erro ao instalar o agente"

# Configura agente
sed -i "s/^Server=.*/Server=$ZABBIX_SERVER/" $ZABBIX_CONF
sed -i "s/^ServerActive=.*/ServerActive=$ZABBIX_SERVER/" $ZABBIX_CONF
sed -i "s/^Hostname=.*/Hostname=$AGENT_HOSTNAME/" $ZABBIX_CONF

# Ativa e inicia serviço
systemctl enable zabbix-agent
systemctl restart zabbix-agent || stop_on_error "Erro ao iniciar o serviço zabbix-agent"

# Libera firewall (UFW)
if command -v ufw >/dev/null && ufw status | grep -q active; then
    echo "🛡 Liberando portas 10050 e 10051 no UFW..."
    ufw allow 10050/tcp
    ufw allow 10051/tcp
    ufw reload
fi

# Verifica status do serviço
sleep 3
if systemctl is-active --quiet zabbix-agent; then
    echo "✅ Zabbix Agent está em execução."
else
    stop_on_error "Serviço zabbix-agent não está rodando."
fi

# Teste de conectividade
echo "🌐 Testando conectividade com o servidor Zabbix ($ZABBIX_SERVER)..."
if ping -c 2 $ZABBIX_SERVER > /dev/null; then
    if nc -zv $ZABBIX_SERVER 10051; then
        echo "✅ Conexão com o servidor Zabbix (porta 10051) bem-sucedida."
    else
        stop_on_error "Não foi possível conectar à porta 10051 do servidor Zabbix."
    fi
else
    stop_on_error "Servidor Zabbix ($ZABBIX_SERVER) não respondeu ao ping."
fi
