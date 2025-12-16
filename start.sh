#!/bin/bash

# Iniciar aplicación (la DB se inicializa automáticamente)
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}