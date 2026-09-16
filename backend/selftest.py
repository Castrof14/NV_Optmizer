"""
NV Optimizer 2.0 - Backend Self-Test
Testa o backend de forma real. Rode como administrador no Windows para
validar operações que exigem elevação.

Uso (Windows):
    python backend/selftest.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import dispatch  # noqa: E402


def _test(name, op, kwargs=None, expect_success=None):
    kwargs = kwargs or {}
    r = dispatch(op, **kwargs)
    ok = r["success"]
    code = r["code"]
    msg = (r.get("message") or "")[:80]

    status = "PASS" if (expect_success is None or ok == expect_success) else "FAIL"
    marker = "  [OK] " if status == "PASS" else "  [FALHA] "
    print(f"{marker}{name:<42} {code:<18} {msg}")


def main():
    print("=" * 70)
    print(" NV OPTIMIZER 2.0 - BACKEND SELF-TEST")
    print("=" * 70)

    print("\n--- SISTEMA ---")
    _test("Detecção do sistema", "system.info", expect_success=True)
    _test("Compatibilidade Windows 10/11", "system.check", expect_success=True)
    _test("Status de administrador", "admin.status", expect_success=True)
    _test("Ativação do Windows", "licensing.windows", expect_success=True)

    print("\n--- PROGRAMAS ---")
    _test("Listar programas", "programs.list", expect_success=True)
    _test("Instalar programa desconhecido", "programs.install",
          {"program_id": "nao-existe"}, expect_success=False)
    _test("Instalar programa (admin?)", "programs.install",
          {"program_id": "steam"}, expect_success=None)

    print("\n--- OFFICE ---")
    _test("Status do Office", "office.status", expect_success=True)
    _test("Verificar Office", "office.check", expect_success=True)
    _test("Instalar Office", "office.install", expect_success=None)

    print("\n--- WINDOWS DEFENDER ---")
    _test("Status do Defender", "defender.status", expect_success=True)
    _test("Status do Firewall", "firewall.status", expect_success=True)
    _test("Ativar Defender", "defender.enable", expect_success=None)
    _test("Desativar Defender (sem confirmação)", "defender.disable",
          expect_success=False)

    print("\n--- DRIVERS ---")
    _test("Info da GPU", "drivers.gpu", expect_success=True)
    _test("Buscar driver oficial", "drivers.search", expect_success=None)

    print("\n--- ENERGIA ---")
    _test("Configurações de energia", "power.settings", expect_success=True)

    print("\n--- EDGE ---")
    _test("Status do Edge", "edge.status", expect_success=True)
    _test("Desinstalar Edge (sem confirmação)", "edge.uninstall",
          expect_success=False)

    print("\n--- OTIMIZAÇÃO ---")
    _test("Analisar perfil Office", "optimization.analyze",
          {"profile": "office"}, expect_success=True)
    _test("Analisar perfil Gaming", "optimization.analyze",
          {"profile": "gaming"}, expect_success=True)
    _test("Aplicar perfil inválido", "optimization.analyze",
          {"profile": "x"}, expect_success=False)
    _test("Aplicar Gaming (sem confirmação)", "optimization.apply",
          {"profile": "gaming"}, expect_success=False)

    print("\n--- STRESS ---")
    _test("Diagnóstico de memória", "stress.memory-diagnostic",
          expect_success=True)
    _test("Iniciar stress CPU (curto)", "stress.start",
          {"test_type": "cpu", "duration": 3}, expect_success=True)
    _test("Status do stress", "stress.status", expect_success=True)
    _test("Cancelar stress", "stress.cancel", expect_success=True)

    print("\n--- BACKUP / RESTORE ---")
    _test("Listar pontos de restauração", "optimization.restore-points",
          expect_success=True)
    _test("Restaurar sessão inexistente", "optimization.restore",
          {"session_id": "fake"}, expect_success=None)
    _test("Criar backup (admin?)", "backup.create",
          {"profile": "office"}, expect_success=None)

    print("\n--- LOGS ---")
    _test("Obter logs", "logs.get", expect_success=True)
    _test("Caminho dos logs", "logs.paths", expect_success=True)

    print("\n--- SEGURANÇA API ---")
    _test("Operação não registrada", "nao.existe", expect_success=False)

    print("\n" + "=" * 70)
    print(" BACKEND SELF-TEST CONCLUÍDO")
    print("=" * 70)
    print("\nNotas:")
    print("  - Operações que exigem administrador retornam ADMIN_REQUIRED")
    print("    quando executadas sem elevação (comportamento esperado).")
    print("  - Rode este script como Administrador no Windows para")
    print("    validar instalações, serviços, energia e otimizações.")


if __name__ == "__main__":
    main()