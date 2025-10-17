"""
Management command to warm up caches.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.api.cache.warming import warmer

User = get_user_model()


class Command(BaseCommand):
    help = 'Warm up application caches with frequently accessed data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Warm caches for a specific user',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress output',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        verbose = not options.get('quiet')

        if user_id:
            # Warm user-specific caches
            stats = warmer.warm_user_specific(user_id, verbose=verbose)

            if 'error' in stats:
                self.stdout.write(self.style.ERROR(f'Error: {stats["error"]}'))
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f'Warmed caches for user {user_id}: {", ".join(stats["tasks"])}'
                )
            )
        else:
            # Warm all caches
            stats = warmer.warm_all(verbose=verbose)

            if stats['succeeded'] == stats['total']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Successfully warmed all {stats["succeeded"]} caches'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Warmed {stats["succeeded"]}/{stats["total"]} caches '
                        f'({stats["failed"]} failed)'
                    )
                )

                for error in stats['errors']:
                    self.stdout.write(
                        self.style.ERROR(f'  - {error["task"]}: {error["error"]}')
                    )
