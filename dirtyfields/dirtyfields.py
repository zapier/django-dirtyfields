# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django import VERSION
from django.db.models.signals import post_save, pre_save


def reset_instance(instance, *args, **kwargs):
    """
    Called on the post_save signal. Calls the instance's _reset_state method
    """
    instance._reset_state()


class DirtyFieldsMixin(object):
    """
    Gives dirty field tracking ability to models, also implements a save_dirty
    method which updates only the dirty fields using QuerySet.update - useful
    for multi-process or multi-worker setups where save() will actually update
    all fields, potentially overriding changes by other workers while the
    current worker has the object open.
    """
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        dispatch_uid = '%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__
        post_save.connect(reset_instance, sender=self.__class__,
                          dispatch_uid=dispatch_uid)
        self._reset_state()

    def _reset_state(self, *args, **kwargs):
        self._original_state = self._as_dict()

    def _as_dict(self):
        # For relations, saves all fk values too so that we can update fk by
        # id, e.g. obj.foreignkey_id = 4
        if self._deferred:
            return {}
        return dict([(f.name, f.to_python(getattr(self, f.attname))) for f in self._meta.local_fields])

    def get_changed_values(self):
        return dict([(field, getattr(self, field)) for field in self.dirty_fields])

    @property
    def dirty_fields(self):
        """
        Returns a list of keys that have changed
        """
        if self._deferred:
            raise TypeError('Cant be used with deferred objects')
        new_state = self._as_dict()
        return tuple(k for k, v in self._original_state.iteritems() if v != new_state[k])

    @property
    def is_dirty(self):
        if self._state.adding:
            return True
        return bool(self.dirty_fields)

    def save_dirty(self):
        """
        An alternative to save, instead writing every field again, only updates
        the dirty fields via QuerySet.update
        """
        if not self.pk:
            self.save()
            updated = 1
        else:
            changed_values = self.get_changed_values()
            if len(changed_values.keys()) == 0:
                return False

            pre_save.send(sender=self.__class__, instance=self)

            # Detect if updating relationship field_ids directly
            # If related field object itself has changed then the field_id
            # also changes, in which case we detect and ignore the field_id
            # change, otherwise we'll reload the object again later unnecessarily
            rel_fields = dict([(f.column, f) for f in self._meta.fields if f.rel])
            updated_rel_ids = []
            for field_name in changed_values.keys():
                if field_name in rel_fields.keys():
                    rel_field = rel_fields[field_name]
                    value = changed_values[rel_field.column]
                    obj_value = getattr(self, rel_field.name).pk
                    del changed_values[rel_field.column]
                    changed_values[rel_field.name] = value
                    if value != obj_value:
                        updated_rel_ids.append(rel_field.column)

            # Maps db column names back to field names if they differ
            field_map = dict([(f.column, f.name) for f in self._meta.fields if f.db_column])
            for field_from, field_to in field_map.iteritems():
                if field_from in changed_values:
                    changed_values[field_to] = changed_values[field_from]
                    del changed_values[field_from]

            updated = self.__class__.objects.filter(pk=self.pk).update(**changed_values)

            # Reload updated relationships
            for field_name in updated_rel_ids:
                field = rel_fields[field_name]
                field_pk = getattr(self, field_name)
                rel_obj = field.related.parent_model.objects.get(pk=field_pk)
                setattr(self, field.name, rel_obj)

            self._reset_state()
            post_save.send(sender=self.__class__, instance=self, created=False)

        return updated == 1


# Django 1.5 added support for updating only specified fields, this fails in
# older versions.
if VERSION >= (1, 5):
    def save(self, *args, **kwargs):
        if not self._state.adding:
            kwargs['update_fields'] = self.dirty_fields
        return super(DirtyFieldsMixin, self).save(*args, **kwargs)
    DirtyFieldsMixin.save = save
