from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Make a user a moderator'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to make moderator')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        try:
            user = User.objects.get(username=username)
            user.profile.is_moderator = True
            user.profile.save()
            
            mod_group, _ = Group.objects.get_or_create(name='Moderators')
            user.groups.add(mod_group)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully made {username} a moderator')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )
