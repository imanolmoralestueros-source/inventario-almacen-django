from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginacionEstandar(PageNumberPagination):
    # Cantidad de elementos por pagina si el cliente no envia el query param cantidad
    page_size = 10

    # Query param para indicar cuantos elementos se quieren por pagina (ej: ?cantidad=20)
    page_size_query_param = "cantidad"

    # Limite maximo de elementos por pagina, aunque el cliente pida mas
    max_page_size = 50

    # Query param para indicar la pagina (ej: ?pagina=2)
    page_query_param = "pagina"

    invalid_page_message = "Pagina invalida"

    def get_paginated_response(self, data):
        return Response(data={
            "content": data,
            "paginacion": {
                "total": self.page.paginator.count,            # total de elementos encontrados
                "paginaActual": self.page.number,              # pagina en la que me encuentro
                "totalPaginas": self.page.paginator.num_pages, # total de paginas que puedo navegar
                "siguiente": self.get_next_link(),             # url de la pagina siguiente (si hay)
                "anterior": self.get_previous_link()           # url de la pagina anterior (si hay)
            }
        })
