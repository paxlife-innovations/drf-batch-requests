import json

from django.core.files import File
from django.utils import six

from rest_framework import serializers

from drf_batch_requests.settings import conf
from drf_batch_requests.utils import generate_random_id


class SingleRequestSerializer(serializers.Serializer):
    
    method = serializers.CharField()
    relative_url = serializers.CharField()
    
    headers = serializers.JSONField(required=False)
    name = serializers.CharField(required=False)
    depends_on = serializers.JSONField(required=False)
    body = serializers.JSONField(required=False, default={})
    # attached files formats: ["a.jpg", "b.png"] - will be attached as it is, {"file": "a.jpg"} - attach as specific key
    attached_files = serializers.JSONField(required=False)
    data = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    def validate_headers(self, value):
        if not isinstance(value, dict):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                raise serializers.ValidationError('Invalid format.')    
        if conf.SUBREQ_ID_REQUIRED and conf.SUBREQ_ID_HEADER not in value:
            raise serializers.ValidationError('Header "%s" is required.' % conf.SUBREQ_ID_HEADER)
        return value

    def validate_relative_url(self, value):
        if not value.startswith('/'):
            raise serializers.ValidationError('Url should start with /.')

        return value

    def validate_body(self, value):
        if isinstance(value, dict):
            return value

        try:
            json.loads(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError('Invalid format.') 

        return value

    def validate(self, attrs):
        if 'name' not in attrs:
            attrs['name'] = generate_random_id()

        if 'depends_on' in attrs:
            value = attrs['depends_on']
            if not isinstance(value, (six.string_types, list)):
                raise serializers.ValidationError({'depends_on': 'Incorrect value provided'})

            if isinstance(value, six.string_types):
                attrs['depends_on'] = [value]

        return attrs

    def get_data(self, data):
        body = data['body']
        if isinstance(body, dict):
            return body

        return json.loads(body)

    def get_files(self, attrs):
        if 'attached_files' not in attrs:
            return []

        attached_files = attrs['attached_files']
        if isinstance(attached_files, dict):
            return {
                key: self.context['parent'].get_files()[attrs['attached_files'][key]] for key in attrs['attached_files']
            }
        elif isinstance(attached_files, list):
            return {
                key: self.context['parent'].get_files()[key] for key in attrs['attached_files']
            }
        else:
            raise serializers.ValidationError('Incorrect format.')


class BatchRequestSerializer(serializers.Serializer):
    batch = serializers.JSONField()
    files = serializers.SerializerMethodField()

    def get_files(self, attrs=None):
        return {fn: f for fn, f in self.initial_data.items() if isinstance(f, File)}

    def validate_batch(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Must be an array.')

        subreq_serializers = [
            SingleRequestSerializer(
                data=subreq,
                context={'parent': self})
            for subreq in value
        ]
        errors = []
        subreq_ids = []
        subreq_names = []
        id_header = conf.SUBREQ_ID_HEADER
        for serializer in subreq_serializers:
            serializer.is_valid()
            sub_id = serializer.data.get('headers', {}).get(id_header, 'no ID given')
            sub_name = serializer.data.get('name', None)
            subreq_errors = serializer.errors.copy()
            # add subrequest IDs to error messages
            if subreq_errors:
                subreq_errors.update({id_header: sub_id})
            errors.append(subreq_errors)
            if sub_id != 'no ID given':
                subreq_ids.append(sub_id)
            if sub_name is not None:
                subreq_names.append(sub_name)
        if any(errors):
            raise serializers.ValidationError(errors)

        # check for subrequest ID duplicates
        if len(subreq_ids) > len(set(subreq_ids)):
            raise serializers.ValidationError('Subrequest IDs must be unique.')
        
        # check for subrequest name duplicates
        if len(subreq_names) > len(set(subreq_names)):
            raise serializers.ValidationError('Subrequest names must be unique.')

        return [s.data for s in subreq_serializers]

    def validate(self, attrs):
        attrs = super(BatchRequestSerializer, self).validate(attrs)

        files_in_use = []
        for batch in attrs['batch']:
            if 'attached_files' not in batch:
                continue

            attached_files = batch['attached_files']
            if isinstance(attached_files, dict):
                files_in_use.extend(attached_files.values())
            elif isinstance(attached_files, list):
                files_in_use.extend(attached_files)
            else:
                raise serializers.ValidationError({'attached_files': 'Invalid format.'})

        missing_files = set(files_in_use) - set(self.get_files().keys())
        if missing_files:
            raise serializers.ValidationError('Some of files are not provided: {}'.format(', '.join(missing_files)))

        return attrs
