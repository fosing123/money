from django.contrib.auth import get_user_model
from django.test import TestCase

from goals.models import Goal

User = get_user_model()


class GoalTests(TestCase):
    def test_goal_progress_percentage(self):
        user = User.objects.create_user(username='goalie', email='goalie@example.com', password='StrongPass123!')
        goal = Goal.objects.create(owner=user, name='School fees', target_amount='50000', current_amount='20000')
        self.assertEqual(goal.progress_percentage, 40)
