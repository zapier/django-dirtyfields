===================
Django Dirty Fields
===================

Tracking changed fields on a Django model instance.

Makes a Mixin available that will give you the properties:

 * ``is_dirty``
 * ``dirty_fields``


Installing
==========

Install the package using pip_. Then use the instructions in "Using the Mixin in the Model".

::

    $ pip install django-dirtyfields

or if you're interested in developing it, use virtualenv_. The default ``settings.py`` will look for the dirtyfields package in its current location.

::

    $ virtualenv --no-site-packages ve/
    $ source ve/bin/activate
    (ve)$ cd example_app
    (ve)$ pip install -r requirements.pip
    (ve)$ ./manage.py test testing_app


.. _pip: http://www.pip-installer.org/en/latest/
.. _virtualenv: https://pypi.python.org/pypi/virtualenv



Using the Mixin in the Model
============================

::

    from django.db import models
    from dirtyfields import DirtyFieldsMixin

    class TestModel(DirtyFieldsMixin, models.Model):
        """A simple test model to test dirty fields mixin with"""
        boolean = models.BooleanField(default=True)
        characters = models.CharField(blank=True, max_length=80)


Using it in the shell
=====================

::

    (ve)$ ./manage.py shell
    >>> from testing_app.models import TestModel
    >>> tm = TestModel(boolean=True, characters="testing")
    >>> tm.save()
    >>> tm.is_dirty
    False
    >>> tm.dirty_fields
    ()
    >>> tm.boolean = False
    >>> tm.is_dirty
    True
    >>> tm.dirty_fields
    ('boolean', )
    >>> tm.characters = "have changed"
    >>> tm.is_dirty
    True
    >>> tm.dirty_fields
    ('boolean', 'characters', )
    >>> tm.save()
    >>> tm.is_dirty
    False
    >>> tm.get_dirty_fields
    ()

Why would you want this?
========================

When using signals_, especially pre_save_, it is useful to be able to see what fields have changed or not. A signal could change its behaviour depending on whether a specific field has changed, whereas otherwise, you only could work on the event that the model's `save()` method had been called.

Credits
=======

This code has largely be adapted from what was made available at `Stack Overflow`_.

.. _Stack Overflow: http://stackoverflow.com/questions/110803/dirty-fields-in-django
.. _signals: http://docs.djangoproject.com/en/1.2/topics/signals/
.. _pre_save: http://docs.djangoproject.com/en/1.2/ref/signals/#django.db.models.signals.pre_save

