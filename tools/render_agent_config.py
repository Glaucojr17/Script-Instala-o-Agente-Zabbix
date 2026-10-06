#!/usr/bin/env python3
"""Render a Zabbix classic agent Linux config without changing the host."""

import argparse
import ipaddress
import re
from pathlib import PurePosixPath


def server_address(value):
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if len(value) > 253 or not all(
        re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
        for label in value.split(".")
    ):
        raise argparse.ArgumentTypeError("use um IP ou nome DNS, sem porta, esquema ou lista")
    return value


def safe_text(value):
    if not value or len(value) > 128 or any(ord(c) < 32 or ord(c) > 126 for c in value):
        raise argparse.ArgumentTypeError("use de 1 a 128 caracteres ASCII imprimíveis")
    if any(c in value for c in "#=\\") or value != value.strip():
        raise argparse.ArgumentTypeError("valor contém delimitador ou espaços nas extremidades")
    return value


def hostname(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]{0,127}", value) or value != value.strip():
        raise argparse.ArgumentTypeError("hostname inválido; use letras ASCII, números, ponto, hífen ou underscore")
    return value


def psk_path(value):
    if not PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts:
        raise argparse.ArgumentTypeError("use um caminho Linux absoluto sem '..'")
    if any(ord(c) < 32 or ord(c) > 126 for c in value) or any(c in value for c in "#=") or value.endswith('/'):
        raise argparse.ArgumentTypeError("caminho de arquivo inválido")
    return value


def render(args):
    active = args.mode in ('active', 'both')
    passive = args.mode in ('passive', 'both')
    endpoint = f'[{args.server}]' if ':' in args.server else args.server
    lines = [
        '# Gerado para Zabbix agent clássico em Linux. Revise antes de aplicar.',
        f'Hostname={args.hostname}', 'LogType=console', 'Timeout=3',
        'UnsafeUserParameters=0', f'StartAgents={3 if passive else 0}',
    ]
    if passive:
        lines.extend([f'Server={args.server}', 'ListenPort=10050'])
    if active:
        lines.append(f'ServerActive={endpoint}:{args.active_port}')
    if args.allow_unencrypted:
        lines.append('# Sem TLS: usar somente em laboratório isolado.')
    else:
        if active:
            lines.append('TLSConnect=psk')
        if passive:
            lines.append('TLSAccept=psk')
        lines.extend([f'TLSPSKIdentity={args.psk_identity}', f'TLSPSKFile={args.psk_file}'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', type=server_address, required=True)
    parser.add_argument('--hostname', type=hostname, required=True)
    parser.add_argument('--mode', choices=['active', 'passive', 'both'], default='active')
    parser.add_argument('--active-port', type=int, default=10051)
    parser.add_argument('--psk-identity', type=safe_text)
    parser.add_argument('--psk-file', type=psk_path)
    parser.add_argument('--allow-unencrypted', action='store_true', help='somente para laboratório isolado')
    args = parser.parse_args()
    if not 1 <= args.active_port <= 65535:
        parser.error('porta deve estar entre 1 e 65535')
    if args.allow_unencrypted:
        if args.psk_identity or args.psk_file:
            parser.error('não combine PSK com --allow-unencrypted')
    elif not args.psk_identity or not args.psk_file:
        parser.error('informe --psk-identity e --psk-file; o conteúdo da chave nunca é recebido pelo programa')
    print(render(args), end='')


if __name__ == '__main__':
    main()
