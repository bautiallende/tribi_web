#!/usr/bin/env python3
"""
Script de diagnóstico completo para Tribi
Verifica configuración, conectividad y genera reporte
"""
import socket
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

COLORS = {
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "BOLD": "\033[1m",
    "END": "\033[0m",
}


class DiagnosticTool:
    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.passed = 0
        self.failed = 0

    def print_header(self, text: str):
        print(f"\n{COLORS['CYAN']}{COLORS['BOLD']}{'='*70}{COLORS['END']}")
        print(f"{COLORS['CYAN']}{COLORS['BOLD']}{text:^70}{COLORS['END']}")
        print(f"{COLORS['CYAN']}{COLORS['BOLD']}{'='*70}{COLORS['END']}\n")

    def print_test(self, name: str):
        print(f"{COLORS['BLUE']}▶ {name:<60}{COLORS['END']}", end=" ")
        sys.stdout.flush()

    def print_pass(self, msg: str = ""):
        suffix = f" ({msg})" if msg else ""
        print(f"{COLORS['GREEN']}✓{suffix}{COLORS['END']}")
        self.passed += 1

    def print_fail(self, msg: str):
        print(f"{COLORS['RED']}✗ {msg}{COLORS['END']}")
        self.failed += 1
        self.issues.append(msg)

    def print_warn(self, msg: str):
        print(f"{COLORS['YELLOW']}⚠ {msg}{COLORS['END']}")
        self.warnings.append(msg)

    def check_file_exists(self, path: str, description: str) -> bool:
        """Verifica que un archivo exista"""
        self.print_test(f"Checking {description}")
        if Path(path).exists():
            self.print_pass()
            return True
        else:
            self.print_fail(f"Not found: {path}")
            return False

    def check_port(self, port: int, service: str) -> bool:
        """Verifica si un puerto está escuchando"""
        self.print_test(f"Checking {service} on port {port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()

        if result == 0:
            self.print_pass("listening")
            return True
        else:
            self.print_fail(f"Not listening on port {port}")
            return False

    def check_env_var(
        self, filepath: str, var_name: str, required: bool = True
    ) -> Tuple[bool, str]:
        """Verifica que una variable de entorno exista en el .env"""
        self.print_test(f"Checking {var_name} in .env")

        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith(var_name + "="):
                        value = line.split("=", 1)[1]
                        if value:
                            self.print_pass("set")
                            return True, value
                        else:
                            if required:
                                self.print_fail("empty")
                            else:
                                self.print_warn("empty")
                            return False, ""

                if required:
                    self.print_fail("not found")
                else:
                    self.print_warn("not found")
                return False, ""
        except Exception as e:
            self.print_fail(f"Error reading file: {e}")
            return False, ""

    def check_process_running(self, pattern: str, name: str) -> bool:
        """Verifica si un proceso está corriendo (Windows)"""
        self.print_test(f"Checking {name} process")
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f'Get-Process | Where-Object {{$_.ProcessName -like "*{pattern}*"}} | Select-Object -First 1',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.stdout.strip() and "ProcessName" in result.stdout:
                self.print_pass("running")
                return True
            else:
                self.print_fail("not running")
                return False
        except Exception as e:
            self.print_fail(f"Error checking process: {e}")
            return False

    def run_diagnostics(self):
        """Ejecuta todos los diagnósticos"""
        print(
            f"\n{COLORS['BOLD']}{COLORS['CYAN']}🔍 TRIBI DIAGNOSTIC TOOL{COLORS['END']}"
        )
        print(
            f"{COLORS['CYAN']}Checking system configuration and services...{COLORS['END']}"
        )

        # 1. Verificar estructura de archivos
        self.print_header("FILE STRUCTURE")
        base_dir = Path(__file__).parent

        self.check_file_exists(
            str(base_dir / "apps" / "backend" / ".env"), "Backend .env file"
        )
        self.check_file_exists(
            str(base_dir / "apps" / "backend" / "app" / "main.py"), "Backend main.py"
        )
        self.check_file_exists(
            str(base_dir / "apps" / "web" / "package.json"), "Web package.json"
        )
        self.check_file_exists(
            str(base_dir / "apps" / "mobile" / "package.json"), "Mobile package.json"
        )
        self.check_file_exists(
            str(base_dir / "apps" / "mobile" / "app.config.js"), "Mobile app.config.js"
        )

        # 2. Verificar configuración del backend
        self.print_header("BACKEND CONFIGURATION")
        env_file = str(base_dir / "apps" / "backend" / ".env")

        self.check_env_var(env_file, "MYSQL_HOST")
        self.check_env_var(env_file, "MYSQL_DB")
        self.check_env_var(env_file, "JWT_SECRET")
        has_cookie_domain, cookie_domain = self.check_env_var(env_file, "COOKIE_DOMAIN")
        has_admin_emails, admin_emails = self.check_env_var(env_file, "ADMIN_EMAILS")

        if has_cookie_domain and cookie_domain:
            print(f"  {COLORS['CYAN']}COOKIE_DOMAIN = {cookie_domain}{COLORS['END']}")

        if has_admin_emails and admin_emails:
            print(f"  {COLORS['CYAN']}ADMIN_EMAILS = {admin_emails}{COLORS['END']}")

        # 3. Verificar servicios corriendo
        self.print_header("SERVICES STATUS")

        mysql_running = self.check_port(3306, "MySQL")
        backend_running = self.check_port(8000, "Backend (FastAPI)")
        web_running = self.check_port(3000, "Frontend (Next.js)")

        # 4. Verificar procesos
        self.print_header("PROCESSES")

        # No podemos verificar reliably los procesos en Windows, skip this
        print(f"{COLORS['YELLOW']}Process checking skipped on Windows{COLORS['END']}")

        # 5. Verificar conectividad API
        self.print_header("API CONNECTIVITY")

        if backend_running:
            try:
                import requests

                # Health check
                self.print_test("GET /health")
                try:
                    r = requests.get("http://localhost:8000/health", timeout=5)
                    if r.status_code == 200:
                        self.print_pass(f"status={r.json().get('status')}")
                    else:
                        self.print_fail(f"Status {r.status_code}")
                except Exception as e:
                    self.print_fail(f"Connection failed: {e}")

                # Countries endpoint
                self.print_test("GET /api/countries")
                try:
                    r = requests.get("http://localhost:8000/api/countries", timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        count = len(data) if isinstance(data, list) else 0
                        self.print_pass(f"{count} countries")
                    else:
                        self.print_fail(f"Status {r.status_code}")
                except Exception as e:
                    self.print_fail(f"Connection failed: {e}")

            except ImportError:
                self.print_warn("'requests' module not available, skipping API tests")
        else:
            print(
                f"{COLORS['YELLOW']}Backend not running, skipping API tests{COLORS['END']}"
            )

        # 6. Verificar configuración de CORS
        self.print_header("CORS CONFIGURATION")

        main_py = base_dir / "apps" / "backend" / "app" / "main.py"
        if main_py.exists():
            with open(main_py, "r", encoding="utf-8") as f:
                content = f.read()

                self.print_test("CORS middleware configured")
                if "CORSMiddleware" in content:
                    self.print_pass()
                else:
                    self.print_fail("CORSMiddleware not found")

                self.print_test("CORS allows credentials")
                if "allow_credentials=True" in content:
                    self.print_pass()
                else:
                    self.print_fail("allow_credentials not set to True")

        # 7. Verificar configuración de cookies en auth
        self.print_header("COOKIE CONFIGURATION")

        auth_py = base_dir / "apps" / "backend" / "app" / "api" / "auth.py"
        if auth_py.exists():
            with open(auth_py, "r", encoding="utf-8") as f:
                content = f.read()

                self.print_test("Cookie set in verify endpoint")
                if "response.set_cookie" in content and "tribi_token" in content:
                    self.print_pass()
                else:
                    self.print_fail("Cookie not being set")

                self.print_test("Cookie httponly=True")
                if "httponly=True" in content:
                    self.print_pass()
                else:
                    self.print_fail("httponly should be True")

                self.print_test("Cookie samesite='lax'")
                if 'samesite="lax"' in content or "samesite='lax'" in content:
                    self.print_pass()
                else:
                    self.print_warn("samesite not set to 'lax'")

        # 8. Verificar configuración del mobile
        self.print_header("MOBILE APP CONFIGURATION")

        app_config = base_dir / "apps" / "mobile" / "app.config.js"
        if app_config.exists():
            with open(app_config, "r", encoding="utf-8") as f:
                content = f.read()

                self.print_test("OTA updates disabled")
                if "enabled: false" in content:
                    self.print_pass()
                else:
                    self.print_fail("OTA updates should be disabled")

                self.print_test("API base URL configured")
                if "apiBase:" in content:
                    # Extract the URL
                    import re

                    match = re.search(r'apiBase:\s*["\']([^"\']+)["\']', content)
                    if match:
                        url = match.group(1)
                        self.print_pass(f"URL={url}")
                    else:
                        self.print_pass()
                else:
                    self.print_fail("apiBase not configured")

        # RESUMEN
        self.print_summary()

    def print_summary(self):
        """Imprime el resumen final"""
        total = self.passed + self.failed

        print(f"\n{COLORS['BOLD']}{'='*70}{COLORS['END']}")
        print(f"{COLORS['BOLD']}DIAGNOSTIC SUMMARY{COLORS['END']}")
        print(f"{COLORS['BOLD']}{'='*70}{COLORS['END']}")

        print(f"Total checks: {total}")
        print(f"{COLORS['GREEN']}Passed: {self.passed}{COLORS['END']}")
        print(f"{COLORS['RED']}Failed: {self.failed}{COLORS['END']}")
        print(f"{COLORS['YELLOW']}Warnings: {len(self.warnings)}{COLORS['END']}")

        if self.issues:
            print(f"\n{COLORS['RED']}{COLORS['BOLD']}CRITICAL ISSUES:{COLORS['END']}")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        if self.warnings:
            print(f"\n{COLORS['YELLOW']}{COLORS['BOLD']}WARNINGS:{COLORS['END']}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        print(f"\n{COLORS['CYAN']}{COLORS['BOLD']}RECOMMENDATIONS:{COLORS['END']}")

        if not self.check_port(8000, "Backend"):
            print("  • Start the backend:")
            print(
                f"    {COLORS['BLUE']}cd apps/backend && python -m uvicorn app.main:app --reload --port 8000{COLORS['END']}"
            )

        if not self.check_port(3000, "Frontend"):
            print("  • Start the frontend:")
            print(f"    {COLORS['BLUE']}cd apps/web && npm run dev{COLORS['END']}")

        if self.issues or self.warnings:
            print("\n  • Review the issues above and fix them")
            print(
                f"  • Check {COLORS['BLUE']}DEBUGGING_GUIDE.md{COLORS['END']} for solutions"
            )
            print(
                f"  • Run {COLORS['BLUE']}python test_api_complete.py{COLORS['END']} to test API endpoints"
            )

        if self.failed == 0:
            print(
                f"\n{COLORS['GREEN']}{COLORS['BOLD']}✓ ALL CHECKS PASSED!{COLORS['END']}"
            )
            print(
                f"\n{COLORS['CYAN']}Your system is ready. You can now:{COLORS['END']}"
            )
            print(
                f"  1. Login at {COLORS['BLUE']}http://localhost:3000/auth{COLORS['END']}"
            )
            print(
                f"  2. Access admin at {COLORS['BLUE']}http://localhost:3000/admin{COLORS['END']}"
            )
            print(
                f"  3. Run API tests: {COLORS['BLUE']}python test_api_complete.py{COLORS['END']}"
            )
            return 0
        else:
            print(
                f"\n{COLORS['RED']}{COLORS['BOLD']}✗ SOME CHECKS FAILED{COLORS['END']}"
            )
            print(
                f"{COLORS['YELLOW']}Fix the issues above before continuing{COLORS['END']}"
            )
            return 1


def main():
    """Función principal"""
    tool = DiagnosticTool()
    exit_code = tool.run_diagnostics()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
