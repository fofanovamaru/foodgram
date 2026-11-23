from django.http import HttpResponse


def create_shopping_cart_file(ingredients):
    lines = ['Список покупок', '']

    for item in ingredients:
        lines.append(
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) — "
            f"{item['total_amount']}"
        )

    response = HttpResponse(
        '\n'.join(lines),
        content_type='text/plain; charset=utf-8',
    )
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"'
    )
    return response