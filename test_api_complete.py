#!/usr/bin/env python3
"""
Script completo de pruebas para Tribi Web
Verifica todos los endpoints críticos y flujos de usuario
"""
import requests
import sys
import time
from typing import Optional, Dict, Any

# Configuración
API_BASE = "http://localhost:8000"
COLORS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKCYAN': '\033[96m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
}

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.session = requests.Session()
        self.test_email = "test@example.com"
        self.admin_email = None  # Se obtendrá del .env
        
    def print_header(self, text: str):
        """Imprime un encabezado de sección"""
        print(f"\n{COLORS['HEADER']}{COLORS['BOLD']}{'='*60}{COLORS['ENDC']}")
        print(f"{COLORS['HEADER']}{COLORS['BOLD']}{text:^60}{COLORS['ENDC']}")
        print(f"{COLORS['HEADER']}{COLORS['BOLD']}{'='*60}{COLORS['ENDC']}\n")
    
    def print_test(self, name: str):
        """Imprime el nombre del test"""
        print(f"{COLORS['OKBLUE']}▶ {name}{COLORS['ENDC']}", end=" ... ")
        sys.stdout.flush()
    
    def print_success(self, message: str = ""):
        """Imprime éxito"""
        msg = f" ({message})" if message else ""
        print(f"{COLORS['OKGREEN']}✓ PASS{msg}{COLORS['ENDC']}")
        self.passed += 1
    
    def print_failure(self, message: str):
        """Imprime fallo"""
        print(f"{COLORS['FAIL']}✗ FAIL: {message}{COLORS['ENDC']}")
        self.failed += 1
    
    def print_warning(self, message: str):
        """Imprime advertencia"""
        print(f"{COLORS['WARNING']}⚠ WARNING: {message}{COLORS['ENDC']}")
    
    def test_health(self) -> bool:
        """Prueba el endpoint de health"""
        self.print_test("Health check")
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"status={data.get('status')}")
                return True
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_request_otp(self, email: str) -> Optional[str]:
        """Prueba el endpoint de solicitud de OTP"""
        self.print_test(f"Request OTP for {email}")
        try:
            response = self.session.post(
                f"{API_BASE}/api/auth/request-code",
                json={"email": email},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.print_success("OTP sent")
                return data.get("message", "")
            else:
                self.print_failure(f"Status {response.status_code}")
                return None
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return None
    
    def extract_otp_from_logs(self, email: str) -> Optional[str]:
        """
        Solicita al usuario que ingrese el OTP de los logs del backend
        """
        self.print_test("Waiting for OTP input")
        print(f"\n{COLORS['WARNING']}Please check backend logs for the OTP code sent to {email}{COLORS['ENDC']}")
        print(f"{COLORS['WARNING']}Look for a line like: 'OTP code for {email}: XXXXXX'{COLORS['ENDC']}")
        
        try:
            code = input(f"{COLORS['OKCYAN']}Enter OTP code: {COLORS['ENDC']}").strip()
            if code and code.isdigit() and len(code) == 6:
                self.print_success(f"OTP entered: {code}")
                return code
            else:
                self.print_failure("Invalid OTP format (must be 6 digits)")
                return None
        except KeyboardInterrupt:
            print(f"\n{COLORS['WARNING']}Test interrupted by user{COLORS['ENDC']}")
            return None
    
    def test_verify_otp(self, email: str, code: str) -> bool:
        """Prueba el endpoint de verificación de OTP"""
        self.print_test(f"Verify OTP for {email}")
        try:
            response = self.session.post(
                f"{API_BASE}/api/auth/verify",
                json={"email": email, "code": code},
                timeout=5
            )
            if response.status_code == 200:
                # Las cookies se guardan automáticamente en la sesión
                self.print_success("Authenticated")
                return True
            else:
                self.print_failure(f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_get_current_user(self) -> Optional[Dict[str, Any]]:
        """Prueba el endpoint /auth/me"""
        self.print_test("Get current user")
        try:
            response = self.session.get(f"{API_BASE}/api/auth/me", timeout=5)
            if response.status_code == 200:
                user = response.json()
                self.print_success(f"email={user.get('email')}")
                return user
            else:
                self.print_failure(f"Status {response.status_code}")
                return None
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return None
    
    def test_get_orders(self) -> bool:
        """Prueba el endpoint de órdenes del usuario"""
        self.print_test("Get user orders")
        try:
            response = self.session.get(f"{API_BASE}/api/orders/mine", timeout=5)
            if response.status_code == 200:
                orders = response.json()
                count = len(orders) if isinstance(orders, list) else 0
                self.print_success(f"{count} orders")
                return True
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_get_countries(self) -> bool:
        """Prueba el endpoint público de países"""
        self.print_test("Get countries list")
        try:
            response = self.session.get(f"{API_BASE}/api/countries", timeout=5)
            if response.status_code == 200:
                countries = response.json()
                count = len(countries) if isinstance(countries, list) else 0
                self.print_success(f"{count} countries")
                return True
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_admin_access(self) -> bool:
        """Prueba el acceso a endpoints de admin"""
        self.print_test("Admin: Get countries (with pagination)")
        try:
            response = self.session.get(
                f"{API_BASE}/admin/countries",
                params={"page": 1, "page_size": 10},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.print_success(f"{total} total countries")
                return True
            elif response.status_code == 403:
                self.print_failure("Access denied - Not an admin")
                return False
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_admin_carriers(self) -> bool:
        """Prueba el endpoint de carriers admin"""
        self.print_test("Admin: Get carriers")
        try:
            response = self.session.get(
                f"{API_BASE}/admin/carriers",
                params={"page": 1, "page_size": 10},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.print_success(f"{total} total carriers")
                return True
            elif response.status_code == 403:
                self.print_warning("Access denied - Not an admin (expected if not admin user)")
                return True  # No falla porque puede que no sea admin
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_admin_plans(self) -> bool:
        """Prueba el endpoint de plans admin"""
        self.print_test("Admin: Get plans")
        try:
            response = self.session.get(
                f"{API_BASE}/admin/plans",
                params={"page": 1, "page_size": 10},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.print_success(f"{total} total plans")
                return True
            elif response.status_code == 403:
                self.print_warning("Access denied - Not an admin (expected if not admin user)")
                return True
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def test_logout(self) -> bool:
        """Prueba el endpoint de logout"""
        self.print_test("Logout")
        try:
            response = self.session.post(f"{API_BASE}/api/auth/logout", timeout=5)
            if response.status_code == 200:
                self.print_success()
                return True
            else:
                self.print_failure(f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print(f"\n{COLORS['BOLD']}{COLORS['OKCYAN']}🧪 TRIBI API TEST SUITE{COLORS['ENDC']}")
        print(f"{COLORS['OKCYAN']}Testing API at: {API_BASE}{COLORS['ENDC']}")
        
        # 1. Tests básicos (sin autenticación)
        self.print_header("BASIC TESTS (No Auth Required)")
        self.test_health()
        self.test_get_countries()
        
        # 2. Flujo de autenticación de usuario
        self.print_header("USER AUTHENTICATION FLOW")
        
        # Solicitar OTP
        otp_result = self.test_request_otp(self.test_email)
        if not otp_result:
            self.print_warning("Cannot continue with auth tests - OTP request failed")
        else:
            # Extraer OTP (simulado)
            otp = self.extract_otp_from_logs(self.test_email)
            
            if otp:
                # Verificar OTP
                if self.test_verify_otp(self.test_email, otp):
                    # Tests con usuario autenticado
                    self.print_header("AUTHENTICATED USER TESTS")
                    self.test_get_current_user()
                    self.test_get_orders()
                    
                    # Tests de admin (pueden fallar si no es admin, y está bien)
                    self.print_header("ADMIN TESTS (May fail if not admin)")
                    self.test_admin_access()
                    self.test_admin_carriers()
                    self.test_admin_plans()
                    
                    # Logout
                    self.print_header("LOGOUT")
                    self.test_logout()
        
        # Resumen
        self.print_summary()
    
    def print_summary(self):
        """Imprime el resumen de tests"""
        total = self.passed + self.failed
        print(f"\n{COLORS['BOLD']}{'='*60}{COLORS['ENDC']}")
        print(f"{COLORS['BOLD']}TEST SUMMARY{COLORS['ENDC']}")
        print(f"{COLORS['BOLD']}{'='*60}{COLORS['ENDC']}")
        print(f"Total tests: {total}")
        print(f"{COLORS['OKGREEN']}Passed: {self.passed}{COLORS['ENDC']}")
        print(f"{COLORS['FAIL']}Failed: {self.failed}{COLORS['ENDC']}")
        
        if self.failed == 0:
            print(f"\n{COLORS['OKGREEN']}{COLORS['BOLD']}✓ ALL TESTS PASSED!{COLORS['ENDC']}")
            return 0
        else:
            print(f"\n{COLORS['FAIL']}{COLORS['BOLD']}✗ SOME TESTS FAILED{COLORS['ENDC']}")
            return 1

def main():
    """Función principal"""
    print(f"\n{COLORS['OKCYAN']}Starting Tribi API tests...{COLORS['ENDC']}")
    print(f"{COLORS['WARNING']}Make sure the backend is running at {API_BASE}{COLORS['ENDC']}")
    print(f"{COLORS['WARNING']}This test uses simulated OTP codes for authentication{COLORS['ENDC']}")
    
    time.sleep(2)
    
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
