#!/usr/bin/env python3
"""
Script para probar el flujo completo de autenticación
Hace login, verifica las cookies, y prueba endpoints autenticados
"""
import requests
import sys
import time

API_BASE = "http://localhost:8000"
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'BOLD': '\033[1m',
    'END': '\033[0m',
}

def print_header(text):
    print(f"\n{COLORS['CYAN']}{COLORS['BOLD']}{'='*70}{COLORS['END']}")
    print(f"{COLORS['CYAN']}{COLORS['BOLD']}{text:^70}{COLORS['END']}")
    print(f"{COLORS['CYAN']}{COLORS['BOLD']}{'='*70}{COLORS['END']}\n")

def print_step(text):
    print(f"{COLORS['BLUE']}▶ {text}{COLORS['END']}")

def print_success(text):
    print(f"{COLORS['GREEN']}✓ {text}{COLORS['END']}")

def print_error(text):
    print(f"{COLORS['RED']}✗ {text}{COLORS['END']}")

def print_warning(text):
    print(f"{COLORS['YELLOW']}⚠ {text}{COLORS['END']}")

def print_info(text):
    print(f"  {COLORS['CYAN']}{text}{COLORS['END']}")

def main():
    print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}🔐 TRIBI AUTHENTICATION TEST{COLORS['END']}")
    
    # Crear una sesión que maneje cookies automáticamente
    session = requests.Session()
    
    # Paso 1: Solicitar email
    print_header("STEP 1: GET EMAIL")
    email = input(f"{COLORS['YELLOW']}Enter your email: {COLORS['END']}").strip()
    
    if not email:
        print_error("Email is required")
        sys.exit(1)
    
    print_info(f"Using email: {email}")
    
    # Paso 2: Solicitar OTP
    print_header("STEP 2: REQUEST OTP CODE")
    print_step("Sending OTP request...")
    
    try:
        response = session.post(
            f"{API_BASE}/api/auth/request-code",
            json={"email": email},
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"OTP sent! Status: {response.status_code}")
            print_info("Check your backend logs for the OTP code")
            print_info("Look for a line like: '📝 BODY: Your login code is: XXXXXX'")
        else:
            print_error(f"Failed to send OTP: {response.status_code}")
            print_error(f"Response: {response.text}")
            sys.exit(1)
    except Exception as e:
        print_error(f"Network error: {e}")
        sys.exit(1)
    
    # Paso 3: Pedir el código al usuario
    print_header("STEP 3: ENTER OTP CODE")
    code = input(f"{COLORS['YELLOW']}Enter the 6-digit OTP code from backend logs: {COLORS['END']}").strip()
    
    if not code or len(code) != 6 or not code.isdigit():
        print_error("Invalid OTP format (must be 6 digits)")
        sys.exit(1)
    
    # Paso 4: Verificar el código
    print_header("STEP 4: VERIFY OTP CODE")
    print_step("Verifying code...")
    
    try:
        response = session.post(
            f"{API_BASE}/api/auth/verify",
            json={"email": email, "code": code},
            timeout=10
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Authentication successful!")
            data = response.json()
            
            print_info(f"Token received: {data['token'][:30]}...")
            print_info(f"User: {data['user']['email']}")
            
            # Verificar cookies
            print_step("Checking cookies in session...")
            cookies = session.cookies.get_dict()
            
            if 'tribi_token' in cookies:
                print_success(f"Cookie 'tribi_token' found in session")
                print_info(f"Cookie value: {cookies['tribi_token'][:30]}...")
            else:
                print_warning("Cookie 'tribi_token' NOT found in session")
                print_info("Available cookies:")
                for key, value in cookies.items():
                    print_info(f"  - {key}: {value[:30]}...")
            
            # Mostrar todos los headers de la respuesta
            print_step("Response headers:")
            for key, value in response.headers.items():
                if 'cookie' in key.lower() or 'set-cookie' in key.lower():
                    print_info(f"  {key}: {value}")
            
        else:
            print_error(f"Verification failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            sys.exit(1)
    except Exception as e:
        print_error(f"Network error: {e}")
        sys.exit(1)
    
    # Paso 5: Probar endpoint autenticado
    print_header("STEP 5: TEST AUTHENTICATED ENDPOINT")
    print_step("Calling GET /api/auth/me...")
    
    time.sleep(1)  # Dar tiempo para que se procese la cookie
    
    try:
        # Verificar que tenemos la cookie
        cookies_before = session.cookies.get_dict()
        print_info(f"Cookies before request: {list(cookies_before.keys())}")
        
        response = session.get(
            f"{API_BASE}/api/auth/me",
            timeout=10
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Successfully retrieved user profile!")
            user = response.json()
            print_info(f"User email: {user['email']}")
            print_info(f"User ID: {user['id']}")
        else:
            print_error(f"Failed to get user profile: {response.status_code}")
            print_error(f"Response: {response.text}")
            
            print_step("Debugging cookie issue...")
            print_info("Request headers sent:")
            # Reconstruir los headers que requests envió
            if 'tribi_token' in cookies_before:
                print_info(f"  Cookie header should contain: tribi_token={cookies_before['tribi_token'][:30]}...")
            else:
                print_error("  Cookie 'tribi_token' was not in the session!")
    except Exception as e:
        print_error(f"Network error: {e}")
        sys.exit(1)
    
    # Paso 6: Probar órdenes
    print_header("STEP 6: TEST ORDERS ENDPOINT")
    print_step("Calling GET /api/orders/mine...")
    
    try:
        response = session.get(
            f"{API_BASE}/api/orders/mine",
            timeout=10
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            print_success(f"Successfully retrieved orders!")
            print_info(f"Number of orders: {len(orders)}")
        else:
            print_error(f"Failed to get orders: {response.status_code}")
            print_error(f"Response: {response.text}")
    except Exception as e:
        print_error(f"Network error: {e}")
    
    # Resumen
    print_header("SUMMARY")
    print_info("If you saw '✓ Cookie tribi_token found' and '✓ Successfully retrieved user profile',")
    print_info("then the backend authentication is working correctly.")
    print_info("")
    print_info("If the cookie was found but /api/auth/me returned 401,")
    print_info("there's an issue with how requests is sending the cookie.")
    print_info("")
    print_info("Now test in the browser:")
    print_info(f"  1. Go to http://localhost:3000/auth")
    print_info(f"  2. Login with: {email}")
    print_info(f"  3. Use code from backend logs")
    print_info(f"  4. Check DevTools → Application → Cookies")
    print_info(f"  5. Try accessing http://localhost:3000/admin")

if __name__ == "__main__":
    main()
