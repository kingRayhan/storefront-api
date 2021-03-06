"""Fresh command."""

# Python
import os

# Django
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    """Drop all tables, then remake and apply migrations."""

    help = 'Drop all tables, then remake and apply migrations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete migration files',
        )

    def handle(self, *args, **options):
        """Run SQL command and delete migrations files."""

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        -- if the schema you operate on is not "current",
                        -- you will want to replace current_schema() in
                        -- query with 'schematodeletetablesfrom'
                        -- *and* update the generate 'DROP...' accordingly.
                        FOR r IN (
                            SELECT tablename
                            FROM pg_tables
                            WHERE schemaname = current_schema()
                        ) LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' ||
                            quote_ident(r.tablename) ||
                            ' CASCADE';
                        END LOOP;
                    END $$;
                """, [])

            # Delete migration files from system storage.
            if options['delete']:
                for root, dirs, files in os.walk(settings.BASE_DIR):
                    for name in files:
                        if 'migrations' in root and name != '__init__.py':
                            os.remove(os.path.join(root, name))

            call_command('makemigrations')
            call_command('migrate')
        except Exception as e:
            raise CommandError(
                f'An error has ocurred while dropping tables. \n{e}'
            )

        self.stdout.write(self.style.SUCCESS('Database has been refreshed'))