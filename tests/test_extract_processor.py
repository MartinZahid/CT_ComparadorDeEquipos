"""Test _extract_processor fixes."""
import sys
sys.path.insert(0, '.')
from src.parser import _extract_processor

pass_count = 0
fail_count = 0

def test(name, desc, expected):
    global pass_count, fail_count
    result = _extract_processor(desc)
    if expected in result:
        pass_count += 1
        print(f"  PASS [{name}]: got '{result}'")
    else:
        fail_count += 1
        print(f"  FAIL [{name}]: expected '{expected}' in result, got '{result}'")

# Intel Core Ultra series
test("Ultra 5 from desc",
     "All in One HP HP ProOne 240 G10, 23.8 pulgadas, Intel Core Ultra 5, 8 GB, 512 GB SSD, Windows 11 Home",
     "Intel Core Ultra 5")

test("Ultra 5 + 125U comma",
     "Procesador Core Ultra 5, 125U (0.70 GHz, up to 4.30 GHz, 12 cores)",
     "Core Ultra 5 125U")

test("Ultra 7 from full desc",
     "Procesador Core Ultra 7 155H, 16GB RAM, 1TB SSD",
     "Core Ultra 7 155H")

test("Ultra 9 with model",
     "Intel Core Ultra 9 185H, 32GB RAM",
     "Core Ultra 9 185H")

# Intel Core i-series
test("i5-1235U",
     "Laptop HP 15, Intel Core i5-1235U, 8GB RAM, 256GB SSD",
     "i5-1235U")

test("i7-1360P",
     "Lenovo ThinkPad Intel Core i7-1360P, 16GB",
     "i7-1360P")

test("i3-N305",
     "Mini PC Intel Core i3-N305, 8GB DDR4",
     "i3-N305")

# AMD Ryzen
test("Ryzen 5 7520U",
     "AMD Ryzen 5 7520U, 8GB RAM, 512GB SSD",
     "Ryzen 5 7520U")

test("Ryzen 7 5825U",
     "AMD Ryzen 7 5825U, de ocho nucleos",
     "Ryzen 7 5825U")

test("Ryzen 9 HX",
     "ROG Zephyrus AMD Ryzen 9 7945HX, 16GB",
     "Ryzen 9 7945HX")

test("Ryzen AI 9",
     "ASUS Vivobook AMD Ryzen AI 9 365, 16GB RAM",
     "Ryzen AI 9 365")

# Celeron / Pentium / N-series
test("N100", "Mini PC Intel N100, 8GB RAM, 256GB SSD", "N100")
test("N305", "Intel N305, 8GB DDR5", "N305")
test("Celeron N4500", "Intel Celeron N4500, 4GB RAM", "Celeron N4500")
test("Pentium Silver", "Intel Pentium Silver N6000, 8GB", "Pentium")

# No processor
test("No CPU - empty", "", "")
test("No CPU - generic", "Computadora de escritorio, 8GB RAM, 256GB SSD, Windows 11", "")
test("No CPU - only specs", "8GB RAM, 512GB SSD, Windows 11 Home", "")

# Mixed/edge cases
test("RAM mention before CPU",
     "Memoria RAM 16GB DDR5, Procesador Intel Core i7-13700H",
     "i7-13700H")

test("Storage GB before CPU",
     "512GB SSD, Intel Core Ultra 5 125U, 8GB",
     "Core Ultra 5 125U")

test("With TM symbol",
     "Intel Core\u2122 i5-1235U, 8GB",
     "i5-1235U")

print(f"\nResultados: {pass_count} passed, {fail_count} failed")
