# Automação de agentes Zabbix

Este projeto nasceu de uma necessidade de infraestrutura: tornar a instalação e a configuração de agentes de monitoramento mais consistentes entre servidores. Reúne os scripts originais em Bash e PowerShell e uma evolução testável para gerar configurações do agente clássico em Linux.

O foco desta versão é separar a preparação da configuração da alteração do servidor. Assim, é possível revisar o resultado, executar testes e planejar a mudança antes de instalar pacotes ou reiniciar serviços.

## O que você pode verificar neste repositório

| Componente | Evidência técnica | Limite atual |
| --- | --- | --- |
| `tools/render_agent_config.py` | CLI parametrizada, validação de entradas, modos ativo/passivo e TLS com PSK | Gera texto; não instala nem configura o host |
| `tests/` | Testes de comportamento, IPv6, entradas inválidas e configuração de TLS | Não substituem teste com servidor Zabbix |
| `.github/workflows/validate.yml` | Pipeline de CI em Linux e Windows | Não realiza deploy nem acessa infraestrutura externa |
| Scripts Bash e PowerShell da raiz | Histórico da automação de instalação | Versões antigas e mudanças de firewall exigem revisão antes do uso |
| [Runbook](docs/RUNBOOK.md) | Instalação assistida, validação, diagnóstico e recuperação | Aplicação manual em ambiente controlado |

## Execução local

Requisito: Python 3.10 ou superior. O gerador usa apenas a biblioteca padrão, não exige root e não faz chamadas de rede.

```bash
git clone https://github.com/Glaucojr17/Script-Instala-o-Agente-Zabbix.git
cd Script-Instala-o-Agente-Zabbix
python3 -m unittest discover -s tests -v
python3 tools/render_agent_config.py \
  --server zabbix.example.net \
  --hostname lab-linux-01 \
  --psk-identity lab-linux-01 \
  --psk-file /etc/zabbix/agent.psk
```

O resultado é impresso no terminal. Para gerar um arquivo de revisão, redirecione a saída para `zabbix_agentd.generated.conf`. A chave PSK não é recebida nem criada pelo programa; somente seu caminho e sua identidade são referenciados.

Para verificações passivas, adicione `--mode passive`; para ambos os modos, `--mode both`. A configuração padrão usa verificações ativas e desativa os workers passivos com `StartAgents=0`. O endereço informado deve ser um único IP ou nome DNS; portas personalizadas de verificações ativas usam `--active-port`.

Somente em laboratório isolado, é possível gerar uma configuração sem TLS com `--allow-unencrypted`, omitindo as opções PSK. Essa escolha precisa ser explícita.

## Decisões de implementação

- **Gerar antes de aplicar:** evita que um teste local altere pacotes, firewall ou serviços.
- **TLS como padrão:** o gerador exige identidade e caminho de PSK e recusa opções conflitantes.
- **Entradas restritas:** impede que quebras de linha e delimitadores insiram diretivas na configuração.
- **Saída determinística:** os mesmos argumentos geram o mesmo conteúdo, facilitando revisão em Git e uso em IaC.
- **Sem dependências externas:** o exemplo pode ser executado em um ambiente simples e incorporado a pipelines.

## Sobre os instaladores originais

`Script_instalacaoagenteZabbixUbuntu_Debian.sh` e `Script_instalacaoagenteZabbixWindows.ps1` foram preservados como histórico. Usam versões 6.4 e 6.2.9, respectivamente, endereços que precisam ser substituídos e regras de firewall amplas. Não são o caminho recomendado desta versão para produção.

O script Linux original também procura a palavra `active` na saída do UFW, que pode aparecer dentro de `inactive`. Ambos dependem de resposta ICMP antes de validar conectividade. A evolução documentada no runbook usa verificação TCP e regras de acesso específicas, aplicadas conscientemente pelo operador.

## Validação e próximos passos

O pipeline executa os testes do gerador e verifica a sintaxe dos scripts originais, sem executá-los. Aprovação no CI demonstra esses controles; não significa homologação do agente em produção.

A próxima etapa técnica é validar instalação, autenticação TLS e coleta real em VMs descartáveis com Debian/Ubuntu e Windows. Instalação idempotente, rollback automatizado e testes de integração continuam como evolução futura.

Autor: [Glauco Junior](https://github.com/Glaucojr17) — infraestrutura, automação e observabilidade.
