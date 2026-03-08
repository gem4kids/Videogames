import unittest
import sys
import os

# Añadimos el directorio src al path para poder importar main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import saludar_usuario, sumar_numeros, restar_numeros


class TestSaludarUsuario(unittest.TestCase):

    def test_saludo_con_nombre(self):
        # Comprueba que el saludo incluye el nombre del usuario
        resultado = saludar_usuario("Ana")
        self.assertIn("Ana", resultado)

    def test_saludo_contiene_bienvenida(self):
        # Comprueba que el mensaje contiene la palabra "Bienvenido"
        resultado = saludar_usuario("Carlos")
        self.assertIn("Bienvenido", resultado)

    def test_saludo_devuelve_cadena(self):
        # Comprueba que el valor devuelto es una cadena de texto
        resultado = saludar_usuario("Luis")
        self.assertIsInstance(resultado, str)


class TestSumarNumeros(unittest.TestCase):

    def test_suma_positivos(self):
        # Comprueba la suma de dos números positivos
        self.assertEqual(sumar_numeros(5, 7), 12)

    def test_suma_con_cero(self):
        # Sumar cualquier número con cero debe devolver el mismo número
        self.assertEqual(sumar_numeros(0, 9), 9)

    def test_suma_negativos(self):
        # Comprueba la suma de dos números negativos
        self.assertEqual(sumar_numeros(-3, -4), -7)

    def test_suma_positivo_y_negativo(self):
        # Comprueba la suma de un positivo y un negativo
        self.assertEqual(sumar_numeros(10, -4), 6)


class TestRestarNumeros(unittest.TestCase):

    def test_resta_positivos(self):
        # Comprueba la resta básica de dos positivos
        self.assertEqual(restar_numeros(10, 3), 7)

    def test_resta_con_cero(self):
        # Restar cero no debe cambiar el valor
        self.assertEqual(restar_numeros(5, 0), 5)

    def test_resta_resultado_negativo(self):
        # Si el sustraendo es mayor, el resultado debe ser negativo
        self.assertEqual(restar_numeros(2, 8), -6)

    def test_resta_numeros_iguales(self):
        # Restar un número a sí mismo debe dar cero
        self.assertEqual(restar_numeros(7, 7), 0)


if __name__ == "__main__":
    unittest.main()
