from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.database import get_db, User, RefreshToken, create_tables
from app.schemas import UserRegister, UserLogin, Token, UserRegisterResponse, TokenRefresh, AccessTokenResponse
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token, get_refresh_token_expiry
from datetime import timedelta, datetime, timezone

router = APIRouter()

@router.post("/register", response_model=UserRegisterResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        # Verificar si el email ya existe
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Hashear la contraseña
        hashed_password = hash_password(user_data.password)
        
        # Crear el nuevo usuario
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password
        )
        
        # Guardar en la base de datos
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Crear el token de acceso para el nuevo usuario
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )
        
        # Crear el refresh token
        refresh_token = create_refresh_token()
        refresh_token_expires = get_refresh_token_expiry()
        
        # Guardar el refresh token en la base de datos
        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=new_user.id,
            expires_at=refresh_token_expires
        )
        db.add(db_refresh_token)
        db.commit()
        
        # Devolver el usuario con ambos tokens        
        return {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "created_at": new_user.created_at,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except OperationalError as e:
        db.rollback()
        if "is full" in str(e):
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="La base de datos está llena. No se pueden registrar más usuarios."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos: " + str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor: " + str(e)
        )

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica un usuario y devuelve un token JWT
    """
    try:
        # Buscar el usuario por email
        user = db.query(User).filter(User.email == user_credentials.email).first()
        
        if not user or not verify_password(user_credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear el token de acceso
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # Crear el refresh token
        refresh_token = create_refresh_token()
        refresh_token_expires = get_refresh_token_expiry()
        
        # Invalidar tokens de refresh anteriores del usuario
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.is_active == "true"
        ).update({"is_active": "false"})
        
        # Guardar el nuevo refresh token en la base de datos
        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=refresh_token_expires
        )
        db.add(db_refresh_token)
        db.commit()
        
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "name": user.name,
            "token_type": "bearer"
        }
        
    except HTTPException:
        # Re-lanzar HTTPExceptions sin modificar
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Renueva un access token usando un refresh token válido
    """
    try:
        # Buscar el refresh token en la base de datos
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token == token_data.refresh_token,
            RefreshToken.is_active == "true"
        ).first()
        
        if not refresh_token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado"
            )
        
        # Verificar si el token ha expirado
        if refresh_token_record.expires_at < datetime.now(timezone.utc):
            # Marcar el token como inactivo
            refresh_token_record.is_active = "false"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado"
            )
        
        # Obtener el usuario asociado
        user = db.query(User).filter(User.id == refresh_token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        # Crear un nuevo access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/logout")
async def logout_user(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Cierra sesión invalidando el refresh token
    """
    try:
        # Buscar y desactivar el refresh token
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token == token_data.refresh_token,
            RefreshToken.is_active == "true"
        ).first()
        
        if refresh_token_record:
            refresh_token_record.is_active = "false"
            db.commit()
        
        return {"message": "Logout exitoso"}
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/logout-all")
async def logout_all_devices(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Cierra sesión en todos los dispositivos invalidando todos los refresh tokens del usuario
    """
    try:
        # Buscar el refresh token para obtener el usuario
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token == token_data.refresh_token,
            RefreshToken.is_active == "true"
        ).first()
        
        if not refresh_token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )
        
        # Invalidar todos los refresh tokens del usuario
        db.query(RefreshToken).filter(
            RefreshToken.user_id == refresh_token_record.user_id,
            RefreshToken.is_active == "true"
        ).update({"is_active": "false"})
        
        db.commit()
        
        return {"message": "Logout exitoso en todos los dispositivos"}
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@router.post("/create-tables")
async def create_database_tables():
    """
    Crea las tablas necesarias en la base de datos (solo para desarrollo)
    """
    try:
        create_tables()
        return {"message": "Tablas creadas exitosamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear las tablas: {str(e)}"
        )


