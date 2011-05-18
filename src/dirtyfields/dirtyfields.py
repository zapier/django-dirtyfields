# Adapted from http://stackoverflow.com/questions/110803/dirty-fields-in-django
from django.db.models.signals import post_save
from django.db import connection

def reset_instance(instance, *args, **kwargs):
    instance._reset_state()

class DirtyFieldsMixin(object):
    '''
    Gives dirty field tracking ability to models, also implements a save_dirty method
    which updates only the dirty fields using QuerySet.update - useful for multi-process
    or multi-worker setups where save() will actually update all fields, potentially
    overriding changes by other workers while the current worker has the object open.
    '''
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        post_save.connect(reset_instance, sender=self.__class__,
                          dispatch_uid='%s-DirtyFieldsMixin-sweeper' % self.__class__.__name__)
        self._reset_state()
    
    def _reset_state(self, *args, **kwargs):
        self._original_state = self._as_dict()
    
    def _as_dict(self):
        # For relations, saves all fk values too so that we can update fk by id, e.g. obj.foreignkey_id = 4
        if self._deferred:
            return {}
        values = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields if not f.rel])
        values.update(dict([(f.column, getattr(self, f.column)) for f in self._meta.fields if f.rel]))
        return values
    
    def get_changed_values(self):
        changed = {}
        for field in self.get_dirty_fields().keys():
            changed[field] = getattr(self, field)
        return changed
    
    def get_dirty_fields(self):
        if self._deferred:
            raise TypeError('Cant be used with deferred objects')
        new_state = self._as_dict()
        return dict([(key, value) for key, value in self._original_state.iteritems() if value != new_state[key]])
    
    def is_dirty(self):
        # in order to be dirty we need to have been saved at least once, so we
        # check for a primary key and we need our dirty fields to not be empty
        if not self.pk: 
            return True
        return {} != self.get_dirty_fields()

    def save_dirty(self):
        '''
        An alternative to save, instead writing every field again, only updates the dirty fields via QuerySet.update
        '''
        if not self.pk:
            self.save()
        else:
            changed_values = self.get_changed_values()
            if len(self.get_changed_values().keys()) == 0:
                return False
            
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
                    
            self.__class__.objects.filter(pk=self.pk).update(**changed_values)
            
            # Reload updated relationships
            for field_name in updated_rel_ids:
                field = rel_fields[field_name]
                field_pk = getattr(self, field_name)
                rel_obj = field.related.parent_model.objects.get(pk=field_pk)
                setattr(self, field.name, rel_obj)
                
            self._reset_state()
            
        return True