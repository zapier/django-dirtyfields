**Take a look at https://github.com/zapier/django-stalefields for a newer, better supported version!**


===================
Django Dirty Fields
===================

Tracking changed fields on a Django model instance.

Makes a Mixin available that will give you the properties:

* ``is_dirty``
* ``dirty_fields``

As well as the methods:

* ``save_dirty()``

Which will will selectively only update dirty columns using the familiar ``Model.objects.filter(pk=pk).update(**dirty_fields)`` pattern (but still resolves ``F()`` or ``auto_now`` constructs).


Why This Branch?
================

It's always annoying to browse various active branches with no context about how they differ outside of diffs. So, we'll just tell you! :-)

We're building off the dirtyfields_ branch by Calloway Project that added some ``update()`` features around dirty fields. However, we fixed two bugs:

* Pre/Post save events have proper kwargs passed in.
* ``foreign_key_id`` attributes that accompany ``foreign_key`` model fields are properly handled.

Thats it really! We've also added a few tests around ``save_dirty()``. Enjoy!

.. _dirtyfields: https://github.com/callowayproject/django-dirtyfields


Installing
==========

Install the package using pip_. Then use the instructions in "Using the Mixin in the Model".

::

    $ pip install django-dirtyfields

or if you're interested in developing it, use virtualenv_ and virtualenvwrapper_. The default ``settings.py`` will look for the dirtyfields package in its current location.

::

    $ mkvirtualenv django-dirtyfields
    (django-dirtyfields)$ pip install -r example_app/requirements.pip
    (django-dirtyfields)$ example_app/manage.py test testing_app


.. _pip: http://www.pip-installer.org/en/latest/
.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _virtualenvwrapper: https://pypi.python.org/pypi/virtualenvwrapper



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

