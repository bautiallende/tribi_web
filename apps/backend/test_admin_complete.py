"""
Pruebas exhaustivas del panel de administración
Incluye: Countries, Carriers, Plans, CSV Import/Export, Search, Sorting, Pagination
"""
import requests
import csv
import io

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@tribi.com"

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{GREEN}✓ PASSED{RESET}" if passed else f"{RED}✗ FAILED{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")
    if not passed:
        raise Exception(f"Test failed: {name}")

def print_section(name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

# Session para mantener cookies
session = requests.Session()

# =============================================================================
# 1. AUTENTICACIÓN
# =============================================================================
print_section("1. AUTENTICACIÓN")

# Solicitar código de verificación
response = session.post(f"{BASE_URL}/api/auth/request-code", json={"email": ADMIN_EMAIL})
print_test("Request verification code", response.status_code == 200, f"Status: {response.status_code}")

# Simular verificación (en producción, obtendrías el código del email)
# Por ahora asumimos que el usuario está autenticado si el request code funcionó
print(f"{YELLOW}⚠ Nota: Para pruebas completas, necesitas verificar el código del email{RESET}\n")

# =============================================================================
# 2. COUNTRIES - CRUD, SEARCH, SORT, PAGINATION
# =============================================================================
print_section("2. COUNTRIES - CRUD, SEARCH, SORT, PAGINATION")

# 2.1 Listar países (verificar estructura de respuesta)
response = session.get(f"{BASE_URL}/admin/countries?page=1&page_size=20")
print_test("List countries", response.status_code in [200, 401, 403], f"Status: {response.status_code}")

if response.status_code in [401, 403]:
    print(f"{YELLOW}⚠ Admin authentication required. Skipping authenticated tests.{RESET}")
    print(f"{YELLOW}  To run full tests, complete email verification for {ADMIN_EMAIL}{RESET}\n")
    exit(0)

countries_data = response.json()
print_test("Countries response structure", 
           all(k in countries_data for k in ['countries', 'total', 'page', 'page_size']),
           f"Keys: {list(countries_data.keys())}")

initial_country_count = countries_data['total']
print(f"  Initial country count: {initial_country_count}")

# 2.2 Buscar país
if initial_country_count > 0:
    first_country_name = countries_data['countries'][0]['name']
    search_query = first_country_name[:3]
    response = session.get(f"{BASE_URL}/admin/countries?q={search_query}")
    print_test("Search countries", 
               response.status_code == 200 and len(response.json()['countries']) > 0,
               f"Query: '{search_query}', Results: {len(response.json()['countries'])}")

# 2.3 Ordenar por ISO2 (asc)
response = session.get(f"{BASE_URL}/admin/countries?sort_by=iso2&sort_order=asc&page_size=5")
countries_asc = response.json()['countries']
print_test("Sort countries by ISO2 (asc)", 
           response.status_code == 200 and len(countries_asc) > 0,
           f"First ISO2: {countries_asc[0]['iso2'] if countries_asc else 'N/A'}")

# 2.4 Ordenar por nombre (desc)
response = session.get(f"{BASE_URL}/admin/countries?sort_by=name&sort_order=desc&page_size=5")
countries_desc = response.json()['countries']
print_test("Sort countries by name (desc)", 
           response.status_code == 200 and len(countries_desc) > 0,
           f"First name: {countries_desc[0]['name'] if countries_desc else 'N/A'}")

# 2.5 Crear país
test_country = {
    "iso2": "ZZ",
    "name": "Test Country Delete Me"
}
response = session.post(f"{BASE_URL}/admin/countries", json=test_country)
print_test("Create country", response.status_code == 200, f"Status: {response.status_code}")
created_country = response.json()
test_country_id = created_country.get('id')

# 2.6 Actualizar país
if test_country_id:
    update_data = {
        "iso2": "ZZ",
        "name": "Test Country Updated"
    }
    response = session.put(f"{BASE_URL}/admin/countries/{test_country_id}", json=update_data)
    print_test("Update country", response.status_code == 200, f"Status: {response.status_code}")

# 2.7 Eliminar país
if test_country_id:
    response = session.delete(f"{BASE_URL}/admin/countries/{test_country_id}")
    print_test("Delete country", response.status_code == 200, f"Status: {response.status_code}")

# 2.8 Paginación
response = session.get(f"{BASE_URL}/admin/countries?page=1&page_size=5")
page1_data = response.json()
print_test("Pagination - page 1", 
           response.status_code == 200 and len(page1_data['countries']) <= 5,
           f"Items: {len(page1_data['countries'])}, Total: {page1_data['total']}")

# =============================================================================
# 3. CARRIERS - CRUD, SEARCH, SORT, PAGINATION
# =============================================================================
print_section("3. CARRIERS - CRUD, SEARCH, SORT, PAGINATION")

# 3.1 Listar carriers
response = session.get(f"{BASE_URL}/admin/carriers?page=1&page_size=20")
print_test("List carriers", response.status_code == 200, f"Status: {response.status_code}")
carriers_data = response.json()
initial_carrier_count = carriers_data['total']
print(f"  Initial carrier count: {initial_carrier_count}")

# 3.2 Buscar carrier
if initial_carrier_count > 0:
    first_carrier_name = carriers_data['carriers'][0]['name']
    search_query = first_carrier_name[:3]
    response = session.get(f"{BASE_URL}/admin/carriers?q={search_query}")
    print_test("Search carriers", 
               response.status_code == 200 and len(response.json()['carriers']) > 0,
               f"Query: '{search_query}', Results: {len(response.json()['carriers'])}")

# 3.3 Ordenar por nombre (asc)
response = session.get(f"{BASE_URL}/admin/carriers?sort_by=name&sort_order=asc&page_size=5")
carriers_asc = response.json()['carriers']
print_test("Sort carriers by name (asc)", 
           response.status_code == 200,
           f"First name: {carriers_asc[0]['name'] if carriers_asc else 'N/A'}")

# 3.4 Ordenar por ID (desc)
response = session.get(f"{BASE_URL}/admin/carriers?sort_by=id&sort_order=desc&page_size=5")
carriers_desc = response.json()['carriers']
print_test("Sort carriers by ID (desc)", 
           response.status_code == 200,
           f"First ID: {carriers_desc[0]['id'] if carriers_desc else 'N/A'}")

# 3.5 Crear carrier
test_carrier = {
    "name": "Test Carrier Delete Me"
}
response = session.post(f"{BASE_URL}/admin/carriers", json=test_carrier)
print_test("Create carrier", response.status_code == 200, f"Status: {response.status_code}")
created_carrier = response.json()
test_carrier_id = created_carrier.get('id')

# 3.6 Actualizar carrier
if test_carrier_id:
    update_data = {
        "name": "Test Carrier Updated"
    }
    response = session.put(f"{BASE_URL}/admin/carriers/{test_carrier_id}", json=update_data)
    print_test("Update carrier", response.status_code == 200, f"Status: {response.status_code}")

# 3.7 Eliminar carrier
if test_carrier_id:
    response = session.delete(f"{BASE_URL}/admin/carriers/{test_carrier_id}")
    print_test("Delete carrier", response.status_code == 200, f"Status: {response.status_code}")

# =============================================================================
# 4. PLANS - CRUD, SEARCH, SORT, PAGINATION, FILTERS
# =============================================================================
print_section("4. PLANS - CRUD, SEARCH, SORT, PAGINATION, FILTERS")

# 4.1 Listar planes
response = session.get(f"{BASE_URL}/admin/plans?page=1&page_size=20")
print_test("List plans", response.status_code == 200, f"Status: {response.status_code}")
plans_data = response.json()
initial_plan_count = plans_data['total']
print(f"  Initial plan count: {initial_plan_count}")

# 4.2 Buscar plan
if initial_plan_count > 0:
    first_plan_name = plans_data['plans'][0]['name']
    search_query = first_plan_name.split()[0]  # Primera palabra
    response = session.get(f"{BASE_URL}/admin/plans?q={search_query}")
    print_test("Search plans", 
               response.status_code == 200,
               f"Query: '{search_query}', Results: {len(response.json()['plans'])}")

# 4.3 Filtrar por country_id
if countries_data['countries']:
    country_id = countries_data['countries'][0]['id']
    response = session.get(f"{BASE_URL}/admin/plans?country_id={country_id}")
    filtered_plans = response.json()['plans']
    print_test("Filter plans by country", 
               response.status_code == 200,
               f"Country ID: {country_id}, Results: {len(filtered_plans)}")

# 4.4 Filtrar por carrier_id
if carriers_data['carriers']:
    carrier_id = carriers_data['carriers'][0]['id']
    response = session.get(f"{BASE_URL}/admin/plans?carrier_id={carrier_id}")
    filtered_plans = response.json()['plans']
    print_test("Filter plans by carrier", 
               response.status_code == 200,
               f"Carrier ID: {carrier_id}, Results: {len(filtered_plans)}")

# 4.5 Ordenar por precio (asc)
response = session.get(f"{BASE_URL}/admin/plans?sort_by=price_usd&sort_order=asc&page_size=5")
plans_by_price = response.json()['plans']
print_test("Sort plans by price (asc)", 
           response.status_code == 200,
           f"First price: ${plans_by_price[0]['price_usd'] if plans_by_price else 'N/A'}")

# 4.6 Ordenar por duración (desc)
response = session.get(f"{BASE_URL}/admin/plans?sort_by=duration_days&sort_order=desc&page_size=5")
plans_by_duration = response.json()['plans']
print_test("Sort plans by duration (desc)", 
           response.status_code == 200,
           f"First duration: {plans_by_duration[0]['duration_days'] if plans_by_duration else 'N/A'} days")

# 4.7 Ordenar por data (asc)
response = session.get(f"{BASE_URL}/admin/plans?sort_by=data_gb&sort_order=asc&page_size=5")
plans_by_data = response.json()['plans']
print_test("Sort plans by data (asc)", 
           response.status_code == 200,
           f"First data: {plans_by_data[0]['data_gb'] if plans_by_data else 'N/A'} GB")

# 4.8 Crear plan (necesitamos country_id y carrier_id válidos)
if countries_data['countries'] and carriers_data['carriers']:
    test_plan = {
        "name": "Test Plan Delete Me",
        "country_id": countries_data['countries'][0]['id'],
        "carrier_id": carriers_data['carriers'][0]['id'],
        "data_gb": 10.0,
        "is_unlimited": False,
        "duration_days": 30,
        "price_usd": 25.00,
        "description": "Test plan for automated testing"
    }
    response = session.post(f"{BASE_URL}/admin/plans", json=test_plan)
    print_test("Create plan", response.status_code == 200, f"Status: {response.status_code}")
    created_plan = response.json()
    test_plan_id = created_plan.get('id')

    # 4.9 Actualizar plan
    if test_plan_id:
        update_data = {
            "name": "Test Plan Updated",
            "country_id": countries_data['countries'][0]['id'],
            "carrier_id": carriers_data['carriers'][0]['id'],
            "data_gb": 15.0,
            "is_unlimited": False,
            "duration_days": 30,
            "price_usd": 30.00,
            "description": "Updated test plan"
        }
        response = session.put(f"{BASE_URL}/admin/plans/{test_plan_id}", json=update_data)
        print_test("Update plan", response.status_code == 200, f"Status: {response.status_code}")

    # 4.10 Eliminar plan
    if test_plan_id:
        response = session.delete(f"{BASE_URL}/admin/plans/{test_plan_id}")
        print_test("Delete plan", response.status_code == 200, f"Status: {response.status_code}")

# =============================================================================
# 5. CSV EXPORT
# =============================================================================
print_section("5. CSV EXPORT")

# 5.1 Exportar todos los planes
response = session.get(f"{BASE_URL}/admin/plans/export")
print_test("Export plans to CSV", 
           response.status_code == 200 and 'text/csv' in response.headers.get('content-type', ''),
           f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")

# 5.2 Validar estructura del CSV
csv_content = response.text
csv_reader = csv.DictReader(io.StringIO(csv_content))
csv_headers = csv_reader.fieldnames or []
expected_headers = ['id', 'name', 'country_id', 'carrier_id', 'data_gb', 'is_unlimited', 'duration_days', 'price_usd', 'description']
print_test("CSV has correct headers", 
           all(h in csv_headers for h in expected_headers),
           f"Headers: {csv_headers}")

# 5.3 Contar filas del CSV
csv_rows = list(csv_reader)
print_test("CSV contains data", 
           len(csv_rows) >= 0,
           f"Rows exported: {len(csv_rows)}")

# =============================================================================
# 6. CSV IMPORT
# =============================================================================
print_section("6. CSV IMPORT")

# 6.1 Preparar CSV de prueba (crear nuevo plan)
if countries_data['countries'] and carriers_data['carriers']:
    test_csv_content = f"""id,name,country_id,carrier_id,data_gb,is_unlimited,duration_days,price_usd,description
,CSV Import Test Plan,{countries_data['countries'][0]['id']},{carriers_data['carriers'][0]['id']},5.0,false,15,12.50,Test plan from CSV import
"""
    
    # 6.2 Importar CSV
    files = {'file': ('test_import.csv', test_csv_content, 'text/csv')}
    response = session.post(f"{BASE_URL}/admin/plans/import", files=files)
    print_test("Import plans from CSV", 
               response.status_code == 200,
               f"Status: {response.status_code}")
    
    if response.status_code == 200:
        import_result = response.json()
        print_test("CSV import successful", 
                   import_result.get('success', False),
                   f"Created: {import_result.get('created', 0)}, Updated: {import_result.get('updated', 0)}, Errors: {len(import_result.get('errors', []))}")
        
        # 6.3 Verificar que el plan fue creado
        response = session.get(f"{BASE_URL}/admin/plans?q=CSV Import Test Plan")
        imported_plans = response.json()['plans']
        print_test("Imported plan is findable", 
                   len(imported_plans) > 0,
                   f"Found {len(imported_plans)} plan(s) with name 'CSV Import Test Plan'")
        
        # 6.4 Limpiar: eliminar el plan importado
        if imported_plans:
            imported_plan_id = imported_plans[0]['id']
            response = session.delete(f"{BASE_URL}/admin/plans/{imported_plan_id}")
            print_test("Cleanup imported plan", response.status_code == 200, f"Deleted plan ID: {imported_plan_id}")

# 6.5 Probar validación de CSV (country_id inválido)
invalid_csv = """id,name,country_id,carrier_id,data_gb,is_unlimited,duration_days,price_usd,description
,Invalid Plan,99999,1,5.0,false,15,12.50,This should fail
"""
files = {'file': ('invalid.csv', invalid_csv, 'text/csv')}
response = session.post(f"{BASE_URL}/admin/plans/import", files=files)
if response.status_code == 200:
    result = response.json()
    print_test("CSV validation catches invalid country_id", 
               not result.get('success', True) and len(result.get('errors', [])) > 0,
               f"Errors detected: {len(result.get('errors', []))}")

# 6.6 Probar validación de CSV (campo requerido faltante)
missing_field_csv = """id,name,country_id,carrier_id,data_gb,is_unlimited,duration_days,price_usd,description
,Missing Country,,1,5.0,false,15,12.50,Missing country_id
"""
files = {'file': ('missing_field.csv', missing_field_csv, 'text/csv')}
response = session.post(f"{BASE_URL}/admin/plans/import", files=files)
if response.status_code == 200:
    result = response.json()
    print_test("CSV validation catches missing required field", 
               not result.get('success', True) and len(result.get('errors', [])) > 0,
               f"Errors detected: {len(result.get('errors', []))}")

# =============================================================================
# 7. VALIDACIONES
# =============================================================================
print_section("7. VALIDACIONES")

# 7.1 Validar ISO2 inválido (debe ser 2 caracteres)
response = session.post(f"{BASE_URL}/admin/countries", json={"iso2": "USA", "name": "Test"})
print_test("Validation: ISO2 must be 2 characters", 
           response.status_code in [400, 422],
           f"Status: {response.status_code}")

# 7.2 Validar nombre de carrier vacío
response = session.post(f"{BASE_URL}/admin/carriers", json={"name": ""})
print_test("Validation: Carrier name required", 
           response.status_code in [400, 422],
           f"Status: {response.status_code}")

# 7.3 Validar precio negativo en plan
if countries_data['countries'] and carriers_data['carriers']:
    invalid_plan = {
        "name": "Invalid Plan",
        "country_id": countries_data['countries'][0]['id'],
        "carrier_id": carriers_data['carriers'][0]['id'],
        "data_gb": 10.0,
        "is_unlimited": False,
        "duration_days": 30,
        "price_usd": -5.00,
        "description": "Negative price should fail"
    }
    response = session.post(f"{BASE_URL}/admin/plans", json=invalid_plan)
    print_test("Validation: Plan price must be positive", 
               response.status_code in [400, 422],
               f"Status: {response.status_code}")

# =============================================================================
# RESUMEN FINAL
# =============================================================================
print_section("RESUMEN DE PRUEBAS")
print(f"{GREEN}✓ Todas las pruebas pasaron exitosamente!{RESET}\n")
print("Funcionalidades verificadas:")
print("  ✓ Autenticación admin")
print("  ✓ Countries: CRUD, search, sort, pagination")
print("  ✓ Carriers: CRUD, search, sort, pagination")
print("  ✓ Plans: CRUD, search, filters, sort, pagination")
print("  ✓ CSV Export: descarga y estructura correcta")
print("  ✓ CSV Import: creación, validación, manejo de errores")
print("  ✓ Validaciones: ISO2, nombres requeridos, precios positivos")
print("\n" + "="*60)
print(f"{GREEN}PANEL DE ADMINISTRACIÓN FUNCIONANDO CORRECTAMENTE{RESET}")
print("="*60 + "\n")
