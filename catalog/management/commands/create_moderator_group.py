from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from catalog.models import Post, Thread

class Command(BaseCommand):
    help = 'Create moderator group with specific permissions'

    def handle(self, *args, **kwargs):
        # Create or get the moderator group
        moderator_group, created = Group.objects.get_or_create(name='Moderators')
        
        # Get content type for Post model
        post_ct = ContentType.objects.get_for_model(Post)
        thread_ct = ContentType.objects.get_for_model(Thread)
        
        # Get or create permissions
        delete_post_perm = Permission.objects.get(
            codename='delete_post',
            content_type=post_ct
        )
        delete_thread_perm = Permission.objects.get(
            codename='delete_thread',
            content_type=thread_ct
        )
        change_post_perm = Permission.objects.get(
            codename='change_post',
            content_type=post_ct
        )
        
        # Assign permissions to moderator group
        moderator_group.permissions.add(
            delete_post_perm,
            delete_thread_perm,
            change_post_perm
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Moderator group created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('Moderator group updated successfully'))
