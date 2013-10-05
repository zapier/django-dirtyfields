from django.db import models
from dirtyfields import DirtyFieldsMixin


class ForeignTestModel(DirtyFieldsMixin, models.Model):
    """
    A simple test model with which to test foreign keys and dirty fields mixin
    """
    boolean = models.BooleanField(default=True)
    characters = models.CharField(blank=True, max_length=80)

    def __unicode__(self):
        return u'{} {}'.format(self.boolean, self.characters)

class TestModel(DirtyFieldsMixin, models.Model):
    """
    A simple test model with which to test dirty fields mixin
    """
    boolean = models.BooleanField(default=True)
    characters = models.CharField(blank=True, max_length=80)
    foreign_test_model = models.ForeignKey(ForeignTestModel, blank=True, null=True)

    def __unicode__(self):
        return u'{} {} {}'.format(self.boolean, self.characters, self.foreign_test_model)
