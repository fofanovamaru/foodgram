import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV-файла'

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR.parent / 'data' / 'ingredients.csv'
        created = 0

        with file_path.open(encoding='utf-8', newline='') as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) != 2:
                    continue

                name, measurement_unit = (
                    value.strip() for value in row
                )

                if name and measurement_unit:
                    _, was_created = Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit,
                    )
                    if was_created:
                        created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Импорт завершён. Добавлено ингредиентов: {created}.'
            )
        )
