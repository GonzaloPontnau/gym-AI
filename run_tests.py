#!/usr/bin/env python
"""
Script para ejecutar las pruebas del proyecto GymAI y generar informes de cobertura.
Ejecutar desde la raíz del proyecto con: python run_tests.py
"""
import os
import sys
import argparse
import subprocess

def parse_args():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Ejecutar pruebas para GymAI')
    parser.add_argument(
        '--simple', 
        action='store_true', 
        help='Ejecutar solo pruebas simples que no requieren dependencias externas'
    )
    parser.add_argument(
        '--coverage', 
        action='store_true', 
        help='Generar informe de cobertura'
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Modo verboso'
    )
    parser.add_argument(
        '--module', '-m', 
        help='Ejecutar pruebas solo de un módulo específico'
    )
    
    return parser.parse_args()

def run_tests(args):
    """Ejecutar pruebas según los argumentos proporcionados"""
    # Construir comando base
    cmd = [sys.executable, '-m', 'pytest']
    
    # Añadir verbosidad si se solicita
    if args.verbose:
        cmd.append('-v')
    
    # Configurar cobertura si se solicita
    if args.coverage:
        cmd.extend(['--cov=app', '--cov-report=term', '--cov-report=html'])
    
    # Seleccionar pruebas a ejecutar
    if args.simple:
        cmd.append('tests/test_simple.py')
        cmd.append('tests/test_models_simple.py')
    elif args.module:
        cmd.append(f'tests/test_{args.module}.py')
    
    # Ejecutar comando
    print(f"Ejecutando comando: {' '.join(cmd)}")
    return subprocess.run(cmd)

def main():
    """Función principal"""
    args = parse_args()
    
    # Asegurar que estamos en el directorio raíz del proyecto
    if not os.path.exists('app') or not os.path.exists('tests'):
        print("Error: Este script debe ejecutarse desde el directorio raíz del proyecto GymAI.")
        return 1
    
    # Ejecutar pruebas
    result = run_tests(args)
    
    # Mostrar mensaje de éxito/fracaso
    if result.returncode == 0:
        print("\n✅ ¡Todas las pruebas pasaron correctamente!")
        if args.coverage:
            print("📊 Informe de cobertura generado en htmlcov/index.html")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los resultados.")
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main()) 