"""Test _extract_processor fixes (pytest parametrized)."""
import sys
sys.path.insert(0, '.')
import pytest
from src.parser import _extract_processor

CASES = [
    ("Ultra 5 from desc",
     "All in One HP HP ProOne 240 G10, 23.8 pulgadas, Intel Core Ultra 5, 8 GB, 512 GB SSD, Windows 11 Home",
     "Intel Core Ultra 5"),
    ("Ultra 5 + 125U comma",
     "Procesador Core Ultra 5, 125U (0.70 GHz, up to 4.30 GHz, 12 cores)",
     "Core Ultra 5 125U"),
    ("Ultra 7 from full desc",
     "Procesador Core Ultra 7 155H, 16GB RAM, 1TB SSD",
     "Core Ultra 7 155H"),
    ("Ultra 9 with model",
     "Intel Core Ultra 9 185H, 32GB RAM",
     "Core Ultra 9 185H"),
    ("i5-1235U",
     "Laptop HP 15, Intel Core i5-1235U, 8GB RAM, 256GB SSD",
     "i5-1235U"),
    ("i7-1360P",
     "Lenovo ThinkPad Intel Core i7-1360P, 16GB",
     "i7-1360P"),
    ("i3-N305",
     "Mini PC Intel Core i3-N305, 8GB DDR4",
     "i3-N305"),
    ("Ryzen 5 7520U",
     "AMD Ryzen 5 7520U, 8GB RAM, 512GB SSD",
     "Ryzen 5 7520U"),
    ("Ryzen 7 5825U",
     "AMD Ryzen 7 5825U, de ocho nucleos",
     "Ryzen 7 5825U"),
    ("Ryzen 9 HX",
     "ROG Zephyrus AMD Ryzen 9 7945HX, 16GB",
     "Ryzen 9 7945HX"),
    ("Ryzen AI 9",
     "ASUS Vivobook AMD Ryzen AI 9 365, 16GB RAM",
     "Ryzen AI 9 365"),
    ("N100", "Mini PC Intel N100, 8GB RAM, 256GB SSD", "N100"),
    ("N305", "Intel N305, 8GB DDR5", "N305"),
    ("Celeron N4500", "Intel Celeron N4500, 4GB RAM", "Celeron N4500"),
    ("Pentium Silver", "Intel Pentium Silver N6000, 8GB", "Pentium"),
    ("No CPU - empty", "", ""),
    ("No CPU - generic", "Computadora de escritorio, 8GB RAM, 256GB SSD, Windows 11", ""),
    ("No CPU - only specs", "8GB RAM, 512GB SSD, Windows 11 Home", ""),
    ("RAM mention before CPU",
     "Memoria RAM 16GB DDR5, Procesador Intel Core i7-13700H",
     "i7-13700H"),
    ("Storage GB before CPU",
     "512GB SSD, Intel Core Ultra 5 125U, 8GB",
     "Core Ultra 5 125U"),
    ("With TM symbol",
     "Intel Core\u2122 i5-1235U, 8GB",
     "i5-1235U"),
]


@pytest.mark.parametrize("name,desc,expected", CASES)
def test_extract_processor(name, desc, expected):
    result = _extract_processor(desc)
    assert expected in result, f"[{name}] expected '{expected}' in result, got '{result}'"
