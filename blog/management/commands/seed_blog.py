from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from blog.models import Category, Post, PostStatus

TOPICS = [
    ('Knee Rehabilitation Exercises After Surgery', 'Rehabilitation'),
    ('How Long Does Frozen Shoulder Really Take to Heal?', 'Rehabilitation'),
    ('Five Desk Stretches That Prevent Lower Back Pain', 'Prevention'),
    ('What Actually Happens in Your First Physio Session', 'Getting Started'),
    ('Strength vs. Mobility: What to Train First', 'Exercise Science'),
    ('Why Rest Alone Rarely Fixes Tendon Pain', 'Exercise Science'),
]


class Command(BaseCommand):
    help = 'Seed the database with demo blog content.'

    def handle(self, *args, **options):
        author, _ = User.objects.get_or_create(
            username='demo_author',
            defaults={'first_name': 'Demo', 'last_name': 'Author'},
        )

        created = 0
        for index, (title, category_name) in enumerate(TOPICS):
            category, _ = Category.objects.get_or_create(name=category_name)
            _, was_created = Post.objects.get_or_create(
                slug=slugify(title),
                defaults={
                    'title': title,
                    'excerpt': f'A practical guide to {title.lower()}.',
                    'content': 'Recovery is a process, not an event.\n\n' * 10,
                    'meta_description': f'Everything you need to know about {title.lower()}.',
                    'focus_keyword': title.lower(),
                    'author': author,
                    'category': category,
                    'status': PostStatus.PUBLISHED if index % 4 else PostStatus.DRAFT,
                    'published_at': timezone.now() if index % 4 else None,
                },
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} new post(s).'))
