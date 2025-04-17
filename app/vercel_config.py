"""
Configuración específica para entorno Vercel
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

# Configurar logger específico para config de Vercel
logger = logging.getLogger("vercel_config")

class VercelConfig:
    """Clase para gestionar la configuración en entorno Vercel"""
    
    def __init__(self):
        self.is_vercel = self._detect_vercel()
        self.debug = self._get_bool_env("DEBUG", True)
        self.use_database = self._get_bool_env("USE_DATABASE", True)
        self.use_gemini = self._get_bool_env("USE_GEMINI", True)
        self.sqlite_fallback = self._get_bool_env("SQLITE_FALLBACK", True)
        
        # Registrar la configuración detectada
        if self.is_vercel:
            logger.info("✅ Entorno Vercel detectado")
        else:
            logger.info("⚠️ No se detectó entorno Vercel - asumiendo entorno de desarrollo")
            
        logger.info(f"Configuración: DEBUG={self.debug}, USE_DATABASE={self.use_database}, "
                    f"USE_GEMINI={self.use_gemini}, SQLITE_FALLBACK={self.sqlite_fallback}")
    
    def _detect_vercel(self) -> bool:
        """Detecta si estamos ejecutando en Vercel"""
        return bool(os.environ.get("VERCEL") or 
                   os.environ.get("VERCEL_ENV") or 
                   os.environ.get("VERCEL_REGION"))
    
    def _get_bool_env(self, name: str, default: bool) -> bool:
        """Obtiene un valor booleano de variables de entorno"""
        value = os.environ.get(name, str(default)).lower()
        return value in ("1", "true", "yes", "y", "t")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de la base de datos"""
        if not self.use_database:
            return {"enabled": False}
            
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url and self.sqlite_fallback:
            logger.warning("⚠️ No se encontró DATABASE_URL - usando SQLite como fallback")
            return {
                "enabled": True,
                "type": "sqlite",
                "url": "sqlite:///app/db/gymAI.db",
                "is_fallback": True
            }
        elif database_url:
            # Enmascarar URL para logs (seguridad)
            masked_url = database_url.split("@")[0].split(":")
            if len(masked_url) > 2:
                masked_url[2] = "********"  # Ocultar contraseña
                masked_url = ":".join(masked_url) + "@" + database_url.split("@")[1]
                logger.info(f"✅ Usando PostgreSQL: {masked_url}")
            
            return {
                "enabled": True,
                "type": "postgres",
                "url": database_url,
                "is_fallback": False
            }
        else:
            logger.error("❌ No se encontró configuración de base de datos válida")
            return {"enabled": False}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Obtiene el estado de los servicios para diagnóstico"""
        db_config = self.get_database_config()
        
        return {
            "environment": "vercel" if self.is_vercel else "development",
            "debug_mode": self.debug,
            "database": {
                "enabled": db_config["enabled"],
                "type": db_config.get("type", "none"),
                "is_fallback": db_config.get("is_fallback", False)
            },
            "gemini_api": {
                "enabled": self.use_gemini and bool(os.environ.get("GEMINI_API_KEY")),
                "key_configured": bool(os.environ.get("GEMINI_API_KEY"))
            },
            "static_files": self._check_static_files(),
            "python_version": os.environ.get("PYTHON_VERSION", "unknown")
        }
    
    def _check_static_files(self) -> Dict[str, Any]:
        """Verifica la disponibilidad de archivos estáticos"""
        static_dirs = [
            "/tmp/staticfiles",
            "staticfiles",
            "static"
        ]
        
        for static_dir in static_dirs:
            if os.path.exists(static_dir):
                try:
                    files = os.listdir(static_dir)
                    return {
                        "available": True,
                        "path": static_dir,
                        "files_count": len(files),
                        "sample_files": files[:5] if files else []
                    }
                except Exception:
                    pass
        
        return {"available": False}

# Crear instancia global
config = VercelConfig()
