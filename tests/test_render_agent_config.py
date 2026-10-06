import subprocess
import sys
import unittest
import argparse
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'render_agent_config.py'


class AgentConfigTests(unittest.TestCase):
    def run_config(self, *extra, server='zabbix.example.net', hostname='lab-linux-01', tls=True):
        command = [sys.executable, str(SCRIPT), '--server', server, '--hostname', hostname]
        if tls:
            command += ['--psk-identity', 'lab-linux-01', '--psk-file', '/etc/zabbix/agent.psk']
        return subprocess.run(command + list(extra), text=True, capture_output=True)

    def test_active_mode_uses_tls_and_disables_passive_workers(self):
        result = self.run_config()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('StartAgents=0\n', result.stdout)
        self.assertIn('TLSConnect=psk\n', result.stdout)
        self.assertNotIn('\nServer=', result.stdout)
        self.assertNotIn('ListenPort=', result.stdout)

    def test_passive_mode_restricts_source_and_uses_tls(self):
        result = self.run_config('--mode', 'passive', server='192.0.2.10')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Server=192.0.2.10\n', result.stdout)
        self.assertIn('TLSAccept=psk\n', result.stdout)
        self.assertNotIn('ServerActive=', result.stdout)

    def test_both_modes(self):
        result = self.run_config('--mode', 'both')
        self.assertEqual(result.returncode, 0)
        self.assertIn('TLSConnect=psk', result.stdout)
        self.assertIn('TLSAccept=psk', result.stdout)

    def test_ipv6_active_endpoint_has_brackets(self):
        result = self.run_config(server='2001:db8::10')
        self.assertEqual(result.returncode, 0)
        self.assertIn('ServerActive=[2001:db8::10]:10051', result.stdout)

    def test_config_injection_is_rejected(self):
        for value in ['valid\nUnsafeUserParameters=1', 'valid#comment', ' x']:
            with self.subTest(value=value):
                result = self.run_config(hostname=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')

    def test_invalid_server_is_rejected(self):
        for value in ['https://example.net', 'host:10051', 'host,other', '$(id)', 'host\nServer=x', '-bad.net']:
            with self.subTest(value=value):
                self.assertNotEqual(self.run_config(server=value).returncode, 0)

    def test_tls_is_required_by_default(self):
        result = self.run_config(tls=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_plaintext_requires_explicit_opt_in(self):
        result = self.run_config('--allow-unencrypted', tls=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn('laboratório isolado', result.stdout)
        self.assertNotIn('TLSPSK', result.stdout)

    def test_conflicting_tls_options_are_rejected(self):
        self.assertNotEqual(self.run_config('--allow-unencrypted').returncode, 0)

    def test_invalid_port_is_rejected(self):
        for port in ['0', '65536', 'invalid']:
            self.assertNotEqual(self.run_config('--active-port', port).returncode, 0)

    def test_relative_and_injected_paths_are_rejected(self):
        for path in ['agent.psk', '/etc/../tmp/key', '/tmp/key\nServer=x', '/etc/zabbix/']:
            self.assertNotEqual(self.run_config('--psk-file', path).returncode, 0)

    def test_null_byte_in_path_is_rejected_before_rendering(self):
        spec = importlib.util.spec_from_file_location('render_agent_config', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(argparse.ArgumentTypeError):
            module.psk_path('/tmp/key\x00bad')

    def test_render_is_deterministic(self):
        self.assertEqual(self.run_config().stdout, self.run_config().stdout)


if __name__ == '__main__':
    unittest.main()
