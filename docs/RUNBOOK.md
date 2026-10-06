# Operação assistida do agente clássico em Linux

Este roteiro descreve uma mudança manual, começando por uma VM de laboratório. O gerador produz uma configuração mínima; ele não inclui personalizações existentes, UserParameters ou arquivos de Include. Não substitua uma configuração existente sem revisar essas diferenças.

## Preparar a mudança

1. Escolha o pacote oficial do agente clássico compatível com o sistema operacional e com sua política de versões. Consulte o [seletor oficial](https://www.zabbix.com/download) e a [instalação por pacotes](https://www.zabbix.com/documentation/7.0/en/manual/installation/install_from_packages).
2. Identifique servidor/proxy, nome exato do host no frontend e modo de coleta. O gerador desta versão atende ao agente clássico (`zabbix_agentd`), não ao Agent 2 ou ao Windows.
3. Salve a configuração atual e registre versão do pacote, estado do serviço e regras de rede antes da mudança.
4. Provisione a PSK por um canal apropriado, fora do Git. Dê leitura somente ao usuário do agente e ao administrador. Cadastre a mesma identidade e chave no frontend. O gerador não verifica se o arquivo existe nem se a chave está correta.
5. Gere a configuração para um arquivo temporário e compare com a atual. A saída usa `LogType=console`, apropriado para execução em primeiro plano; antes do uso no serviço empacotado, adapte a configuração de logs/PID e as opções do serviço conforme o pacote instalado.

## Validar rede e configuração

No modo ativo, o agente abre a conexão para o servidor/proxy na porta TCP 10051 (ou na porta configurada). Não é preciso abrir entrada 10051 no host monitorado. No modo passivo, permita entrada TCP 10050 apenas a partir do servidor/proxy autorizado. O gerador não cria nenhuma regra de firewall.

```bash
# No host monitorado: resolução DNS e conexão TCP para verificações ativas.
getent hosts zabbix.example.net
nc -vz -w 3 zabbix.example.net 10051

# Teste local de um item com o arquivo que você revisou.
zabbix_agentd -c ./zabbix_agentd.generated.conf -t agent.ping
```

Esses comandos pressupõem as ferramentas instaladas. TCP acessível não comprova autenticação TLS nem coleta. `agent.ping` local também não confirma comunicação ponta a ponta.

Para verificações passivas, use `zabbix_get` a partir do servidor/proxy autorizado, com as opções TLS correspondentes. Para ativas, confira o nome do host, a identidade PSK, os logs do agente/servidor e a chegada de novos valores no frontend. Bloqueio de ICMP não implica falha do agente.

## Aplicar e observar

Depois de revisar e adaptar o arquivo ao pacote, use uma janela de mudança. Instale a configuração com proprietário e permissões adequados, reinicie o serviço correspondente e examine status e logs. Exemplos para o nome habitual do serviço:

```bash
systemctl status zabbix-agent --no-pager
journalctl -u zabbix-agent --since '-10 minutes' --no-pager
```

Confira coleta recente no frontend, erros de TLS, nome do host e itens sem suporte. Registre os horários de mudança e as verificações realizadas. Sem evidência de coleta, o serviço estar ativo não basta para encerrar a mudança.

## Recuperar e investigar

Se a coleta falhar, preserve os logs. Retorne à configuração anterior e reinicie o serviço; confirme a retomada de valores. Se houve mudança de pacote, recuperar a configuração pode não ser suficiente: a versão e suas dependências devem seguir o plano de retorno preparado antes da alteração.

| Sintoma | Verificação inicial |
| --- | --- |
| Nome não resolve | DNS no host, resolvers e nome do servidor/proxy |
| TCP não conecta | Rota, firewall de saída/entrada, porta e processo no destino |
| TLS recusado | Identidade PSK, chave, permissões e configuração do frontend |
| Ativas sem dados | Correspondência de Hostname, tipo dos itens e proxy atribuído |
| Passivas recusadas | Origem autorizada em Server, firewall e TLSAccept |
| Serviço falha ao iniciar | Diretivas, caminho dos arquivos, usuário, logs e unidade systemd |

Referências: [parâmetros do agente](https://www.zabbix.com/documentation/7.0/en/manual/appendix/config/zabbix_agentd), [criptografia](https://www.zabbix.com/documentation/7.0/en/manual/encryption) e [coleta Linux](https://www.zabbix.com/documentation/7.0/en/manual/quickstart/monitor_linux).
