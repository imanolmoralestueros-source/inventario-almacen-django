from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsAdminOSoloLectura(BasePermission):
    """
    - Metodos de lectura (GET): cualquier usuario con una JWT valida.
    - Metodos de escritura (POST, PUT, PATCH, DELETE): solo usuarios con rol ADMIN.
    """
    message = "Solo un usuario ADMIN puede realizar esta accion"

    def has_permission(self, request, view):
        # Sin JWT valida no se puede ingresar a ningun endpoint del catalogo
        if not request.user or not request.user.is_authenticated:
            return False

        # SAFE_METHODS son GET, HEAD y OPTIONS
        if request.method in SAFE_METHODS:
            return True

        return request.user.rol == "ADMIN"
